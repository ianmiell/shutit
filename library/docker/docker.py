#Copyright (C) 2014 OpenBet Limited
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is furnished
#to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
#FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
#COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
#IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

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
		shutit.send('pushd /usr/bin')
		# Sensible to pick a relatively old one to avoid client mismatch errors
		shutit.send('curl https://get.docker.io/builds/Linux/x86_64/docker-1.0.1 > docker')
		shutit.send('chmod +x docker')
		shutit.send_host_file('/usr/bin/wrapdocker','context/wrapdocker')
		shutit.send('chmod +x /usr/bin/wrapdocker')
		start_docker = """cat > /root/start_docker.sh << 'END'
#!/bin/bash
/root/start_ssh_server.sh
/usr/bin/wrapdocker &
echo "SSH Server up"
echo "Docker daemon running"
END"""
		shutit.send(start_docker)
		shutit.send('chmod +x /root/start_docker.sh')
		shutit.send('popd')
		shutit.send('ln -s /usr/bin/docker /usr/bin/docker.io')
		return True

	def is_installed(self, shutit):
		return False

	def check_ready(self, shutit):
		"""Only apt-based systems are supported support atm.
		"""
		return shutit.cfg['target']['install_type'] == 'apt'

	def start(self, shutit):
		shutit.send('/root/start_docker.sh')
		return True

	def stop(self, shutit):
		shutit.send('killall docker')
		return True
		


def module():
	return docker(
		'shutit.tk.docker.docker', 0.396,
		description="docker server (communicates with host's docker daemon)",
		depends=['shutit.tk.setup', 'shutit.tk.ssh_server.ssh_server']
	)

