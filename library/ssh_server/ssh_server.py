from shutit_module import ShutItModule

class ssh_server(ShutItModule):

	def is_installed(self, shutit):
		shutit.file_exists('/root/start_ssh_server.sh')

	def build(self, shutit):
		shutit.install('openssh-server')
		shutit.set_password(shutit.collect_config(self.module_id,'password'))
		shutit.send('mkdir -p /var/run/sshd')
		shutit.send('chmod 700 /var/run/sshd')
		# Set up root bashrcs once
		# Root bash files seem to be inconsistent, so this the canonical one...
		#shutit.add_line_to_file('export HOME=/root', '/root/.bashrc')
		# ... and the others point to it.
		#shutit.add_line_to_file('. /root/.bashrc', '/root/.bash_profile.sh')
		#shutit.add_line_to_file('. /root/.bashrc', '/.bashrc')
		#shutit.add_line_to_file('. /root/.bashrc', '/.bash_profile')
		#shutit.add_line_to_file('# sshd', '/root/start_ssh_server.sh')
		## To get sshd to work, we need to create a privilege separation directory.
		## see http://docs.docker.io/en/latest/examples/running_ssh_service/
		shutit.add_line_to_file('mkdir -p /var/run/sshd', '/root/start_ssh_server.sh')
		shutit.add_line_to_file('chmod 700 /var/run/sshd', '/root/start_ssh_server.sh')
		if shutit.collect_config('target','distro') in ('ubuntu','debian'):
			shutit.add_line_to_file('start-stop-daemon --start --quiet --oknodo --pidfile /var/run/sshd.pid --exec /usr/sbin/sshd', '/root/start_ssh_server.sh')
			shutit.add_line_to_file('start-stop-daemon --stop --quiet --oknodo --pidfile /var/run/sshd.pid', '/root/stop_ssh_server.sh')
			# 12.04 issue on selinux hosts:
			# https://groups.google.com/forum/#!topic/docker-user/73AiwlZEgY4
			#if shutit.collect_config('target','distro_version') == '12.04':
			#    shutit.send('wget http://mirrors.kernel.org/ubuntu/pool/main/libs/libselinux/libselinux1_2.1.13-2_i386.deb')
			#    shutit.send('dpkg --install libselinux1_2.1.13-2_i386.deb')
		else:
			shutit.send('sshd-keygen')
			shutit.add_line_to_file('/usr/sbin/sshd', '/root/start_ssh_server.sh')
			shutit.add_line_to_file('ps -ef | grep -w sshd | awk \'{print $2}\' | xargs kill', '/root/stop_ssh_server.sh')
		shutit.send('chmod +x /root/start_ssh_server.sh')
		shutit.send('chmod +x /root/stop_ssh_server.sh')
		return True

	def start(self, shutit):
		shutit.send('/root/start_ssh_server.sh', check_exit=False)
		return True

	def stop(self, shutit):
		shutit.send('/root/stop_ssh_server.sh', check_exit=False)
		return True

	def remove(self, shutit):
		shutit.send('rm -f /root/start_ssh_server.sh')
		return True
	
	def get_config(self, shutit):
		shutit.get_config(self.module_id, 'password', 'changeme', hint='root password for the image')
		return True


def module():
	return ssh_server(
		'shutit.tk.ssh_server.ssh_server', 0.121,
		description='ssh server',
		depends=['shutit.tk.setup']
	)

