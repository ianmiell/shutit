def pre_build(shutit, virt_method='virtualbox'):
	if virt_method == 'virtualbox':
		if not shutit.command_available('VBoxManage'):
			if shutit.get_current_shutit_pexpect_session_environment().install_type == 'apt':
				shutit.send('echo "deb http://download.virtualbox.org/virtualbox/debian $(lsb_release -s -c) contrib" >> /etc/apt/sources.list ')
				shutit.send('wget -qO- https://www.virtualbox.org/download/oracle_vbox.asc | sudo apt-key add -')
				shutit.send('apt-get update')
				shutit.install('virtualbox-5.0')
			else:
				shutit.install('virtualbox')
	elif virt_method == 'libvirt':
		# Is this a good enough test of whether virsh exists?
		if not shutit.command_available('virsh'):
			shutit.install('kvm')
			shutit.install('libvirt')
			shutit.install('libvirt-devel')
			shutit.install('qemu-kvm')
			shutit.send('systemctl start libvirtd')
	else:
		return False
	return True
