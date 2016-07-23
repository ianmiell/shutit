import os

def setup_vagrant_template(shutit, skel_path, skel_delivery, skel_domain, skel_module_name, skel_shutitfiles, skel_domain_hash, skel_depends):

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
	os.chmod(runsh_filename,0755)

	# destroy_vms.sh
	destroyvmssh_filename = skel_path + '/run.sh'
	destroyvmssh_file = open(destroyvmssh_filename,'w+')
	destroyvmssh_file.write('''
#!/bin/bash
if [[ $(command -v VBoxManage) != '' ]]
then
	while true 
	do
		VBoxManage list runningvms | grep {{ skeleton.module_name }} | awk '{print $1}' | xargs -IXXX VBoxManage controlvm 'XXX' poweroff && VBoxManage list vms | grep {{ skeleton.module_name }} | awk '{print $1}'  | xargs -IXXX VBoxManage unregistervm 'XXX' --delete
		# The xargs removes whitespace
		if [[ $(VBoxManage list vms | grep {{ skeleton.module_name }} | wc -l | xargs) -eq '0' ]]
		then
			break
		else
			ps -ef | grep virtualbox | grep {{ skeleton.module_name }} | awk '{print $2}' | xargs kill
			sleep 10
		fi
	done
fi''')
	destroyvmssh_file.close()
	os.chmod(destroyvmssh_filename,0755)

	# build.cnf file
	os.system('mkdir -p ' + skel_path + '/configs')
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
	os.chmod(build_cnf_filename,0400)

	os.system('git init')
	os.system('git submodule init')
	os.system('git submodule add https://github.com/ianmiell/shutit-library')

	# User message
	shutit.log('''# Run:
cd ''' + skel_path + ''' && ./run.sh
# to run.''',transient=True)




TODO: template
-rw-r--r--  1 imiell  staff  2436 23 Jul 16:58 template.py





import random
import string

{{ skeleton.header_section }}

	def build(self, shutit):
		vagrant_image = shutit.cfg[self.module_id]['vagrant_image']
		vagrant_provider = shutit.cfg[self.module_id]['vagrant_provider']
		gui = shutit.cfg[self.module_id]['gui']
		memory = shutit.cfg[self.module_id]['memory']
		module_name = '{{ skeleton.module_name }}_' + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
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
    vb.name = "{{ skeleton.module_name }}"
  end
end''')
		shutit.send('vagrant up --provider virtualbox',timeout=99999)
		shutit.login(command='vagrant ssh')
		shutit.login(command='sudo su -',password='vagrant')

{{ skeleton.build_section }}

		shutit.logout()
		shutit.logout()
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id,'vagrant_image',default='ubuntu/trusty64')
		shutit.get_config(self.module_id,'vagrant_provider',default='virtualbox')
		shutit.get_config(self.module_id,'gui',default='false')
		shutit.get_config(self.module_id,'memory',default='1024')
{{ skeleton.config_section }}
		return True

	def test(self, shutit):
{{ skeleton.test_section }}
		return True

	def finalize(self, shutit):
{{ skeleton.finalize_section }}
		return True

	def isinstalled(self, shutit):
{{ skeleton.isinstalled_section }}
		return False

	def start(self, shutit):
{{ skeleton.start_section }}
		return True

	def stop(self, shutit):
{{ skeleton.stop_section }}
		return True

def module():
	return {{ skeleton.module_name }}(
		'{{ skeleton.domain }}.{{ skeleton.module_name }}', {{ skeleton.domain_hash }}.0001,
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['{{ skeleton.depends }}','shutit-library.virtualbox.virtualbox.virtualbox','tk.shutit.vagrant.vagrant.vagrant']
	)









