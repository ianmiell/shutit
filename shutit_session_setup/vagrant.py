import virtualization
def build(shutit, vagrant_version='1.8.6', virt_method='virtualbox'):
	if not virtualization.build(shutit, virt_method=virt_method):
		return False
	processor = shutit.send_and_get_output('uname -p')
	if not shutit.command_available('wget'):
		shutit.install('wget')
	if not shutit.command_available('vagrant'):
		if shutit.get_current_shutit_pexpect_session_environment().install_type == 'apt':
			pw = shutit.get_env_pass('Input your sudo password to install vagrant')
			shutit.send('wget -qO- https://releases.hashicorp.com/vagrant/' + vagrant_version + '/vagrant_' + vagrant_version + '_' + processor + '.deb > /tmp/vagrant.deb',note='Downloading vagrant and installing')
			shutit.multisend('sudo dpkg -i /tmp/vagrant.deb',{'assword':pw})
			shutit.send('rm -f /tmp/vagrant.deb')
		elif shutit.get_current_shutit_pexpect_session_environment().install_type == 'yum':
			pw = shutit.get_env_pass('Input your sudo password to install vagrant')
			shutit.send('wget -qO- https://releases.hashicorp.com/vagrant/' + vagrant_version + '/vagrant_' + vagrant_version + '_' + processor + '.rpm > /tmp/vagrant.rpm',note='Downloading vagrant and installing')
			shutit.multisend('sudo rpm -i /tmp/vagrant.rpm',{'assword':pw})
			shutit.send('rm -f /tmp/vagrant.rpm')
		else:
			shutit.install('vagrant')
	# do not move this!
	if virt_method == 'libvirt' and shutit.send_and_get_output('vagrant plugin list | grep vagrant-libvirt') == '':
		if shutit.get_current_shutit_pexpect_session_environment().install_type == 'yum':
			shutit.install('gcc-c++')
		shutit.install('gcc')
		shutit.install('libvirt')
		shutit.install('libvirt-devel')
		shutit.install('qemu-kvm')
		pw = shutit.get_env_pass()
		shutit.multisend('sudo /opt/vagrant/embedded/bin/gem source -r https://rubygems.org/',{'assword':pw})
		shutit.multisend('sudo /opt/vagrant/embedded/bin/gem source -a http://rubygems.org/', {'Do you want to add this insecure source?':'y','assword':pw})
		shutit.multisend('sudo /opt/vagrant/embedded/bin/gem update --system --no-doc',{'assword':pw})
		shutit.multisend('sudo /opt/vagrant/embedded/bin/gem source -r http://rubygems.org/',{'assword':pw})
		shutit.multisend('sudo /opt/vagrant/embedded/bin/gem source -a https://rubygems.org/',{'assword':pw})
		shutit.multisend('sudo vagrant plugin install vagrant-libvirt',{'assword':pw})
	if virt_method == 'libvirt':
		pw = shutit.get_env_pass()
		shutit.multisend('sudo systemctl start libvirtd',{'assword':pw})
	else:
		if shutit.send_and_get_output("""vagrant version  | head -1 | awk '{print $3}'""") < '1.8.6':
			shutit.log('Vagrant version may be too low!')
			shutit.send('echo VAGRANT VERSION MAY BE TOO LOW SEE https://github.com/ianmiell/shutit-library/issues/1 && sleep 10')
	return True
