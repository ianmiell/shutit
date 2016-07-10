import os
import shutit_global
from . import shutitfile

def setup_vagrant_pattern(skel_path,
                          skel_delivery,
                          skel_domain,
                          skel_module_name,
                          skel_shutitfiles, 
                          skel_domain_hash,
                          skel_depends):

	shutit = shutit_global.shutit
	# run.sh
	runsh_filename = skel_path + '/run.sh'
	runsh_file = open(runsh_filename,'w+')
	runsh_file.write('''#!/bin/bash
bash ./destroy_vms.sh
[[ -z "$SHUTIT" ]] && SHUTIT="$1/shutit"
[[ ! -a "$SHUTIT" ]] || [[ -z "$SHUTIT" ]] && SHUTIT="$(which shutit)"
if [[ ! -a "$SHUTIT" ]]
then
	echo "Must have shutit on path, eg export PATH=$PATH:/path/to/shutit_dir"
	exit 1
fi
$SHUTIT build -d bash -m shutit-library/vagrant -m shutit-library/virtualbox "$@"
if [[ $? != 0 ]]
then
	exit 1
fi''')
	runsh_file.close()
	os.chmod(runsh_filename,0o755)

	# destroy_vms.sh
	destroyvmssh_filename = skel_path + '/destroy_vms.sh'
	destroyvmssh_file = open(destroyvmssh_filename,'w+')
	destroyvmssh_file.write('''
#!/bin/bash
if [[ $(command -v VBoxManage) != '' ]]
then
	while true 
	do
		VBoxManage list runningvms | grep ''' + skel_module_name + ''' | awk '{print $1}' | xargs -IXXX VBoxManage controlvm 'XXX' poweroff && VBoxManage list vms | grep ''' + skel_module_name + ''' | awk '{print $1}'  | xargs -IXXX VBoxManage unregistervm 'XXX' --delete
		# The xargs removes whitespace
		if [[ $(VBoxManage list vms | grep ''' + skel_module_name + ''' | wc -l | xargs) -eq '0' ]]
		then
			break
		else
			ps -ef | grep virtualbox | grep ''' + skel_module_name + ''' | awk '{print $2}' | xargs kill
			sleep 10
		fi
	done
fi''')
	destroyvmssh_file.close()
	os.chmod(destroyvmssh_filename,0o755)

	# build.cnf file
	os.system('mkdir -p ' + skel_path + '/configs')

	os.system('git init')
	os.system('git submodule init')
	os.system('git submodule add https://github.com/ianmiell/shutit-library')

	# User message
	shutit.log('''# Run:
cd ''' + skel_path + ''' && ./run.sh
# to run.''',transient=True)

	# Handle shutitfiles
	if skel_shutitfiles:
		_total = len(skel_shutitfiles)
		_count = 0
		for skel_shutitfile in skel_shutitfiles:
			_count += 1
			module_modifier = '_' + str(_count)
			new_module_filename = skel_path + '/' + os.path.join(skel_module_name + module_modifier + '.py')
			shutit.cfg['skeleton']['module_modifier'] = module_modifier
			(sections, skel_module_id, skel_module_name, default_include, ok) = shutitfile.shutitfile_to_shutit_module(skel_shutitfile,skel_path,skel_domain,skel_module_name,skel_domain_hash,skel_delivery,skel_depends,_count,_total,module_modifier)
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
			if _count == 1 or True:
				module_file.write("""import random
import string

""" + shutit.cfg['skeleton']['header_section'] + """

	def build(self, shutit):
		vagrant_image = shutit.cfg[self.module_id]['vagrant_image']
		vagrant_provider = shutit.cfg[self.module_id]['vagrant_provider']
		gui = shutit.cfg[self.module_id]['gui']
		memory = shutit.cfg[self.module_id]['memory']
		module_name = '""" + skel_module_name + """_' + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
		shutit.send('rm -rf /tmp/' + module_name + ' && mkdir -p /tmp/' + module_name + ' && cd /tmp/' + module_name)
		shutit.send('vagrant init ' + vagrant_image)
		shutit.send_file('/tmp/' + module_name + '/Vagrantfile','''
Vagrant.configure(2) do |config|
  config.vm.box = "''' + vagrant_image + '''"
  # config.vm.box_check_update = false
  # config.vm.network "forwarded_port", guest: 80, host: 8080
  # config.vm.network "private_network", ip: "192.168.33.10"
  # config.vm.network "public_network"
  # config.vm.synced_folder "../data", "/vagrant_data"
  config.vm.provider "virtualbox" do |vb|
    vb.gui = ''' + gui + '''
    vb.memory = "''' + memory + '''"
    vb.name = """ + '"' + skel_module_name + '''"''' + """
  end
end''')
		shutit.send('vagrant up --provider virtualbox',timeout=99999)
		shutit.login(command='vagrant ssh')
		shutit.login(command='sudo su -',password='vagrant')

""" + shutit.cfg['skeleton']['build_section'] + """

		shutit.logout()
		shutit.logout()
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id,'vagrant_image',default='ubuntu/trusty64')
		shutit.get_config(self.module_id,'vagrant_provider',default='virtualbox')
		shutit.get_config(self.module_id,'gui',default='false')
		shutit.get_config(self.module_id,'memory',default='1024')
""" + shutit.cfg['skeleton']['config_section'] + """
		return True

	def test(self, shutit):
""" + shutit.cfg['skeleton']['test_section'] + """
		return True

	def finalize(self, shutit):
""" + shutit.cfg['skeleton']['finalize_section'] + """
		return True

	def isinstalled(self, shutit):
""" + shutit.cfg['skeleton']['isinstalled_section'] + """
		return False

	def start(self, shutit):
""" + shutit.cfg['skeleton']['start_section'] + """
		return True

	def stop(self, shutit):
""" + shutit.cfg['skeleton']['stop_section'] + """
		return True

def module():
	return """ + skel_module_name + """(
		'""" + skel_module_id + """', """ + skel_domain_hash + """.000""" + str(_count) + """,
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['""" + skel_depends + """','shutit-library.virtualbox.virtualbox.virtualbox','tk.shutit.vagrant.vagrant.vagrant']
	)""")
			else:
				module_file.write("""import random
import string

""" + shutit.cfg['skeleton']['header_section'] + """

	def build(self, shutit):
		shutit.login(command='vagrant ssh')
		shutit.login(command='sudo su -',password='vagrant')
""" + shutit.cfg['skeleton']['config_section'] + """
		return True

	def test(self, shutit):
""" + shutit.cfg['skeleton']['test_section'] + """
		return True

	def finalize(self, shutit):
""" + shutit.cfg['skeleton']['finalize_section'] + """
		return True

	def isinstalled(self, shutit):
""" + shutit.cfg['skeleton']['isinstalled_section'] + """
		return False

	def start(self, shutit):
""" + shutit.cfg['skeleton']['start_section'] + """
		return True

	def stop(self, shutit):
""" + shutit.cfg['skeleton']['stop_section'] + """
		return True

def module():
	return """ + skel_module_name + """(
		'""" + skel_module_id + """',""" + skel_domain_hash + """.000""" + str(_count) + """,
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['""" + skel_depends + """','shutit-library.virtualbox.virtualbox.virtualbox','tk.shutit.vagrant.vagrant.vagrant']
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
	else:
		shutit.cfg['skeleton']['header_section']      = 'from shutit_module import ShutItModule\n\nclass ' + skel_module_name + '(ShutItModule):\n'
		shutit.cfg['skeleton']['config_section']      = ''
		shutit.cfg['skeleton']['build_section']       = ''
		shutit.cfg['skeleton']['finalize_section']    = ''
		shutit.cfg['skeleton']['test_section']        = ''
		shutit.cfg['skeleton']['isinstalled_section'] = ''
		shutit.cfg['skeleton']['start_section']       = ''
		shutit.cfg['skeleton']['stop_section']        = ''
		new_module_filename = skel_path + '/' + skel_module_name + '.py'
		module_file = open(new_module_filename,'w+')
		module_file.write('''import random
import string

''' + shutit.cfg['skeleton']['header_section'] + """

	def build(self, shutit):
		vagrant_image = shutit.cfg[self.module_id]['vagrant_image']
		vagrant_provider = shutit.cfg[self.module_id]['vagrant_provider']
		gui = shutit.cfg[self.module_id]['gui']
		memory = shutit.cfg[self.module_id]['memory']
		module_name = '""" + skel_module_name + """_' + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
		shutit.send('rm -rf /tmp/' + module_name + ' && mkdir -p /tmp/' + module_name + ' && cd /tmp/' + module_name)
		shutit.send('vagrant init ' + vagrant_image)
		shutit.send_file('/tmp/' + module_name + '/Vagrantfile','''
Vagrant.configure(2) do |config|
  config.vm.box = "''' + vagrant_image + '''"
  # config.vm.box_check_update = false
  # config.vm.network "forwarded_port", guest: 80, host: 8080
  # config.vm.network "private_network", ip: "192.168.33.10"
  # config.vm.network "public_network"
  # config.vm.synced_folder "../data", "/vagrant_data"
  config.vm.provider "virtualbox" do |vb|
    vb.gui = ''' + gui + '''
    vb.memory = "''' + memory + '''"
    vb.name = """ + '"' + skel_module_name + '''"''' + """
  end
end''')
		shutit.send('vagrant up --provider virtualbox',timeout=99999)
		shutit.login(command='vagrant ssh')
		shutit.login(command='sudo su -',password='vagrant')

""" + shutit.cfg['skeleton']['build_section'] + """

		shutit.logout()
		shutit.logout()
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id,'vagrant_image',default='ubuntu/trusty64')
		shutit.get_config(self.module_id,'vagrant_provider',default='virtualbox')
		shutit.get_config(self.module_id,'gui',default='false')
		shutit.get_config(self.module_id,'memory',default='1024')
""" + shutit.cfg['skeleton']['config_section'] + """
		return True

	def test(self, shutit):
""" + shutit.cfg['skeleton']['test_section'] + """
		return True

	def finalize(self, shutit):
""" + shutit.cfg['skeleton']['finalize_section'] + """
		return True

	def isinstalled(self, shutit):
""" + shutit.cfg['skeleton']['isinstalled_section'] + """
		return False

	def start(self, shutit):
""" + shutit.cfg['skeleton']['start_section'] + """
		return True

	def stop(self, shutit):
""" + shutit.cfg['skeleton']['stop_section'] + """
		return True

def module():
	return """ + skel_module_name + """(
		'""" + skel_domain + '''.''' + skel_module_name + """', """ + skel_domain_hash + """.0001,   
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['""" + skel_depends + """','shutit-library.virtualbox.virtualbox.virtualbox','tk.shutit.vagrant.vagrant.vagrant']
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
