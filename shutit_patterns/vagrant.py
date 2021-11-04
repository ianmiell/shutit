from __future__ import print_function
import os
import readline
import texttable
import jinja2
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
                          skel_vagrant_disk_size,
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
		# Add random word to default machine name to avoid vagrant machine name clash.
		options.append({'name':'machine_prefix','question':'What do you want to call the machines (eg superserver)?','value':'machine-' + shutit_util.random_word(),'ok_values':[]})
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
	if skel_vagrant_disk_size is None:
		options.append({'name':'disk_size','question':'What root disk size do you want?','value':'10GB','ok_values':[]})
	else:
		disk_size = skel_vagrant_disk_size
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
			if opt['name'] == 'disk_size':
				# TODO: check it's an int
				if True:
					pass
				else:
					shutit.fail('Bad value for disk_size')
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
		machine_name = machine_prefix + '-' + str(m)
		machine_fqdn = machine_name + '.vagrant.test'
		# vagrant_image is calculated within the code later
		machine_stanzas += ('''
  config.vm.define "''' + machine_name + '''" do |''' + machine_name + '''|
    ''' + machine_name + """.vm.box = ''' + '"' + vagrant_image + '"' + '''
    """ + machine_name + '''.vm.hostname = "''' + machine_fqdn + '''"''' +
    '''
    ''' + machine_name + '''.vm.provider :virtualbox do |vb|
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
			time.sleep(10)'''


	vagrant_dir_section_1 = """
		if shutit.build['vagrant_run_dir'] is None:
			################################################################################
			# Set up the Vagrant run directory
			shutit.build['vagrant_run_dir'] = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda:0))) + '/vagrant_run'
			timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
			shutit.build['module_name'] = '""" + skel_module_name + """_' + timestamp
			shutit.build['this_vagrant_run_dir'] = shutit.build['vagrant_run_dir'] + '/' + timestamp
		shutit.send(' command rm -rf ' + shutit.build['this_vagrant_run_dir'] + ' && command mkdir -p ' + shutit.build['this_vagrant_run_dir'] + ' && command cd ' + shutit.build['this_vagrant_run_dir'])"""
	vagrant_dir_section_n = """
		shutit.send(' command mkdir -p ' + shutit.build['this_vagrant_run_dir'] + ' && command cd ' + shutit.build['this_vagrant_run_dir'])"""

	vagrant_setup = r"""
		################################################################################
		# Set up the sessions
		shutit_sessions = {}
		for machine in sorted(machines.keys()):
			shutit_sessions.update({machine:shutit.create_session('bash', loglevel='DEBUG')})
		# Set up and validate landrush
		for machine in sorted(machines.keys()):
			shutit_session = shutit_sessions[machine]
			# Move into the vagrant run directory.
			shutit_session.send('cd ' + shutit.build['this_vagrant_run_dir'])
			# Remove any existing landrush entry.
			shutit_session.send('vagrant landrush rm ' + machines[machine]['fqdn'])
			# 'vagrant up' needs to be done serially for stability reasons.
			try:
				shutit_session.multisend('vagrant up --provider ' + shutit.cfg['shutit-library.virtualization.virtualization.virtualization']['virt_method'] + ' ' + machine,{'assword for':pw,'assword:':pw})
			except NameError:
				shutit.multisend('vagrant up ' + machine,{'assword for':pw,'assword:':pw},timeout=99999)
			if shutit.send_and_get_output("vagrant status 2> /dev/null | grep -w ^" + machine + " | awk '{print $2}'") != 'running':
				shutit.pause_point("machine: " + machine + " appears not to have come up cleanly")
			ip = shutit.send_and_get_output('''vagrant landrush ls 2> /dev/null | grep -w ^''' + machines[machine]['fqdn'] + ''' | awk '{print $2}' ''')
			# Set up machines dictionary with IP address.
			machines.get(machine).update({'ip':ip})
			# Log onto the vagrant host, and get root.
			shutit_session.login(command='vagrant ssh ' + machine)
			shutit_session.login(command='sudo su - ')
			# Allow IPv4 routing.
			shutit_session.send('sysctl -w net.ipv4.conf.all.route_localnet=1')
			# Correct /etc/hosts.
			shutit_session.send(r'''cat <(echo $(ip -4 -o addr show scope global | grep -v 10.0.2.15 | head -1 | awk '{print $4}' | sed 's/\(.*\)\/.*/\1/') $(hostname)) <(cat /etc/hosts | grep -v $(hostname -s)) > /tmp/hosts && mv -f /tmp/hosts /etc/hosts''')
			# Correct any broken ip addresses.
			if shutit.send_and_get_output('''vagrant landrush ls | grep ''' + machine + ''' | grep 10.0.2.15 | wc -l''') != '0':
				shutit_session.log('A 10.0.2.15 landrush ip was detected for machine: ' + machine + ', correcting.',level=logging.WARNING)
				# This gets all the eth0 addresses from the machine and picks the first one that it not 10.0.2.15.
				while True:
					ipaddr = shutit_session.send_and_get_output(r'''ip -4 -o addr show scope global | grep -v 10.0.2.15 | head -1 | awk '{print $4}' | sed 's/\(.*\)\/.*/\1/' ''')
					if ipaddr[0] not in ('1','2','3','4','5','6','7','8','9'):
						time.sleep(10)
					else:
						break
				# Send this on the host (ie calling the global shutit object, not shutit_session)
				shutit.send('vagrant landrush set ' + machines[machine]['fqdn'] + ' ' + ipaddr)
			# Check that the landrush entry is there.
			shutit.send('vagrant landrush ls | grep -w ' + machines[machine]['fqdn'])
		# Gather landrush info.
		for machine in sorted(machines.keys()):
			ip = shutit.send_and_get_output('''vagrant landrush ls 2> /dev/null | grep -w ^''' + machines[machine]['fqdn'] + ''' | awk '{print $2}' ''')
			# Set up machines dictionary with IP address.
			machines.get(machine).update({'ip':ip})"""

	hosts_file_code = ('\n'
	                   '		for machine in sorted(machines.keys()):\n'
	                   '			for machine_k in sorted(machines.keys()):\n'
	                   '				shutit_session = shutit_sessions[machine]\n'
	                   '''				shutit_session.send('echo ' + machines[machine_k]['ip'] + ' ' + machine_k + ' ' + machines[machine_k]['fqdn'] + ' >> /etc/hosts')\n''')


	if ssh_access:
		copy_keys_code = '''
		################################################################################
		# Set ssh access.
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
		docker_code = ('\n'
		               '		################################################################################\n'
		               '		# Set up docker.\n'
		               '		for machine in sorted(machines.keys()):\n'
		               '			shutit_session = shutit_sessions[machine]\n'
		               '			# Workaround for docker networking issues + landrush.\n'
		               "			shutit_session.install('docker')\n"
		               "			shutit_session.insert_text('Environment=GODEBUG=netdns=cgo','/lib/systemd/system/docker.service',pattern='.Service.')\n"
		               "			shutit_session.send('mkdir -p /etc/docker',note='Create the docker config folder')\n"
		               '''			shutit_session.send_file('/etc/docker/daemon.json',"""{\n'''
		               '  "dns": ["8.8.8.8"]\n'
		               '''}""",note='Use the google dns server rather than the vagrant one. Change to the value you want if this does not work, eg if google dns is blocked.')\n'''
		               "			shutit_session.send('systemctl daemon-reload && systemctl restart docker')")
	else:
		docker_code = ''
	user_code = ('\n'
	             '		################################################################################\n'
	             '		# Set up user and swapfile.\n'
	             '		for machine in sorted(machines.keys()):\n'
	             '			shutit_session = shutit_sessions[machine]\n'
	             '			# Set up swapfile\n'
	             "			shutit_session.run_script(r\'\'\'#!/bin/sh\n"
	             '# See https://raw.githubusercontent.com/ianmiell/vagrant-swapfile/master/vagrant-swapfile.sh\n'
	             "fallocate -l \'\'\' + shutit.cfg[self.module_id]['swapsize'] + r\'\'\' /swapfile\n"
	             'ls -lh /swapfile\n'
	             'chown root:root /swapfile\n'
	             'chmod 0600 /swapfile\n'
	             'ls -lh /swapfile\n'
	             'mkswap /swapfile\n'
	             'swapon /swapfile\n'
	             'swapon -s\n'
	             'grep -i --color swap /proc/meminfo\n'
	             '''echo "\n/swapfile none            swap    sw              0       0" >> /etc/fstab\'\'\')\n'''
	             "			shutit_session.multisend('adduser person',{'password:':'person','Enter new UNIX password':'person','Retype new UNIX password:':'person','Full Name':'','Phone':'','Room':'','Other':'','Is the information correct':'Y'})")
	machine_seed_code = ('\n'
	                     '		for machine in sorted(machines.keys()):\n'
	                     '			shutit_session = shutit_sessions[machine]\n'
	                     "			shutit_session.send('hostname')")

	if snapshot:
		# TODO: add 'copy to snapshot folder function'
		# TODO: create snapshot subfolder
		snapshot_code = ('\n'
		                 '		################################################################################\n'
		                 '		# Set up snapshots of Vagrant machines.\n'
		                 '		for machine in sorted(machines.keys()):\n'
		                 "			shutit.send('vagrant snapshot save ' + machine,note='Snapshot the vagrant machine')\n")
	else:
		snapshot_code = ''

	if upload:
		upload_code = ('\n'
		               '		################################################################################\n'
		               '		# Upload snapshots.\n'
		               '		# Create a stable box name for this particular build.\n'
		               "		boxname_base = shutit.build['module_name'] + '_' + str(int(time.time()))\n"
		               '		for machine in sorted(machines.keys()):\n'
		               "			boxname = boxname_base + '_' + machine + '.box'\n"
		               "			shutit.send('vagrant package --output ' + boxname + ' --vagrantfile Vagrantfile '  + machine,note='Package the vagrant machine')\n"
		               "			shutit.send('mvn deploy:deploy-file -DgroupId=com.meirionconsulting -DartifactId=' + boxname + ' -Dversion=0.0.0.1 -Dpackaging=tar.gz -DrepositoryId=nexus.meirionconsulting.com -Durl=http://nexus.meirionconsulting.com/repository/maven-releases -Dfile=' + boxname,note='Push the vagrant box')\n")
	else:
		upload_code = ''


# TODO get this info out
#	print("""
#
#		shutit.log('''********************************************************************************
#
## Vagrantfile created in: ''' + shutit.build['vagrant_run_dir'] + '''
## Run:
#
#cd ''' + shutit.build['vagrant_run_dir'] + ''' && vagrant status && vagrant landrush ls
#
## to get information about your machines' setup.
#
#********************************************************************************''')""")
#
#	if snapshot:
#		print("""
#		shutit.log('''********************************************************************************
#
#Your VM images have been snapshotted in the folder ''' + shutit.build['vagrant_run_dir'] + '''
#
#********************************************************************************
#''')""")

	get_config_section = ("\n"
	                      "	def get_config(self, shutit):\n"
	                      "		shutit.get_config(self.module_id,'vagrant_image',default='" + image_name + "')\n"
	                      "		shutit.get_config(self.module_id,'vagrant_provider',default='virtualbox')\n"
	                      "		shutit.get_config(self.module_id,'gui',default='false')\n"
	                      "		shutit.get_config(self.module_id,'memory',default='1024')\n"
	                      "		shutit.get_config(self.module_id,'swapsize',default='2G')\n"
	                      "		return True\n")

	header = '# Generated by shutit skeleton\n'
	shared_imports = ('''import random\n'''
	                  '''import datetime\n'''
	                  '''import logging\n'''
	                  '''import string\n'''
	                  '''import os\n'''
	                  '''import inspect\n'''
	                  '''import time\n''')
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
	gitignore_file.write('*pyc\n'
	                     'vagrant_run\n'
	                     'secret\n')
	gitignore_file.close()
	os.chmod(gitignore_filename,0o700)

	# secret
	secretfile_filename = skel_path + '/secret'
	secretfile_file = open(secretfile_filename,'w+')
	secretfile_file.write(sudo_password)
	secretfile_file.close()
	os.chmod(secretfile_filename,0o400)

	# run.py
	run_filename = skel_path + '/run.py'
	run_file = open(run_filename,'w+')
	run_file.write('def run(shutit_sessions, machines):\n'
	               "	print('machines:')\n"
	               '	print(machines)\n'
	               '	for machine in sorted(machines.keys()):\n'
	               '		term = shutit_sessions[machine]\n')
	for m in range(1,num_machines+1):
		machine_name = machine_prefix + str(m)
		machine_fqdn = machine_name + '.vagrant.test'
		machine_session_name = machine_name + '_term'
		run_file.write('		' + machine_session_name + " = shutit_sessions['" + machine_name + "']\n")
		run_file.write('		' + machine_session_name + ".send('echo in terminal $(hostname)')\n")
	run_file.close()
	os.chmod(run_filename,0o644)

	# README.md
	readme_filename = skel_path + '/README.md'
	readme_file = open(readme_filename,'w+')
	readme_file.write('\n'
	                  '\n'
	                  '## Install\n'
	                  '\n'
	                  '- virtualbox\n'
	                  '- vagrant\n'
	                  '- git\n'
	                  '- python-pip\n'
	                  '\n'
	                  '## Run\n'
	                  '\n'
	                  '```\n'
	                  'git clone --recursive [this repo]\n'
	                  'cd [this repo file]\n'
	                  './run.sh\n'
	                  '```\n')
	readme_file.close()
	os.chmod(readme_filename,0o700)

	# run.sh
	runsh_filename = skel_path + '/run.sh'
	runsh_file = open(runsh_filename,'w+')
	runsh_file.write('#!/bin/bash\n'
	                 'set -e\n'
	                 '[[ -z "$SHUTIT" ]] && SHUTIT="$1/shutit"\n'
	                 '[[ ! -a "$SHUTIT" ]] || [[ -z "$SHUTIT" ]] && SHUTIT="$(which shutit)"\n'
	                 'if [[ ! -a "$SHUTIT" ]]\n'
	                 'then\n'
	                 '	echo "Must have shutit on path, eg export PATH=$PATH:/path/to/shutit_dir"\n'
	                 '	exit 1\n'
	                 'fi\n'
	                 './destroy_vms.sh\n'
	                 '$SHUTIT build --echo -d bash -m shutit-library/vagrant -m shutit-library/virtualization -l debug "$@"\n'
	                 'if [[ $? != 0 ]]\n'
	                 'then\n'
	                 '	exit 1\n'
	                 'fi\n')
	runsh_file.close()
	os.chmod(runsh_filename,0o755)

	# destroy_vms.sh
	destroyvmssh_filename = skel_path + '/destroy_vms.sh'
	destroyvmssh_file = open(destroyvmssh_filename,'w+')
	destroyvmssh_file_contents = '#!/bin/bash\n'
	if snapshot:
		destroyvmssh_file_contents += ('\n'
	                                   'FOLDER=$( ls $( cd $( dirname "${BASH_SOURCE[0]}" ) && pwd )/vagrant_run 2> /dev/null)\n'
	                                   "ANSWER='y'\n"
	                                   'if [[ $FOLDER != '' ]]\n'
	                                   'then\n'
	                                   '	echo "This is snapshotted - sure you want to continue deleting? (y/n)"\n'
	                                   '	echo See folder: vagrant_run/${FOLDER}\n'
	                                   '	read ANSWER\n'
	                                   'fi\n'
	                                   "if [[ ${ANSWER} != 'y' ]]\n"
	                                   'then\n'
	                                   '	echo Refusing to continue\n'
	                                   '	exit 1\n'
	                                   'fi\n')
	destroyvmssh_file_contents += ('\nMODULE_NAME=' + skel_module_name + '\n'
	                               '''rm -rf $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/vagrant_run/*\n'''
	                               "XARGS_FLAG='--no-run-if-empty'\n"
	                               "if ! echo '' | xargs --no-run-if-empty >/dev/null 2>&1\n"
	                               'then\n'
	                               "	XARGS_FLAG=''\n"
	                               'fi\n'
	                               "if [[ $(command -v VBoxManage) != '' ]]\n"
	                               'then\n'
	                               '	while true\n'
	                               '	do\n'
	                               '''		VBoxManage list runningvms | grep ${MODULE_NAME} | awk '{print $1}' | xargs $XARGS_FLAG -IXXX VBoxManage controlvm 'XXX' poweroff && VBoxManage list vms | grep ''' + skel_module_name + ''' | awk '{print $1}'  | xargs -IXXX VBoxManage unregistervm 'XXX' --delete\n'''
	                               '		# The xargs removes whitespace\n'
	                               "		if [[ $(VBoxManage list vms | grep ${MODULE_NAME} | wc -l | xargs) -eq '0' ]]\n"
	                               '		then\n'
	                               '			break\n'
	                               '		else\n'
	                               "			ps -ef | grep virtualbox | grep ${MODULE_NAME} | awk '{print $2}' | xargs kill\n"
	                               '			sleep 10\n'
	                               '		fi\n'
	                               '	done\n'
	                               'fi\n'
	                               "if [[ $(command -v virsh) ]] && [[ $(kvm-ok 2>&1 | command grep 'can be used') != '' ]]\n"
	                               'then\n'
	                               "	if [[ $(id -u) != '0' ]]\n"
	                               '	then\n'
	                               '	    echo If using kvm, then you may need to be root or give perms to this user to destroy the pre-existing machines\n'
	                               '	fi\n'
	                               "	virsh list | grep ${MODULE_NAME} | awk '{print $1}' | xargs $XARGS_FLAG -n1 virsh destroy\n"
	                               'fi\n')
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
	log_message = ('\n'
	               '# Run:\n'
	               'cd ' + skel_path + ' && ./run.sh\n'
	               '\n'
	               '# to run.\n')

	if upload:
		log_message += r('\n'
		                 '\n'
		                 'As you have chosen to upload, you may want to install maven and set your\n'
		                 '~/.m2/settings.xml file to contain these settings:\n'
		                 '\n'
		                 '<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"\n'
		                 '   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
		                 '   xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0\n'
		                 '                       https://maven.apache.org/xsd/settings-1.0.0.xsd">\n'
		                 '   <localRepository/>\n'
		                 '   <interactiveMode/>\n'
		                 '   <usePluginRegistry/>\n'
		                 '   <offline/>\n'
		                 '   <pluginGroups/>\n'
		                 '   <servers>\n'
		                 '       <server>\n'
		                 '         <id>nexus.meirionconsulting.com</id>\n'
		                 '         <username>uploader</username>\n'
		                 '         <password>uploader</password>\n'
		                 '       </server>\n'
		                 '   </servers>\n'
		                 '   <mirrors/>\n'
		                 '   <proxies/>\n'
		                 '   <profiles/>\n'
		                 '   <activeProfiles/>\n'
		                 '</settings>\n'
		                 '\n'
		                 'so you can upload vagrant boxes.\n')
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
				template = jinja2.Template((header + shared_imports + "\n{{ shutit.cfg['skeleton']['header_section'] }}\n"
				                            '\n'
				                            '	def build(self, shutit):\n'
				                            '		################################################################################\n'
				                            '		# Set up vagrant run dir\n'
				                            "		vagrant_image = shutit.cfg[self.module_id]['vagrant_image']\n"
				                            "		vagrant_provider = shutit.cfg[self.module_id]['vagrant_provider']\n"
				                            "		gui = shutit.cfg[self.module_id]['gui']\n"
				                            "		memory = shutit.cfg[self.module_id]['memory']\n"
				                            '{{ vagrant_dir_section_1 }}\n'
				                            "		if shutit.send_and_get_output('vagrant plugin list | grep landrush') == '':\n"
				                            "			shutit.send('vagrant plugin install landrush')\n"
				                            "		if shutit.send_and_get_output('vagrant plugin list | grep vagrant-disksize') == '':\n"
				                            "			shutit.send('vagrant plugin install vagrant-disksize')\n"
				                            "		shutit.send('vagrant init ' + vagrant_image)\n"
				                            """		shutit.send_file(shutit.build['this_vagrant_run_dir'] + '/Vagrantfile','''Vagrant.configure("2") do |config|\n"""
				                            '  config.landrush.enabled = true\n'
				                            '''  config.disksize.size = '""" + disk_size + """\n'''
				                            '  config.vm.provider "virtualbox" do |vb|\n'
				                            "    vb.gui = ''' + gui + '''\n"
				                            """    vb.memory = "''' + memory + '''"\n"""
				                            '  end\n'
				                            '{{ machine_stanzas }}\n'
				                            "end''')\n"
				                            '{{ machines_update }}\n'
				                            '{{ vagrant_up_section }}\n'
				                            '{{ vagrant_setup }}\n'
				                            '{{ copy_keys_code }}\n'
				                            '{{ hosts_file_code }}\n'
				                            '{{ docker_code }}\n'
				                            '{{ user_code }}\n'
				                            "{{ shutit.cfg['skeleton']['build_section'] }}\n"
				                            '{{ snapshot_code }}\n'
				                            '{{ upload_code }}\n'
				                            '		################################################################################\n'
				                            '		# Your code here\n'
				                            '		import run\n'
				                            '		run.run(shutit_session, machines)\n'
				                            '\n'
				                            '		return True\n'
				                            '\n'
				                            '{{ get_config_section }}\n'
				                            '\n'
				                            "{{ shutit.cfg['skeleton']['config_section'] }}		return True\n"
				                            '\n'
				                            '	def test(self, shutit):\n'
				                            "{{ shutit.cfg['skeleton']['test_section'] }}		return True\n"
				                            '\n'
				                            '	def finalize(self, shutit):\n'
				                            "{{ shutit.cfg['skeleton']['finalize_section'] }}		return True\n"
				                            '\n'
				                            '	def is_installed(self, shutit):\n'
				                            "{{ shutit.cfg['skeleton']['isinstalled_section'] }}\n"
				                            '		return False\n'
				                            '\n'
				                            '	def start(self, shutit):\n'
				                            "{{ shutit.cfg['skeleton']['start_section'] }}		return True\n"
				                            '\n'
				                            '	def stop(self, shutit):\n'
				                            "{{ shutit.cfg['skeleton']['stop_section'] }}		return True\n"
				                            '\n'
				                            'def module():\n'
				                            '	return {{ skel_module_name }}{{ module_modifier }}(\n'
				                            "		'{{ skel_module_id }}', {{ skel_domain_hash }}.000{{ str(_count) }},\n"
				                            "		description='',\n"
				                            "		maintainer='',\n"
				                            "		delivery_methods=['bash'],\n"
				                            "		depends=['{{ skel_depends }}','shutit-library.virtualization.virtualization.virtualization','tk.shutit.vagrant.vagrant.vagrant']\n"
				                            '	)""")\n'
				                            "			# In the non-first one, we don't have all the setup stuff (but we do have some!)\n"
				                            '			else:\n'
				                            '				module_file.write(header + shared_imports + """\n'
				                            "{{ shutit.cfg['skeleton']['header_section'] }}\n"
				                            '\n'
				                            '	def build(self, shutit):\n'
				                            '{{ vagrant_dir_section_n }}\n'
				                            "{{ shutit.cfg['skeleton']['build_section'] }}\n"
				                            '\n'
				                            "{{ shutit.cfg['skeleton']['config_section'] }}		return True\n"
				                            '\n'
				                            '	def test(self, shutit):\n'
				                            "{{ shutit.cfg['skeleton']['test_section'] }}		return True\n"
				                            '\n'
				                            '	def finalize(self, shutit):\n'
				                            "{{ shutit.cfg['skeleton']['finalize_section'] }}		return True\n"
				                            '\n'
				                            '	def is_installed(self, shutit):\n'
				                            "{{ shutit.cfg['skeleton']['isinstalled_section'] }}\n"
				                            '		return False\n'
				                            '\n'
				                            '	def start(self, shutit):\n'
				                            "{{ shutit.cfg['skeleton']['start_section'] }}		return True\n"
				                            '\n'
				                            '	def stop(self, shutit):\n'
				                            "{{ shutit.cfg['skeleton']['stop_section'] }}		return True\n"
				                            '\n'
				                            'def module():\n'
				                            '	return {{ skel_module_name }}{{ module_modifier }}(\n'
				                            "		'{{ skel_module_id }}',{{ skel_domain_hash }}.000{{ str(_count) }},\n"
				                            "		description='',\n"
				                            "		maintainer='',\n"
				                            "		delivery_methods=['bash'],\n"
				                            "		depends=['{{ skel_depends }}','shutit-library.virtualization.virtualization.virtualization','tk.shutit.vagrant.vagrant.vagrant']\n"
				                            '	)"""\n'))
				module_file.write(template.render(vars()))
			module_file.close()
			# Set up build.cnf
			build_cnf_filename = skel_path + '/configs/build.cnf'
			if _count == 1:
				build_cnf_file = open(build_cnf_filename,'w+')
				build_cnf_file.write(('###############################################################################\n'
				                      '# PLEASE NOTE: This file should be changed only by the maintainer.\n'
				                      '# PLEASE NOTE: This file is only sourced if the "shutit build" command is run\n'
				                      '#              and this file is in the relative path: configs/build.cnf\n'
				                      '#              This is to ensure it is only sourced if _this_ module is the\n'
				                      '#              target.\n'
				                      '###############################################################################\n'
				                      '# When this module is the one being built, which modules should be built along with it by default?\n'
				                      '# This feeds into automated testing of each module.\n'
				                      '[' + skel_module_id + ']\n'
				                      'shutit.core.module.build:yes\n'))
				build_cnf_file.close()
			else:
				build_cnf_file = open(build_cnf_filename,'a')
				build_cnf_file.write(('\n'
				                      '''[''' + skel_domain + '''.''' +  skel_module_name + module_modifier + ''']\n'''
				                      '''shutit.core.module.build:yes\n'''))
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

		template = jinja2.Template((header + shared_imports + '\n'
		                            "{{ shutit.cfg['skeleton']['header_section'] }}\n"
		                            '\n'
		                            '	def build(self, shutit):\n'
		                            '		################################################################################\n'
		                            '		# Set up vagrant run dir\n'
		                            "		vagrant_image = shutit.cfg[self.module_id]['vagrant_image']\n"
		                            "		vagrant_provider = shutit.cfg[self.module_id]['vagrant_provider']\n"
		                            "		gui = shutit.cfg[self.module_id]['gui']\n"
		                            "		memory = shutit.cfg[self.module_id]['memory']\n"
		                            "		shutit.build['vagrant_run_dir'] = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda:0))) + '/vagrant_run'\n"
		                            "		shutit.build['module_name'] = '{{ skel_module_name }}_' + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))\n"
		                            "		shutit.build['this_vagrant_run_dir'] = shutit.build['vagrant_run_dir'] + '/' + shutit.build['module_name']\n"
		                            "		shutit.send(' command rm -rf ' + shutit.build['this_vagrant_run_dir'] + ' && command mkdir -p ' + shutit.build['this_vagrant_run_dir'] + ' && command cd ' + shutit.build['this_vagrant_run_dir'])\n"
		                            "		shutit.send('command rm -rf ' + shutit.build['this_vagrant_run_dir'] + ' && command mkdir -p ' + shutit.build['this_vagrant_run_dir'] + ' && command cd ' + shutit.build['this_vagrant_run_dir'])\n"
		                            "		if shutit.send_and_get_output('vagrant plugin list | grep landrush') == '':\n"
		                            "			shutit.send('vagrant plugin install landrush')\n"
		                            "		shutit.send('vagrant init ' + vagrant_image)\n"
		                            """		shutit.send_file(shutit.build['this_vagrant_run_dir'] + '/Vagrantfile','''Vagrant.configure("2") do |config|\n"""
		                            '  config.landrush.enabled = true\n'
		                            '  config.vm.provider "virtualbox" do |vb|\n'
		                            "    vb.gui = ''' + gui + '''\n"
		                            """    vb.memory = "''' + memory + '''"\n"""
		                            '  end\n'
		                            '{{ machine_stanzas }}\n'
		                            "end''')\n"
		                            '{{ machines_update }}\n'
		                            '\n'
		                            '{{ vagrant_up_section }}\n'
		                            '\n'
		                            '{{ vagrant_setup }}\n'
		                            '\n'
		                            '{{ copy_keys_code }}\n'
		                            '\n'
				                    '{{ hosts_file_code }}\n'
		                            '\n'
		                            '{{ docker_code }}\n'
		                            '\n'
		                            '{{ user_code }}\n'
		                            '\n'
		                            '{{ machine_seed_code }}\n'
		                            '\n'
		                            '{{ snapshot_code }}\n'
		                            '\n'
		                            '{{ upload_code }}\n'
		                            '		################################################################################\n'
		                            '		# Your code here\n'
		                            '		import run\n'
		                            '		run.run(shutit_sessions, machines)\n'
		                            '		return True\n'
		                            '\n'
		                            '{{ get_config_section }}\n'
		                            '\n'
		                            '	def test(self, shutit):\n'
		                            '		return True\n'
		                            '\n'
		                            '	def finalize(self, shutit):\n'
		                            '		return True\n'
		                            '\n'
		                            '	def is_installed(self, shutit):\n'
		                            '		return False\n'
		                            '\n'
		                            '	def start(self, shutit):\n'
		                            '		return True\n'
		                            '\n'
		                            '	def stop(self, shutit):\n'
		                            '		return True\n'
		                            '\n'
		                            'def module():\n'
		                            '	return {{ skel_module_name }}(\n'
		                            "		'{{ skel_domain }}.{{ skel_module_name }}', {{ skel_domain_hash }}.0001,\n"
		                            "		description='',\n"
		                            "		maintainer='',\n"
		                            "		delivery_methods=['bash'],\n"
		                            "		depends=['{{ skel_depends }}','shutit-library.virtualization.virtualization.virtualization','tk.shutit.vagrant.vagrant.vagrant']\n"
		                            '	)\n'))
		module_file.write(template.render(vars()))
		module_file.close()

		build_cnf_filename = skel_path + '/configs/build.cnf'
		build_cnf_file = open(build_cnf_filename,'w+')

		build_cnf_file.write(('###############################################################################\n'
		                      '# PLEASE NOTE: This file should be changed only by the maintainer.\n'
		                      '# PLEASE NOTE: This file is only sourced if the "shutit build" command is run\n'
		                      '#              and this file is in the relative path: configs/build.cnf\n'
		                      '#              This is to ensure it is only sourced if _this_ module is the\n'
		                      '#              target.\n'
		                      '###############################################################################\n'
		                      '# When this module is the one being built, which modules should be built along with it by default?\n'
		                      '# This feeds into automated testing of each module.\n'
		                      '[' + skel_domain + '.' + skel_module_name + ']\n'
		                      'shutit.core.module.build:yes'))

		build_cnf_file.close()
		os.chmod(build_cnf_filename,0o400)
################################################################################
# END MODULE SETUP
################################################################################
