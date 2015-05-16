from shutit_module import ShutItModule

class docker(ShutItModule):

	def build(self, shutit):
		#shutit.install('lsb-release')
		#shutit.send('echo deb http://archive.ubuntu.com/ubuntu $(lsb_release -s -c) universe > /etc/apt/sources.list.d/universe.list')
		#shutit.send('apt-get update -qq')
		shutit.install('iptables')
		shutit.install('ca-certificates')
		shutit.install('lxc')
		shutit.install('curl')
		shutit.install('aufs-tools')
		shutit.install('psmisc') # for killall
		shutit.send('cd /usr/bin')
		# Sensible to pick a relatively old one to avoid client mismatch errors
		shutit.send('curl https://get.docker.io/builds/Linux/x86_64/docker-1.0.1 > docker')
		shutit.send('chmod +x docker')
		shutit.send_host_file('/usr/bin/wrapdocker','context/wrapdocker')
		shutit.send('chmod +x /usr/bin/wrapdocker')
		start_docker = """cat > /root/start_docker.sh << 'END'
#!/bin/bash
/usr/bin/wrapdocker &
echo "Docker daemon running"
END"""
		shutit.send(start_docker)
		shutit.send('chmod +x /root/start_docker.sh')
		shutit.send('ln -s /usr/bin/docker /usr/bin/docker.io')
		return True

	def check_ready(self, shutit):
		"""Only apt-based systems are supported support atm.
		"""
		return shutit.get_current_environment()['install_type'] == 'apt'

	def start(self, shutit):
		shutit.send('/root/start_docker.sh')
		return True

	def stop(self, shutit):
		shutit.send('/usr/bin/killall docker',check_exit=False) # could return 1 if none exist
		return True
		


def module():
	return docker(
		'shutit.tk.docker.docker', 0.396,
		description="docker server (communicates with host's docker daemon)",
		depends=['shutit.tk.setup']
	)

