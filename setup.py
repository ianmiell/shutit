#The MIT License (MIT)
#
#Copyright (C) 2014 OpenBet Limited
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of
#this software and associated documentation files (the "Software"), to deal in
#the Software without restriction, including without limitation the rights to
#use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#of the Software, and to permit persons to whom the Software is furnished to do
#so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#ITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.


from shutit_module import ShutItModule
import pexpect
import fdpexpect
import sys
import util
import time
import re
import shutit_global

import pty
import os

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

	def build(self,config_dict):
		# Kick off container within host machine
		port_args = []
		privileged_arg = ''
		lxc_conf_arg = ''
		ports_list = config_dict['container']['ports'].split()
		for portmap in ports_list:
			port_args.append('-p=' + portmap)
		if config_dict['build']['privileged']:
			privileged_arg = '-privileged'
		if config_dict['build']['lxc_conf'] != '':
			lxc_conf_arg = '-lxc-conf=' + config_dict['build']['lxc_conf']
		config_dict['build']['cidfile'] = '/tmp/' + config_dict['host']['username'] + '_cidfile_' + config_dict['build']['build_id']
		if config_dict['container']['name'] != '':
			name_arg = '-name=' + config_dict['container']['name']
		else:
			name_arg = ''
		docker_command = config_dict['host']['docker_executable'].split(' ') + [
			arg for arg in [
				'run',
				'-cidfile=' + config_dict['build']['cidfile'],
				privileged_arg,
				lxc_conf_arg,
				name_arg,
				'-v=' + config_dict['host']['resources_dir'] + ':/resources',
				'-h=' + config_dict['container']['hostname'],
				config_dict['host']['dns']
				] + port_args + [
				'-t',
				'-i',
				config_dict['container']['docker_image'],
				'/bin/bash'
			] if arg != ''
		]
		if config_dict['build']['tutorial']:
			util.pause_point(None,'\n\nAbout to start container. ' +
				'Ports mapped will be: ' + ', '.join(port_args) +
				' (from\n\n[host]\nports:<value>\n\nconfig, building on the ' +
				'configurable base image passed in in:\n\n\t--image <image>\n' +
				'\nor config:\n\n\t[container]\n\tdocker_image:<image>)\n\nBase' +
				'image in this case is:\n\n\t' + config_dict['container']['docker_image'] +
				'\n\n',print_input=False)
			util.pause_point(None,'Command being run is:\n\n' + ' '.join(docker_command),print_input=False)

		# Fork off a pty specially for docker. This protects us from modules
		# killing the bash process they're executing in and ending up running
		# on the host itself
		def docker_start(cmd_list):
			# http://stackoverflow.com/questions/373639/running-interactive-commands-in-paramiko
			# http://stackoverflow.com/questions/13041732/ssh-password-through-python-subprocess
			# http://stackoverflow.com/questions/1939107/python-libraries-for-ssh-handling
			# http://stackoverflow.com/questions/11272536/how-to-obtain-pseudo-terminal-master-file-descriptor-from-inside-ssh-session
			# http://stackoverflow.com/questions/4022600/python-pty-fork-how-does-it-work
			(child_pid, fd) = pty.fork()
			if child_pid == 0:
				# The first item of the list in the second argument is the name
				# of the new program
				try:
					os.execvp(cmd_list[0], cmd_list)
				except OSError:
					print "Failed to exec docker"
					sys.exit(1)
			else:
				return fd
		container_fd = docker_start(docker_command)
		container_child = fdpexpect.fdspawn(container_fd)
		# Long timeout in case we are downloading an image.
		if container_child.expect(['assword',config_dict['container']['hostname']],9999) == 0:
			util.send_and_expect(container_child,config_dict['host']['password'],config_dict['expect_prompts']['base_prompt'],timeout=9999,check_exit=False)

		# Get the cid
		time.sleep(1) # cidfile creation is sometimes slow...
		cid = open(config_dict['build']['cidfile']).read()
		if cid == '' or re.match('^[a-z0-9]+$', cid) == None:
			util.fail('Could not get container_id - quitting. Check whether other containers are running\nwhich clash eg on port allocation or name, preventing startup.\nYou might want to try running: sudo docker kill ' + config_dict['container']['name'] + '; sudo docker rm ' + config_dict['container']['name'])
		config_dict['container']['container_id'] = cid
		# Now let's have a host_child
		host_child = pexpect.spawn('/bin/bash')
		# Some pexpect settings
		util.set_pexpect_child('host_child',host_child)
		util.set_pexpect_child('container_child', container_child)
		host_child.logfile = container_child.logfile = sys.stdout
		host_child.maxread = container_child.maxread = 2000
		host_child.searchwindowsize = container_child.searchwindowsize = 1024
		# Set up prompts and let the user do things before the build
		util.setup_prompt(host_child,config_dict,'SHUTIT_PROMPT_REAL_USER#','real_user_prompt')
		util.pause_point(container_child,'Anything you want to do to the container before the build starts?')
		util.setup_prompt(container_child,config_dict,'SHUTIT_PROMPT_PRE_BUILD#','pre_build')
		util.get_distro_info(container_child,config_dict['expect_prompts']['pre_build'],config_dict)
		util.setup_prompt(container_child,config_dict,'SHUTIT_PROMPT_ROOT_PROMPT#','root_prompt')
		util.send_and_expect(container_child,'export DEBIAN_FRONTEND=noninteractive',config_dict['expect_prompts']['root_prompt'],check_exit=False)

		return True

	def start(self,config_dict):
		return True

	def stop(self,config_dict):
		return True

	def cleanup(self,config_dict):
		return True

	def remove(self,config_dict):
		container_child = util.get_pexpect_child('container_child')
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
		return True

	def test(self,config_dict):
		return True

	def get_config(self,config_dict):
		cp = config_dict['config_parser']
		return True

if not util.module_exists('com.ian.miell.setup'):
	obj = setup('com.ian.miell.setup',0.0)
	util.get_shutit_modules().add(obj)
	ShutItModule.register(setup)

