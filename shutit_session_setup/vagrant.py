import random
import logging
import string
from shutit_session_setup import virtualization


def pre_build(shutit,
              vagrant_version='1.8.6',
              virt_method='virtualbox'):
	if not virtualization.pre_build(shutit, virt_method=virt_method):
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

                                                                                                                  
def setup_machines(shutit,
                   vagrant_image,
                   virt_method,
                   gui,
                   memory,
                   sourcepath,
                   module_base_name,
                   swapsize,
                   num_machines):

	assert isinstance(num_machines, str)
	assert isinstance(gui, bool)
	num_machines = int(num_machines)
	vagrant_run_dir = sourcepath + '/vagrant_run'
	module_base_name = module_base_name.replace('-','').replace('_','')
	module_name = module_base_name + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6)).replace('-','').replace('_','')
	this_vagrant_run_dir = vagrant_run_dir + '/' + module_name
	shutit.send(' command rm -rf ' + this_vagrant_run_dir + ' && command mkdir -p ' + this_vagrant_run_dir + ' && command cd ' + this_vagrant_run_dir, echo=False)
	# check whether vagrant box is already up
	if shutit.send_and_get_output('''vagrant global-status | sed -n '3,$p' | sed '/^The above/,$d' | awk '{print $2}' | grep ''' + module_name + ''' | wc -l''') != '0':
		# TODO: ask first
		lines = shutit.send_and_get_output('''vagrant global-status | sed -n '3,$p' | sed '/^The above/,$d' | grep ''' + module_name)
		shutit.send('''vagrant global-status | sed -n '3,$p' | sed '/^The above/,$d' | awk '{print $1, $2}' | grep ''' + module_name + ''' | awk {print $1}' | xargs -n1 vagrant-destroy''')

	if shutit.send_and_get_output('vagrant plugin list | grep landrush', echo=False) == '':
		shutit.send('vagrant plugin install landrush', echo=False)
	shutit.send('vagrant init ' + vagrant_image, echo=False)

	# Data structures.
	shutit_sessions = {}
	machines = {}

	vagrantfile_contents = '''Vagrant.configure("2") do |config|
  config.landrush.enabled = true
  config.vm.provider "virtualbox" do |vb|
    vb.gui = ''' + str(gui).lower() + '''
    vb.memory = "''' + memory + '''"
  end'''
	# TODO: check no hyphens or underscores in module_name as that can confuse things
	for m in range(1, num_machines+1):
		machine_name = module_base_name + str(m)
		vagrantfile_contents += '''

  config.vm.define "''' + machine_name + '''" do |''' + machine_name + '''|
    ''' + machine_name + '''.vm.box = ''' + '"' + vagrant_image + '"' + '''
    ''' + machine_name + '''.vm.hostname = "''' + machine_name + '''.vagrant.test"
    config.vm.provider :virtualbox do |vb|
      vb.name = "''' + machine_name + '''"
    end
  end'''
		vagrantfile_contents += '''
end'''
		# machines is a dict of dicts containing information about each machine for you to use.
		machine_fqdn = machine_name + '.vagrant.test'
		machines.update({machine_name:{'fqdn':machine_fqdn}})
	shutit.send_file(this_vagrant_run_dir+ '/Vagrantfile',vagrantfile_contents)
	module_base_name = None

	try:
		pw = open('secret').read().strip()
	except IOError:
		pw = ''
	if pw == '':
		shutit.log("""You can get round this manual step by creating a 'secret' with your password: 'touch secret && chmod 700 secret'""",level=logging.CRITICAL)
		pw = shutit.get_env_pass()
		import time
		time.sleep(10)

	# Set up the sessions.
	shutit_host_session = shutit.create_session(session_type='bash')
	for machine in sorted(machines.keys()):
		shutit_sessions.update({machine:shutit.create_session(session_type='bash', walkthrough=False)})
	# Set up and validate landrush.
	for machine in sorted(machines.keys()):
		shutit_session = shutit_sessions[machine]
		machine_name   = machines
		shutit_session.send('cd ' + this_vagrant_run_dir, echo=False)
		shutit_host_session.send('cd ' + this_vagrant_run_dir, echo=False)
		# Remove any existing landrush entry.
		shutit_host_session.send('vagrant landrush rm ' + machines[machine]['fqdn'], echo=False)
		# Needs to be done serially for stability reasons.
		try:
			shutit_host_session.multisend('vagrant up --provider ' + virt_method + ' ' + machine,{'assword for':pw,'assword:':pw}, echo=False)
		except NameError:
			shutit_host_session.multisend('vagrant up ' + machine,{'assword for':pw,'assword:':pw},timeout=99999, echo=False)
		if shutit_host_session.send_and_get_output("vagrant status 2> /dev/null | grep -w ^" + machine + " | awk '{print $2}'", echo=False) != 'running':
			shutit_host_session.pause_point("machine: " + machine + " appears not to have come up cleanly")
		ip = shutit_host_session.send_and_get_output('''vagrant landrush ls 2> /dev/null | grep -w ^''' + machines[machine]['fqdn'] + ''' | awk '{print $2}' ''', echo=False)
		machines.get(machine).update({'ip':ip})
		shutit_session.login(command='vagrant ssh ' + machine, echo=False)
		shutit_session.login(command='sudo su - ', echo=False)
		# Correct /etc/hosts
		shutit_session.send(r'''cat <(echo $(ip -4 -o addr show scope global | grep -v 10.0.2.15 | head -1 | awk '{print $4}' | sed 's/\(.*\)\/.*/\1/') $(hostname)) <(cat /etc/hosts | grep -v $(hostname -s)) > /tmp/hosts && mv -f /tmp/hosts /etc/hosts''', echo=False)
		# Correct any broken ip addresses.
		if shutit_host_session.send_and_get_output('''vagrant landrush ls | grep ''' + machine + ''' | grep 10.0.2.15 | wc -l''', echo=False) != '0':
			shutit_session.log('A 10.0.2.15 landrush ip was detected for machine: ' + machine + ', correcting.',level=logging.WARNING)
			# This beaut gets all the eth0 addresses from the machine and picks the first one that it not 10.0.2.15.
			while True:
				ipaddr = shutit_session.send_and_get_output(r'''ip -4 -o addr show scope global | grep -v 10.0.2.15 | head -1 | awk '{print $4}' | sed 's/\(.*\)\/.*/\1/' ''', echo=False)
				if ipaddr[0] not in ('1','2','3','4','5','6','7','8','9'):
					time.sleep(10)
				else:
					break
			# Send this on the host (shutit, not shutit_session)
			shutit_host_session.send('vagrant landrush set ' + machines[machine]['fqdn'] + ' ' + ipaddr)
		# Check that the landrush entry is there.
		shutit_host_session.send('vagrant landrush ls | grep -w ' + machines[machine]['fqdn'])
	# All done, so gather landrush info
	for machine in sorted(machines.keys()):
		ip = shutit_host_session.send_and_get_output('''vagrant landrush ls 2> /dev/null | grep -w ^''' + machines[machine]['fqdn'] + ''' | awk '{print $2}' ''', echo=False)
		machines.get(machine).update({'ip':ip})

	for machine in sorted(machines.keys()):
		shutit_session = shutit_sessions[machine]
		shutit_session.run_script(r'''#!/bin/sh
# See https://raw.githubusercontent.com/ianmiell/vagrant-swapfile/master/vagrant-swapfile.sh
fallocate -l ''' + swapsize + r''' /swapfile
ls -lh /swapfile
chown root:root /swapfile
chmod 0600 /swapfile
ls -lh /swapfile
mkswap /swapfile
swapon /swapfile
swapon -s
grep -i --color swap /proc/meminfo
echo "
/swapfile none            swap    sw              0       0" >> /etc/fstab''', echo=False)
		shutit_session.multisend('adduser person',
		    {'Enter new UNIX password':'person',
		     'Retype new UNIX password:':'person',
		     'Full Name':'',
		     'Phone':'',
		     'Room':'',
		     'Other':'',
		     'Is the information correct':'Y'}, echo=False)


	# TODO: copy ssh keys code
	# TODO: docker code
