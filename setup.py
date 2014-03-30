#Copyright (C) 2014 OpenBet Limited
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


from shutit_module import ShutItModule
import pexpect
import fdpexpect
import pexcpssh
import subprocess
import sys
import util
import time
import re
import shutit_global
import random

# Nomenclature:
#
# Host machine
#   Machine on which this pexpect script is run.
# Container
#   Container created to run the modules on.
#
# container_child - pexpect-spawned child created to create the container
# host_child      - pexpect spawned child living on the host container

# Possibly useful for time/date requirements
#[root@localhost ~]# rm /etc/localtime; ln -s /usr/share/zoneinfo/Europe/London /etc/localtime
#[root@localhost ~]# date --set="27 JUN 2013 23:05:00"

class setup(ShutItModule):

	def check_ready(self,config_dict):
		# I am born ready
		return True

	def is_installed(self,config_dict):
		return False

	def bootstrap(self,config_dict):
		control = pexpect.spawn('/bin/bash')
		control.logfile          = sys.stdout
		control.maxread          = 2000
		control.searchwindowsize = 1024
		# Kick off container within host machine
		port_arg = ''
		privileged_arg = ''
		lxc_conf_arg = ''
		ports_list = config_dict['container']['ports'].split()
		for portmap in ports_list:
			port_arg = port_arg + '-p ' + portmap
		if config_dict['build']['privileged']:
			privileged_arg = '-privileged'
		if config_dict['build']['lxc_conf'] != '':
			lxc_conf_arg = '-lxc-conf=' + config_dict['build']['lxc_conf']
		config_dict['build']['cidfile'] = '/tmp/' + config_dict['host']['username'] + '_cidfile_' + config_dict['build']['build_id']
		if config_dict['container']['name'] != '':
			name_arg = '-name ' + config_dict['container']['name']
		else:
			name_arg = ''
		docker_command = (config_dict['host']['docker_executable'] +
				' run -cidfile=' + config_dict['build']['cidfile'] +
				' ' + privileged_arg +
				' ' + lxc_conf_arg + 
				' ' + name_arg +
				' -v=' + config_dict['host']['resources_dir'] + ':/resources' +
				' -h=' + config_dict['container']['hostname'] +
				' ' + config_dict['host']['dns'] +
				' ' + port_arg +
				' -t -i ' + config_dict['container']['docker_image'] +
				' /bin/bash')
		if config_dict['build']['tutorial']:
			util.pause_point(None,'\n\nAbout to start container. Ports mapped will be: ' + port_arg + ' (from\n\n[host]\nports:<value>\n\nconfig, building on the configurable base image passed in in:\n\n\t--image <image>\n\nor config:\n\n\t[container]\n\tdocker_image:<image>)\n\nBase image in this case is:\n\n\t' + config_dict['container']['docker_image'] + '\n\n',print_input=False)
			util.pause_point(None,'Command being run is:\n\n' + docker_command,print_input=False)
		if util.send_and_expect(control,docker_command,['assword',config_dict['expect_prompts']['base_prompt']],check_exit=False,timeout=9999) == 0:
			util.send_and_expect(control,config_dict['host']['password'],config_dict['expect_prompts']['base_prompt'],timeout=9999,check_exit=False)
		# This line appears to be redundant.
		#control.expect(config_dict['expect_prompts']['base_prompt'],timeout=9999)
		time.sleep(1) # cidfile creation is sometimes slow...
		cid = open(config_dict['build']['cidfile']).read()
		if cid == '' or re.match('^[a-z0-9]+$', cid) == None:
			util.fail('Could not get container_id - quitting. Check whether other containers are running\nwhich clash eg on port allocation or name, preventing startup.')
		config_dict['container']['container_id'] = cid
		util.pause_point(control,'Anything you want to do to the container before the build starts?')
		util.setup_prompt(control,config_dict,'SHUTIT_PROMPT_PRE_SSH#','pre_ssh')
		util.get_distro_info(control,config_dict['expect_prompts']['pre_ssh'],config_dict)
		self.setup_ssh_server(config_dict,control,config_dict['expect_prompts']['pre_ssh'])
		# Log into an ssh session to ensure that we don't mess up the host with accidental root access.
		def mk_sess(port, password):
			ssh_fd = pexcpssh.ssh_start('localhost', port, 'root')
			util.add_ssh_session(ssh_fd)
			expect_child = fdpexpect.fdspawn(ssh_fd)
			expect_child.expect('assword:')
			expect_child.sendline(password)
			return expect_child
		# Now let's have a host_child
		host_child = pexpect.spawn('/bin/bash')
		container_child = mk_sess(config_dict['container']['ports'].split()[0].split(':')[0], config_dict['container']['password'])
		util.set_pexpect_child('control',control)
		util.set_pexpect_child('host_child',host_child)
		util.set_pexpect_child('container_child', container_child)
		host_child.logfile = container_child.logfile = sys.stdout
		host_child.maxread = container_child.maxread = 2000
		host_child.searchwindowsize = container_child.searchwindowsize = 1024
		util.setup_prompt(host_child,config_dict,'SHUTIT_PROMPT_REAL_USER#','real_user_prompt')
		# container_child
		container_child.expect(config_dict['expect_prompts']['base_prompt'])
		util.setup_prompt(container_child,config_dict,'SHUTIT_PROMPT_ROOT_PROMPT#','root_prompt')
		util.send_and_expect(container_child,'export DEBIAN_FRONTEND=noninteractive',config_dict['expect_prompts']['root_prompt'],check_exit=False)



	def build(self,config_dict):
		self.bootstrap(config_dict)
		host_child = util.get_pexpect_child('host_child')
		container_child = util.get_pexpect_child('container_child')
		# Get the port, then ssh in.
		res = util.send_and_expect(host_child,config_dict['host']['docker_executable'] + ' port ' + config_dict['container']['container_id'] + ' 22',[config_dict['expect_prompts']['real_user_prompt'],'assword'],check_exit=False)
		if res == 1:
			util.send_and_expect(host_child,config_dict['host']['password'],config_dict['expect_prompts']['real_user_prompt'])
		return True

	def start(self,config_dict):
		container_child = util.get_pexpect_child('container_child')
		util.send_and_expect(container_child,'/root/start_ssh.sh',config_dict['expect_prompts']['root_prompt'])
		return True

	def stop(self,config_dict):
		container_child = util.get_pexpect_child('container_child')
		util.send_and_expect(container_child,'/root/stop_ssh.sh',config_dict['expect_prompts']['root_prompt'])
		return True

	def cleanup(self,config_dict):
		return True

	def remove(self,config_dict):
		container_child = util.get_pexpect_child('container_child')
		util.remove(container_child,config_dict,'openssh-server',config_dict['expect_prompts']['root_prompt'])
		if config_dict['container']['install_type'] == 'yum':
			util.remove(container_child,config_dict,'passwd',config_dict['expect_prompts']['root_prompt'])
		return True

	def finalize(self,config_dict):
		# Finish with the container
		container_child = util.get_pexpect_child('container_child')
		# Put build info into the container
		util.send_and_expect(container_child,'mkdir -p /root/shutit_build',config_dict['expect_prompts']['root_prompt'])
		logfile = '/root/shutit_build/shutit_buildlog_' + shutit_global.config_dict['build']['build_id']
		util.send_and_expect(container_child,'touch ' + logfile,config_dict['expect_prompts']['root_prompt'])
		print_conf = 'cat > ' + logfile + """ << LOGFILEEND
""" + util.print_config(config_dict) + """
LOGFILEEND"""
		util.send_and_expect(container_child,print_conf,config_dict['expect_prompts']['root_prompt'],record_command=False)
		build_rep = """cat > """ + logfile + """ << BUILDREPEND
""" + util.build_report('') + """
BUILDREPEND"""
		util.send_and_expect(container_child,build_rep,config_dict['expect_prompts']['root_prompt'],record_command=False)
		container_child.sendline('exit') # Exit container
		control = util.get_pexpect_child('control')
		util.send_and_expect(control,'/root/stop_ssh.sh',config_dict['expect_prompts']['base_prompt'],check_exit=False)
		control.sendline('exit')
		return True

	def test(self,config_dict):
		return True

	def get_config(self,config_dict):
		cp = config_dict['config_parser']
		return True

	# Install ssh on the container
	def setup_ssh_server(self,config_dict,child,expect):
		util.install(child,config_dict,'openssh-server',expect,options='--force-yes -y')
		util.send_and_expect(child,'mkdir -p /var/run/sshd',expect)
		util.send_and_expect(child,'chmod 700 /var/run/sshd',expect)
		## To get sshd to work, we need to create a privilege separation directory.
		## see http://docs.docker.io/en/latest/examples/running_ssh_service/
		util.add_line_to_file(child,'mkdir -p /var/run/sshd','/root/start_ssh.sh',expect)
		util.add_line_to_file(child,'chmod 700 /var/run/sshd','/root/start_ssh.sh',expect)
		if config_dict['container']['install_type'] == 'apt':
			util.add_line_to_file(child,'start-stop-daemon --start --quiet --oknodo --pidfile /var/run/sshd.pid --exec /usr/sbin/sshd','/root/start_ssh.sh',expect)
			util.add_line_to_file(child,'start-stop-daemon --stop --quiet --oknodo --pidfile /var/run/sshd.pid','/root/stop_ssh.sh',expect)
		elif config_dict['container']['install_type'] == 'yum' and config_dict['container']['distro'] != 'fedora':
			util.add_line_to_file(child,'/etc/init.d/sshd start','/root/start_ssh.sh',expect)
			util.add_line_to_file(child,'/etc/init.d/sshd stop','/root/stop_ssh.sh',expect)
		elif config_dict['container']['distro'] == 'fedora':
			util.add_line_to_file(child,'ssh-keygen -A','/root/start_ssh.sh',expect)
			util.add_line_to_file(child,'/usr/sbin/sshd','/root/start_ssh.sh',expect)
			util.add_line_to_file(child,"""ps -ef | grep sshd | awk '{print $1}' | sed 's/\(.*\)/kill \\1/' | sh""",'/root/stop_ssh.sh',expect)
		else:
			util.fail('install_type not covered: ' + config_dict['container']['install_type'])
		util.send_and_expect(child,'chmod +x /root/start_ssh.sh',expect)
		util.send_and_expect(child,'chmod +x /root/stop_ssh.sh',expect)
		util.add_line_to_file(child,'export HOME=/root','/root/.bashrc',expect)
		# ... and the others point to it.
		util.add_line_to_file(child,'. /root/.bashrc','/root/.bash_profile.sh',expect)
		util.add_line_to_file(child,'. /root/.bashrc','/.bashrc',expect)
		util.add_line_to_file(child,'. /root/.bashrc','/.bash_profile',expect)
		# Start ssh
		util.send_and_expect(child,'/root/start_ssh.sh',expect,check_exit=False)
		time.sleep(5)

if not util.module_exists('com.ian.miell.setup'):
	obj = setup('com.ian.miell.setup',0.0)
	util.get_shutit_modules().add(obj)
	ShutItModule.register(setup)

