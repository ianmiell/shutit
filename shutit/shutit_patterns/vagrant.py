from __future__ import print_function
import os
import readline
import texttable
import shutit_util
from . import shutitfile

def setup_vagrant_pattern(shutit,
                          skel_path,
                          skel_delivery,
                          skel_domain,
                          skel_module_name,
                          skel_shutitfiles,
                          skel_domain_hash,
                          skel_depends,
                          skel_vagrant_num_machines,
                          skel_vagrant_machine_prefix,
                          skel_vagrant_ssh_access,
                          skel_vagrant_docker,
                          skel_vagrant_snapshot,
                          skel_vagrant_upload,
                          skel_vagrant_image_name):

################################################################################
# BEGIN ARGUMENT HANDLING
################################################################################
	# Gather requirements for multinode vagrant setup:
	options = []
	if skel_vagrant_num_machines is None:
		options.append({'name':'num_machines','question':'How many machines do you want?','value':'3','ok_values':[]})
	else:
		num_machines = skel_vagrant_num_machines
	if skel_vagrant_machine_prefix is None:
		options.append({'name':'machine_prefix','question':'What do you want to call the machines (eg superserver)?','value':'machine','ok_values':[]})
	else:
		machine_prefix = skel_vagrant_machine_prefix
	if skel_vagrant_ssh_access is None:
		options.append({'name':'ssh_access','question':'Do you want to have open ssh access between machines (yes or no)?','value':'yes','ok_values':['yes','no']})
	else:
		ssh_access = skel_vagrant_ssh_access
	if skel_vagrant_docker is None:
		options.append({'name':'docker','question':'Do you want Docker on the machine (yes or no)?','value':'no','ok_values':['yes','no']})
	else:
		docker = skel_vagrant_docker
	if skel_vagrant_snapshot is None:
		options.append({'name':'snapshot','question':'Do you want to snapshot the machine on completion (yes or no)?','value':'no','ok_values':['yes','no']})
	else:
		snapshot = skel_vagrant_snapshot
	if skel_vagrant_upload is None:
		options.append({'name':'upload','question':'Do you want to upload the snapshot on completion (yes or no)?','value':'no','ok_values':['yes','no']})
	else:
		upload = skel_vagrant_upload
	if skel_vagrant_image_name is None:
		options.append({'name':'image_name','question':'What base vagrant image you want?','value':'ubuntu/xenial64','ok_values':[]})
	else:
		image_name = skel_vagrant_image_name
	options.append({'name':'sudo_password','question':'Input sudo password to save time (will be saved in readonly-by-you file)','value':'','ok_values':[]})
	if options:
		while True:
			table = texttable.Texttable()
			count = 1
			rows = [['No.','Option','Current value']]
			for opt in options:
				rows.append([str(count),opt['question'],opt['value']])
				count += 1
			#table.set_deco(texttable.Texttable.HEADER)
			table.set_cols_dtype(['i','a','a'])
			table.set_cols_align(['r', "l", "r"])
			table.add_rows(rows)
			shutit.shutit_global_object.shutit_print(table.draw() + '\n')
			readline.set_startup_hook(lambda: readline.insert_text(''))
			for choice_li in ('5','4','3','2','1'):
				readline.add_history(choice_li)
			choice = shutit_util.util_raw_input(prompt='''
Choose an item to change if you want to change the default.

Input 'c' to continue to the build.

If you want to change a config, choose the number: ''')
			readline.set_startup_hook() 
			if choice in ('c','1','2','3','4','5','6','7'):
				if choice == 'c':
					break
				try:
					choice = int(choice)
				except ValueError:
					shutit.shutit_global_object.shutit_print('Bad value, ignoring')
					continue
			else:
				shutit.shutit_global_object.shutit_print('Bad value, ignoring')
				continue
			# Print out the actual choice....
			shutit.shutit_global_object.shutit_print(rows[choice][1])
			# off by one
			choice -= 1
			item = options[choice]
			value = shutit_util.get_input(msg='Input the value: ',color=None)
			if item['ok_values'] and value not in item['ok_values']:
				shutit.shutit_global_object.shutit_print('Bad value, ignoring')
				continue
			item['value'] = value
		for opt in options:
			if opt['name'] == 'num_machines':
				num_machines = int(opt['value'])
			if opt['name'] == 'machine_prefix':
				machine_prefix = opt['value']
			if opt['name'] == 'ssh_access':
				if opt['value'] == 'no':
					ssh_access = False
				elif opt['value'] == 'yes':
					ssh_access = True
				else:
					shutit.fail('Bad value for ssh_access')
			if opt['name'] == 'docker':
				if opt['value'] == 'no':
					docker = False
				elif opt['value'] == 'yes':
					docker = True
				else:
					shutit.fail('Bad value for docker')
			if opt['name'] == 'snapshot':
				if opt['value'] == 'no':
					snapshot = False
				elif opt['value'] == 'yes':
					snapshot = True
				else:
					shutit.fail('Bad value for snapshot')
			if opt['name'] == 'upload':
				if opt['value'] == 'no':
					upload = False
				elif opt['value'] == 'yes':
					upload = True
				else:
					shutit.fail('Bad value for upload')
			if opt['name'] == 'image_name':
				image_name = opt['value']
			if opt['name'] == 'sudo_password':
				sudo_password = opt['value']
	num_machines = int(num_machines)
################################################################################
# END ARGUMENT HANDLING
################################################################################

################################################################################
# BEGIN TEXT GOBBETS
################################################################################
	# Set up Vagrantfile data for the later
	machine_stanzas = ''
	vagrant_up_section = ''

	machines_update = '''
		# machines is a dict of dicts containing information about each machine for you to use.
		machines = {}'''
	for m in range(1,num_machines+1):
		machine_name = machine_prefix + str(m)
		machine_fqdn = machine_name + '.vagrant.test'
		# vagrant_image is calculated within the code later
		machine_stanzas += ('''
  config.vm.define "''' + machine_name + '''" do |''' + machine_name + '''|
    ''' + machine_name + """.vm.box = ''' + '"' + vagrant_image + '"' + '''
    """ + machine_name + '''.vm.hostname = "''' + machine_fqdn + '''"''' +
    '''
    config.vm.provider :virtualbox do |vb|
      vb.name = "''' + skel_module_name + '_' + str(m) + '''"
    end
  end''')
		machines_update += """
		machines.update({'""" + machine_name + """':{'fqdn':'""" + machine_fqdn + """'}})"""
	vagrant_up_section += '''
		try:
			pw = open('secret').read().strip()
		except IOError:
			pw = ''
		if pw == '':
			shutit.log("""You can get round this manual step by creating a 'secret' with your password: 'touch secret && chmod 700 secret'""",level=logging.CRITICAL)
			pw = shutit.get_env_pass()
			import time
			time.sleep(10)'''


	vagrant_dir_section_1 = """
		if shutit.build['vagrant_run_dir'] is None:
			shutit.build['vagrant_run_dir'] = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda:0))) + '/vagrant_run'
			timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
			shutit.build['module_name'] = '""" + skel_module_name + """_' + timestamp
			shutit.build['this_vagrant_run_dir'] = shutit.build['vagrant_run_dir'] + '/' + timestamp
		shutit.send(' command rm -rf ' + shutit.build['this_vagrant_run_dir'] + ' && command mkdir -p ' + shutit.build['this_vagrant_run_dir'] + ' && command cd ' + shutit.build['this_vagrant_run_dir'])"""
	vagrant_dir_section_n = """
		shutit.send(' command mkdir -p ' + shutit.build['this_vagrant_run_dir'] + ' && command cd ' + shutit.build['this_vagrant_run_dir'])"""

	vagrant_setup = r"""
		# Set up the sessions
		shutit_sessions = {}
		for machine in sorted(machines.keys()):
			shutit_sessions.update({machine:shutit.create_session('bash')})
		# Set up and validate landrush
		for machine in sorted(machines.keys()):
			shutit_session = shutit_sessions[machine]
			shutit_session.send('cd ' + shutit.build['this_vagrant_run_dir'])
			# Remove any existing landrush entry.
			shutit_session.send('vagrant landrush rm ' + machines[machine]['fqdn'])
			# Needs to be done serially for stability reasons.
			try:
				shutit_session.multisend('vagrant up --provider ' + shutit.cfg['shutit-library.virtualization.virtualization.virtualization']['virt_method'] + machine_name,{'assword for':pw,'assword:':pw})
			except NameError:
				shutit.multisend('vagrant up ' + machine,{'assword for':pw,'assword:':pw},timeout=99999)
			if shutit.send_and_get_output("vagrant status 2> /dev/null | grep -w ^" + machine + " | awk '{print $2}'") != 'running':
				shutit.pause_point("machine: " + machine + " appears not to have come up cleanly")
			ip = shutit.send_and_get_output('''vagrant landrush ls 2> /dev/null | grep -w ^''' + machines[machine]['fqdn'] + ''' | awk '{print $2}' ''')
			machines.get(machine).update({'ip':ip})
			shutit_session.login(command='vagrant ssh ' + machine)
			shutit_session.login(command='sudo su - ')
			# Correct /etc/hosts
			shutit_session.send(r'''cat <(echo $(ip -4 -o addr show scope global | grep -v 10.0.2.15 | head -1 | awk '{print $4}' | sed 's/\(.*\)\/.*/\1/') $(hostname)) <(cat /etc/hosts | grep -v $(hostname -s)) > /tmp/hosts && mv -f /tmp/hosts /etc/hosts''')
			# Correct any broken ip addresses.
			if shutit.send_and_get_output('''vagrant landrush ls | grep ''' + machine + ''' | grep 10.0.2.15 | wc -l''') != '0':
				shutit_session.log('A 10.0.2.15 landrush ip was detected for machine: ' + machine + ', correcting.',level=logging.WARNING)
				# This beaut gets all the eth0 addresses from the machine and picks the first one that it not 10.0.2.15.
				while True:
					ipaddr = shutit_session.send_and_get_output(r'''ip -4 -o addr show scope global | grep -v 10.0.2.15 | head -1 | awk '{print $4}' | sed 's/\(.*\)\/.*/\1/' ''')
					if ipaddr[0] not in ('1','2','3','4','5','6','7','8','9'):
						time.sleep(10)
					else:
						break
				# Send this on the host (shutit, not shutit_session)
				shutit.send('vagrant landrush set ' + machines[machine]['fqdn'] + ' ' + ipaddr)
			# Check that the landrush entry is there.
			shutit.send('vagrant landrush ls | grep -w ' + machines[machine]['fqdn'])
		# Gather landrush info
		for machine in sorted(machines.keys()):
			ip = shutit.send_and_get_output('''vagrant landrush ls 2> /dev/null | grep -w ^''' + machines[machine]['fqdn'] + ''' | awk '{print $2}' ''')
			machines.get(machine).update({'ip':ip})"""


	if ssh_access:
		copy_keys_code = '''
		for machine in sorted(machines.keys()):
			shutit_session = shutit_sessions[machine]
			root_password = 'root'
			shutit_session.install('net-tools') # netstat needed
			if not shutit_session.command_available('host'):
				shutit_session.install('bind-utils') # host needed
			shutit_session.multisend('passwd',{'assword:':root_password})
			shutit_session.send("""sed -i 's/.*PermitRootLogin.*/PermitRootLogin yes/g' /etc/ssh/sshd_config""")
			shutit_session.send("""sed -i 's/.*PasswordAuthentication.*/PasswordAuthentication yes/g' /etc/ssh/sshd_config""")
			shutit_session.send('service ssh restart || systemctl restart sshd')
			shutit_session.multisend('ssh-keygen',{'Enter':'','verwrite':'n'})
		for machine in sorted(machines.keys()):
			for copy_to_machine in machines:
				for item in ('fqdn','ip'):
					shutit_session.multisend('ssh-copy-id root@' + machines[copy_to_machine][item],{'assword:':root_password,'ontinue conn':'yes'})'''
	else:
		copy_keys_code = ''

	if docker:
		docker_code = '''
		for machine in sorted(machines.keys()):
			shutit_session = shutit_sessions[machine]
			# Workaround for docker networking issues + landrush.
			shutit_session.install('docker')
			shutit_session.insert_text('Environment=GODEBUG=netdns=cgo','/lib/systemd/system/docker.service',pattern='.Service.')
			shutit_session.send('mkdir -p /etc/docker',note='Create the docker config folder')
			shutit_session.send_file('/etc/docker/daemon.json',"""{
  "dns": ["8.8.8.8"]
}""",note='Use the google dns server rather than the vagrant one. Change to the value you want if this does not work, eg if google dns is blocked.')
			shutit_session.send('systemctl daemon-reload && systemctl restart docker')'''
	else:
		docker_code = ''
	user_code = '''
		for machine in sorted(machines.keys()):
			shutit_session = shutit_sessions[machine]
			shutit_session.run_script(r\'\'\'#!/bin/sh
# See https://raw.githubusercontent.com/ianmiell/vagrant-swapfile/master/vagrant-swapfile.sh
fallocate -l \'\'\' + shutit.cfg[self.module_id]['swapsize'] + r\'\'\' /swapfile
ls -lh /swapfile
chown root:root /swapfile
chmod 0600 /swapfile
ls -lh /swapfile
mkswap /swapfile
swapon /swapfile
swapon -s
grep -i --color swap /proc/meminfo
echo "\n/swapfile none            swap    sw              0       0" >> /etc/fstab\'\'\')
			shutit_session.multisend('adduser person',{'Enter new UNIX password':'person','Retype new UNIX password:':'person','Full Name':'','Phone':'','Room':'','Other':'','Is the information correct':'Y'})'''
	machine_seed_code = '''
		for machine in sorted(machines.keys()):
			shutit_session = shutit_sessions[machine]
			shutit_session.send('hostname')'''

	if snapshot:
		# TODO: add 'copy to snapshot folder function'
		# TODO: create snapshot subfolder
		snapshot_code = '''
		for machine in sorted(machines.keys()):
			shutit.send('vagrant snapshot save ' + machine,note='Snapshot the vagrant machine')'''
	else:
		snapshot_code = ''

	if upload:
		upload_code = '''
		# Create a stable box name for this particular build
		boxname_base = shutit.build['module_name'] + '_' + str(int(time.time()))
		for machine in sorted(machines.keys()):
			boxname = boxname_base + '_' + machine + '.box'
			shutit.send('vagrant package --output ' + boxname + ' --vagrantfile Vagrantfile '  + machine,note='Package the vagrant machine')
			shutit.send('mvn deploy:deploy-file -DgroupId=com.meirionconsulting -DartifactId=' + boxname + ' -Dversion=0.0.0.1 -Dpackaging=tar.gz -DrepositoryId=nexus.meirionconsulting.com -Durl=http://nexus.meirionconsulting.com/repository/maven-releases -Dfile=' + boxname,note='Push the vagrant box')'''
	else:
		upload_code = ''


	print("""

		shutit.log('''********************************************************************************

# Vagrantfile created in: ''' + shutit.build['vagrant_run_dir'] + '''
# Run:

cd ''' + shutit.build['vagrant_run_dir'] + ''' && vagrant status && vagrant landrush ls

# to get information about your machines' setup.

********************************************************************************''')""")

	if snapshot:
		print("""
		shutit.log('''********************************************************************************

Your VM images have been snapshotted in the folder ''' + shutit.build['vagrant_run_dir'] + '''

********************************************************************************
''')""")

	get_config_section = """
	def get_config(self, shutit):
		shutit.get_config(self.module_id,'vagrant_image',default='""" + image_name + """')
		shutit.get_config(self.module_id,'vagrant_provider',default='virtualbox')
		shutit.get_config(self.module_id,'gui',default='false')
		shutit.get_config(self.module_id,'memory',default='1024')
		shutit.get_config(self.module_id,'swapsize',default='2G')
		return True"""

	header = '# Generated by shutit skeleton\n'
	shared_imports = '''import random
import datetime
import logging
import string
import os
import inspect'''
################################################################################
# END TEXT GOBBETS
################################################################################

################################################################################
# FILE SETUP BEGIN
################################################################################
	# Set up files:
	# .gitignore
	gitignore_filename = skel_path + '/.gitignore'
	gitignore_file = open(gitignore_filename,'w+')
	gitignore_file.write('''*pyc
vagrant_run
secret''')
	gitignore_file.close()
	os.chmod(gitignore_filename,0o700)

	secretfile_filename = skel_path + '/secret'
	secretfile_file = open(secretfile_filename,'w+')
	secretfile_file.write(sudo_password)
	secretfile_file.close()
	os.chmod(secretfile_filename,0o400)

	# README.md
	readme_filename = skel_path + '/README.md'
	readme_file = open(readme_filename,'w+')
	readme_file.write('''

## Install

- virtualbox
- vagrant
- git
- python-pip

## Run

```
git clone --recursive [this repo]
cd [this repo file]
./run.sh
```
''')
	readme_file.close()
	os.chmod(readme_filename,0o700)

	# run.sh
	runsh_filename = skel_path + '/run.sh'
	runsh_file = open(runsh_filename,'w+')
	runsh_file.write('''#!/bin/bash
set -e
[[ -z "$SHUTIT" ]] && SHUTIT="$1/shutit"
[[ ! -a "$SHUTIT" ]] || [[ -z "$SHUTIT" ]] && SHUTIT="$(which shutit)"
if [[ ! -a "$SHUTIT" ]]
then
	echo "Must have shutit on path, eg export PATH=$PATH:/path/to/shutit_dir"
	exit 1
fi
./destroy_vms.sh
$SHUTIT build --echo -d bash -m shutit-library/vagrant -m shutit-library/virtualization -l debug "$@"
if [[ $? != 0 ]]
then
	exit 1
fi''')
	runsh_file.close()
	os.chmod(runsh_filename,0o755)

	# destroy_vms.sh
	destroyvmssh_filename = skel_path + '/destroy_vms.sh'
	destroyvmssh_file = open(destroyvmssh_filename,'w+')
	destroyvmssh_file_contents = '''#!/bin/bash'''
	if snapshot:
		destroyvmssh_file_contents += '''
FOLDER=$( ls $( cd $( dirname "${BASH_SOURCE[0]}" ) && pwd )/vagrant_run 2> /dev/null)
ANSWER='y'
if [[ $FOLDER != '' ]]
then
	echo "This is snapshotted - sure you want to continue deleting? (y/n)"
	echo See folder: vagrant_run/${FOLDER}
	read ANSWER
fi
if [[ ${ANSWER} != 'y' ]]
then
	echo Refusing to continue
	exit 1
fi'''
	destroyvmssh_file_contents += '''
MODULE_NAME=''' + skel_module_name + '''
rm -rf $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/vagrant_run/*
XARGS_FLAG='--no-run-if-empty'
if ! echo '' | xargs --no-run-if-empty >/dev/null 2>&1
then
	XARGS_FLAG=''
fi
if [[ $(command -v VBoxManage) != '' ]]
then
	while true
	do
		VBoxManage list runningvms | grep ${MODULE_NAME} | awk '{print $1}' | xargs $XARGS_FLAG -IXXX VBoxManage controlvm 'XXX' poweroff && VBoxManage list vms | grep ''' + skel_module_name + ''' | awk '{print $1}'  | xargs -IXXX VBoxManage unregistervm 'XXX' --delete
		# The xargs removes whitespace
		if [[ $(VBoxManage list vms | grep ${MODULE_NAME} | wc -l | xargs) -eq '0' ]]
		then
			break
		else
			ps -ef | grep virtualbox | grep ${MODULE_NAME} | awk '{print $2}' | xargs kill
			sleep 10
		fi
	done
fi
if [[ $(command -v virsh) ]] && [[ $(kvm-ok 2>&1 | command grep 'can be used') != '' ]]
then
	virsh list | grep ${MODULE_NAME} | awk '{print $1}' | xargs $XARGS_FLAG -n1 virsh destroy
fi'''
	destroyvmssh_file.write(destroyvmssh_file_contents)
	destroyvmssh_file.close()
	os.chmod(destroyvmssh_filename,0o755)

	# build.cnf
	os.system('mkdir -p ' + skel_path + '/configs')

	# git setup
	os.system('git init')
	os.system('git submodule init')
	os.system('git submodule add https://github.com/ianmiell/shutit-library')
	os.system('git submodule update')

	# User message
	log_message = '''
# Run:
cd ''' + skel_path + ''' && ./run.sh

# to run.
'''
	if upload:
		log_message += r'''

As you have chosen to upload, you may want to install maven and set your
~/.m2/settings.xml file to contain these settings:

<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"
   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
   xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0
                       https://maven.apache.org/xsd/settings-1.0.0.xsd">
   <localRepository/>
   <interactiveMode/>
   <usePluginRegistry/>
   <offline/>
   <pluginGroups/>
   <servers>
       <server>
         <id>nexus.meirionconsulting.com</id>
         <username>uploader</username>
         <password>uploader</password>
       </server>
   </servers>
   <mirrors/>
   <proxies/>
   <profiles/>
   <activeProfiles/>
</settings>

so you can upload vagrant boxes.
'''
	shutit.log(log_message,transient=True)
################################################################################
# FILE SETUP END
################################################################################

################################################################################
# BEGIN MODULE SETUP
################################################################################
################################################################################
# BEGIN SHUTITFILE HANDLING
################################################################################
# Handle shutitfiles. If there are no shutitfiles, handle separately.
# If there are more than one, you need to treat the first one differently.
	if skel_shutitfiles:
		_total = len(skel_shutitfiles)
		_count = 0
		for skel_shutitfile in skel_shutitfiles:
			_count += 1
			module_modifier = '_' + str(_count)
			new_module_filename = skel_path + '/' + os.path.join(skel_module_name + module_modifier + '.py')
			shutit.cfg['skeleton']['module_modifier'] = module_modifier
			(sections, skel_module_id, skel_module_name, _, _) = shutitfile.shutitfile_to_shutit_module(shutit, skel_shutitfile,skel_path,skel_domain,skel_module_name,skel_domain_hash,skel_delivery,skel_depends,_count,_total,module_modifier)
			shutit.cfg['skeleton']['header_section']      = sections['header_section']
			shutit.cfg['skeleton']['config_section']      = sections['config_section']
			shutit.cfg['skeleton']['build_section']       = sections['build_section']
			shutit.cfg['skeleton']['finalize_section']    = sections['finalize_section']
			shutit.cfg['skeleton']['test_section']        = sections['test_section']
			shutit.cfg['skeleton']['isinstalled_section'] = sections['isinstalled_section']
			shutit.cfg['skeleton']['start_section']       = sections['start_section']
			shutit.cfg['skeleton']['stop_section']        = sections['stop_section']
			shutit.cfg['skeleton']['final_section']       = sections['final_section']
			module_file = open(new_module_filename,'w+')

			# We only write out the heavy stuff for vagrant on the first time round
			if _count == 1:
				module_file.write(header + shared_imports + """
""" + shutit.cfg['skeleton']['header_section'] + """

	def build(self, shutit):
		vagrant_image = shutit.cfg[self.module_id]['vagrant_image']
		vagrant_provider = shutit.cfg[self.module_id]['vagrant_provider']
		gui = shutit.cfg[self.module_id]['gui']
		memory = shutit.cfg[self.module_id]['memory']
""" + vagrant_dir_section_1 + """
		if shutit.send_and_get_output('vagrant plugin list | grep landrush') == '':
			shutit.send('vagrant plugin install landrush')
		shutit.send('vagrant init ' + vagrant_image)
		shutit.send_file(shutit.build['this_vagrant_run_dir'] + '/Vagrantfile','''Vagrant.configure("2") do |config|
  config.landrush.enabled = true
  config.vm.provider "virtualbox" do |vb|
    vb.gui = ''' + gui + '''
    vb.memory = "''' + memory + '''"
  end
""" + machine_stanzas + """
end''')
""" + machines_update + """
""" + vagrant_up_section + """
""" + vagrant_setup + """
""" + copy_keys_code + """
""" + docker_code + """
""" + user_code + """
""" + shutit.cfg['skeleton']['build_section'] + """
""" + snapshot_code + """
""" + upload_code + """
		return True

""" + get_config_section + """

""" + shutit.cfg['skeleton']['config_section'] + """		return True

	def test(self, shutit):
""" + shutit.cfg['skeleton']['test_section'] + """		return True

	def finalize(self, shutit):
""" + shutit.cfg['skeleton']['finalize_section'] + """		return True

	def is_installed(self, shutit):
""" + shutit.cfg['skeleton']['isinstalled_section'] + """
		return False

	def start(self, shutit):
""" + shutit.cfg['skeleton']['start_section'] + """		return True

	def stop(self, shutit):
""" + shutit.cfg['skeleton']['stop_section'] + """		return True

def module():
	return """ + skel_module_name + module_modifier + """(
		'""" + skel_module_id + """', """ + skel_domain_hash + """.000""" + str(_count) + """,
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['""" + skel_depends + """','shutit-library.virtualization.virtualization.virtualization','tk.shutit.vagrant.vagrant.vagrant']
	)""")
			# In the non-first one, we don't have all the setup stuff (but we do have some!)
			else:
				module_file.write(header + shared_imports + """
""" + shutit.cfg['skeleton']['header_section'] + """

	def build(self, shutit):
""" + vagrant_dir_section_n + """
""" + shutit.cfg['skeleton']['build_section'] + """

""" + shutit.cfg['skeleton']['config_section'] + """		return True

	def test(self, shutit):
""" + shutit.cfg['skeleton']['test_section'] + """		return True

	def finalize(self, shutit):
""" + shutit.cfg['skeleton']['finalize_section'] + """		return True

	def is_installed(self, shutit):
""" + shutit.cfg['skeleton']['isinstalled_section'] + """
		return False

	def start(self, shutit):
""" + shutit.cfg['skeleton']['start_section'] + """		return True

	def stop(self, shutit):
""" + shutit.cfg['skeleton']['stop_section'] + """		return True

def module():
	return """ + skel_module_name + module_modifier + """(
		'""" + skel_module_id + """',""" + skel_domain_hash + """.000""" + str(_count) + """,
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['""" + skel_depends + """','shutit-library.virtualization.virtualization.virtualization','tk.shutit.vagrant.vagrant.vagrant']
	)""")
			module_file.close()
			# Set up build.cnf
			build_cnf_filename = skel_path + '/configs/build.cnf'
			if _count == 1:
				build_cnf_file = open(build_cnf_filename,'w+')
				build_cnf_file.write('''###############################################################################
# PLEASE NOTE: This file should be changed only by the maintainer.
# PLEASE NOTE: This file is only sourced if the "shutit build" command is run
#              and this file is in the relative path: configs/build.cnf
#              This is to ensure it is only sourced if _this_ module is the
#              target.
###############################################################################
# When this module is the one being built, which modules should be built along with it by default?
# This feeds into automated testing of each module.
[''' + skel_module_id + ''']
shutit.core.module.build:yes''')
				build_cnf_file.close()
			else:
				build_cnf_file = open(build_cnf_filename,'a')
				build_cnf_file.write('''
[''' + skel_domain + '''.''' +  skel_module_name + module_modifier + ''']
shutit.core.module.build:yes''')
				build_cnf_file.close()
		os.chmod(build_cnf_filename,0o400)
################################################################################
# END SHUTITFILE HANDLING
################################################################################
	else:
		# No shutitfiles to consider, so simpler logic here.
		shutit.cfg['skeleton']['header_section']      = 'from shutit_module import ShutItModule\n\nclass ' + skel_module_name + '(ShutItModule):\n'
		new_module_filename = skel_path + '/' + skel_module_name + '.py'
		module_file = open(new_module_filename,'w+')

		module_file.write(header + shared_imports + """
""" + shutit.cfg['skeleton']['header_section'] + """

	def build(self, shutit):
		vagrant_image = shutit.cfg[self.module_id]['vagrant_image']
		vagrant_provider = shutit.cfg[self.module_id]['vagrant_provider']
		gui = shutit.cfg[self.module_id]['gui']
		memory = shutit.cfg[self.module_id]['memory']
		shutit.build['vagrant_run_dir'] = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda:0))) + '/vagrant_run'
		shutit.build['module_name'] = '""" + skel_module_name + """_' + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
		shutit.build['this_vagrant_run_dir'] = shutit.build['vagrant_run_dir'] + '/' + shutit.build['module_name']
		shutit.send(' command rm -rf ' + shutit.build['this_vagrant_run_dir'] + ' && command mkdir -p ' + shutit.build['this_vagrant_run_dir'] + ' && command cd ' + shutit.build['this_vagrant_run_dir'])
		shutit.send('command rm -rf ' + shutit.build['this_vagrant_run_dir'] + ' && command mkdir -p ' + shutit.build['this_vagrant_run_dir'] + ' && command cd ' + shutit.build['this_vagrant_run_dir'])
		if shutit.send_and_get_output('vagrant plugin list | grep landrush') == '':
			shutit.send('vagrant plugin install landrush')
		shutit.send('vagrant init ' + vagrant_image)
		shutit.send_file(shutit.build['this_vagrant_run_dir'] + '/Vagrantfile','''Vagrant.configure("2") do |config|
  config.landrush.enabled = true
  config.vm.provider "virtualbox" do |vb|
    vb.gui = ''' + gui + '''
    vb.memory = "''' + memory + '''"
  end
""" + machine_stanzas + """
end''')
""" + machines_update + """
""" + vagrant_up_section + """
""" + vagrant_setup + """
""" + copy_keys_code + """
""" + docker_code + """
""" + user_code + """
""" + machine_seed_code + """
""" + snapshot_code + """
""" + upload_code + """
		return True

""" + get_config_section + """

	def test(self, shutit):
		return True

	def finalize(self, shutit):
		return True

	def is_installed(self, shutit):
		return False

	def start(self, shutit):
		return True

	def stop(self, shutit):
		return True

def module():
	return """ + skel_module_name + """(
		'""" + skel_domain + '''.''' + skel_module_name + """', """ + skel_domain_hash + """.0001,
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['""" + skel_depends + """','shutit-library.virtualization.virtualization.virtualization','tk.shutit.vagrant.vagrant.vagrant']
	)""")

		module_file.close()

		build_cnf_filename = skel_path + '/configs/build.cnf'
		build_cnf_file = open(build_cnf_filename,'w+')

		build_cnf_file.write('''###############################################################################
# PLEASE NOTE: This file should be changed only by the maintainer.
# PLEASE NOTE: This file is only sourced if the "shutit build" command is run
#              and this file is in the relative path: configs/build.cnf
#              This is to ensure it is only sourced if _this_ module is the
#              target.
###############################################################################
# When this module is the one being built, which modules should be built along with it by default?
# This feeds into automated testing of each module.
['''+skel_domain+'''.'''+skel_module_name+''']
shutit.core.module.build:yes''')

		build_cnf_file.close()
		os.chmod(build_cnf_filename,0o400)
################################################################################
# END MODULE SETUP
################################################################################
