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
import sys
import util
import time
import re

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

class setup(ShutItModule):

	def is_installed(self,shutit):
		return False

	def build(self,shutit):
		config_dict = shutit.cfg
		# Kick off container within host machine

		# Always-required options
		config_dict['build']['cidfile'] = '/tmp/' + config_dict['host']['username'] + '_cidfile_' + config_dict['build']['build_id']
		cidfile_arg = '--cidfile=' + config_dict['build']['cidfile']

		# Singly specified options
		privileged_arg = ''
		lxc_conf_arg   = ''
		name_arg       = ''
		hostname_arg   = ''
		volume_arg     = ''
		rm_arg         = ''
		if config_dict['build']['privileged']:
			privileged_arg = '--privileged=true'
		if config_dict['build']['lxc_conf'] != '':
			lxc_conf_arg = '--lxc-conf=' + config_dict['build']['lxc_conf']
		if config_dict['container']['name'] != '':
			name_arg = '--name=' + config_dict['container']['name']
		if config_dict['container']['hostname'] != '':
			hostname_arg = '-h=' + config_dict['container']['hostname']
		if config_dict['host']['resources_dir'] != '':
			volume_arg = '-v=' + config_dict['host']['resources_dir'] + ':/resources'
		# Incompatible with do_repository_work
		if config_dict['container']['rm']:
			rm_arg = '--rm=true'

		# Multiply specified options
		port_args = []
		dns_args = []
		ports_list = config_dict['container']['ports'].strip().split()
		dns_list = config_dict['host']['dns'].strip().split()
		for portmap in ports_list:
			port_args.append('-p=' + portmap)
		for dns in dns_list:
			dns_args.append('-dns=' + dns)

		docker_command = config_dict['host']['docker_executable'].split(' ') + [
			arg for arg in [
				'run',
				cidfile_arg,
				privileged_arg,
				lxc_conf_arg,
				name_arg,
				hostname_arg,
				volume_arg,
				rm_arg,
				] + port_args + dns_args + [
				'-t',
				'-i',
				config_dict['container']['docker_image'],
				'/bin/bash'
			] if arg != ''
		]
		if config_dict['build']['tutorial']:
			shutit.pause_point('\n\nAbout to start container. ' +
				'Ports mapped will be: ' + ', '.join(port_args) +
				' (from\n\n[host]\nports:<value>\n\nconfig, building on the ' +
				'configurable base image passed in in:\n\n\t--image <image>\n' +
				'\nor config:\n\n\t[container]\n\tdocker_image:<image>)\n\nBase' +
				'image in this case is:\n\n\t' + config_dict['container']['docker_image'] +
				'\n\n',child=None,print_input=False)
		shutit.log('\n\nCommand being run is:\n\n' + ' '.join(docker_command),force_stdout=True,prefix=False)
		shutit.log('\n\nThis may download the image, please be patient\n\n',force_stdout=True,prefix=False)
		container_child = pexpect.spawn(docker_command[0], docker_command[1:])
		if container_child.expect(['assword',config_dict['expect_prompts']['base_prompt'].strip()],9999) == 0:
			shutit.send_and_expect(config_dict['host']['password'],child=container_child,
				expect=config_dict['expect_prompts']['base_prompt'],timeout=9999,check_exit=False)
		# Get the cid
		time.sleep(1) # cidfile creation is sometimes slow...
		cid = open(config_dict['build']['cidfile']).read()
		if cid == '' or re.match('^[a-z0-9]+$', cid) == None:
			util.fail('Could not get container_id - quitting. Check whether other containers are running\nwhich clash eg on port allocation or name, preventing startup.\nYou might want to try running: sudo docker kill ' + config_dict['container']['name'] + '; sudo docker rm ' + config_dict['container']['name'])
		config_dict['container']['container_id'] = cid
		# Now let's have a host_child
		host_child = pexpect.spawn('/bin/bash')
		# Some pexpect settings
		shutit.pexpect_children['host_child'] = host_child
		shutit.pexpect_children['container_child'] = container_child
		shutit.set_default_expect(config_dict['expect_prompts']['base_prompt'])
		host_child.logfile = container_child.logfile = sys.stdout
		host_child.maxread = container_child.maxread = 2000
		host_child.searchwindowsize = container_child.searchwindowsize = 1024
		# Set up prompts and let the user do things before the build
		# host child
		shutit.set_default_child(host_child)
		shutit.setup_prompt('SHUTIT_REAL_USER','real_user_prompt')
		shutit.set_default_expect(config_dict['expect_prompts']['real_user_prompt'])
		# container child
		shutit.set_default_child(container_child)
		shutit.setup_prompt('SHUTIT_PRE_BUILD','pre_build')
		shutit.set_default_expect(config_dict['expect_prompts']['pre_build'])
		shutit.get_distro_info()
		shutit.setup_prompt('SHUTIT_ROOT','root_prompt')
		shutit.set_default_expect(config_dict['expect_prompts']['root_prompt'])
		shutit.send_and_expect('export DEBIAN_FRONTEND=noninteractive',check_exit=False)
		shutit.pause_point('Anything you want to do to the container before the build starts?')
		return True

	def remove(self,shutit):
		config_dict = shutit.cfg
		if config_dict['container']['install_type'] == 'yum':
			shutit.remove('passwd')
		return True

	def finalize(self,shutit):
		config_dict = shutit.cfg
		# Finish with the container
		container_child = util.get_pexpect_child('container_child')
		# Put build info into the container
		shutit.send_and_expect('mkdir -p /root/shutit_build')
		logfile = '/root/shutit_build/shutit_buildlog_' + config_dict['build']['build_id']
		shutit.send_and_expect('touch ' + logfile)
		print_conf = 'cat > ' + logfile + """ << LOGFILEEND
""" + util.print_config(config_dict) + """
LOGFILEEND"""
		shutit.send_and_expect(print_conf,record_command=False)
		build_rep = """cat > """ + logfile + """ << BUILDREPEND
""" + util.build_report('') + """
BUILDREPEND"""
		shutit.send_and_expect(build_rep,record_command=False)
		container_child.sendline('exit') # Exit container
		return True

if not util.module_exists('shutit.tk.setup'):
	obj = setup('shutit.tk.setup',0.0,'Core ShutIt setup')
	util.get_shutit_modules().add(obj)
	ShutItModule.register(setup)

