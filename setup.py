"""
Nomenclature:

Host machine
  Machine on which this pexpect script is run.
Container
  Container created to run the modules on.

container_child - pexpect-spawned child created to create the container
host_child      - pexpect spawned child living on the host container
"""

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
import json


class conn_docker(ShutItModule):
	"""Connects ShutIt to docker daemon and starts the container.
	"""

	def is_installed(self,shutit):
		"""Always considered false for ShutIt setup.
		"""
		return False

	def build(self,shutit):
		"""Sets up the container ready for building.
		"""
		cfg = shutit.cfg

		docker = cfg['host']['docker_executable'].split(' ')
		password = cfg['host']['password']

		# Do some docker capability checking

		# First check we actually have docker and password (if needed) works
		check_cmd = docker + ['--version']
		str_cmd = ' '.join(check_cmd)
		try:
			shutit.log('Running: ' + str_cmd,force_stdout=True,prefix=False)
			child = pexpect.spawn(check_cmd[0], check_cmd[1:], timeout=1)
		except pexpect.ExceptionPexpect:
			shutit.fail('Cannot run check on "' + str_cmd + '", is the docker ' +
				'command on your path?')
		try:
			if child.expect(['assword', pexpect.EOF]) == 0:
				child.sendline(password)
				child.expect(pexpect.EOF)
		except pexpect.ExceptionPexpect:
			shutit.fail('"' + str_cmd + '" did not complete in 1s, ' +
				'\nIs your host password config correct?\nIs your docker_executable setting correct?')
		child.close()
		if child.exitstatus != 0:
			shutit.fail('"' + str_cmd + '" didn\'t return a 0 exit code')
		# Now check connectivity to the docker daemon
		check_cmd = docker + ['info']
		str_cmd = ' '.join(check_cmd)
		child = pexpect.spawn(check_cmd[0], check_cmd[1:], timeout=1)
		try:
			if child.expect(['assword', pexpect.EOF]) == 0:
				child.sendline(password)
				child.expect(pexpect.EOF)
		except pexpect.ExceptionPexpect:
			shutit.fail('"' + str_cmd + '" did not complete in 1s, ' +
				'is the docker daemon overloaded?')
		child.close()
		if child.exitstatus != 0:
			shutit.fail(str_cmd + ' didn\'t return a 0 exit code, ' +
				'is the docker daemon running?')

		# Onto the actual execution

		# Always-required options
		cfg['build']['cidfile'] = '/tmp/' + cfg['host']['username'] + '_cidfile_' + cfg['build']['build_id']
		cidfile_arg = '--cidfile=' + cfg['build']['cidfile']

		# Singly-specified options
		privileged_arg = ''
		lxc_conf_arg   = ''
		name_arg       = ''
		hostname_arg   = ''
		volume_arg     = ''
		rm_arg         = ''
		if cfg['build']['privileged']:
			privileged_arg = '--privileged=true'
		else:
			# TODO: put in to ensure serve always works.
			# Need better solution in place, eg refresh builder when build needs privileged
			privileged_arg = '--privileged=true'
		if cfg['build']['lxc_conf'] != '':
			lxc_conf_arg = '--lxc-conf=' + cfg['build']['lxc_conf']
		if cfg['container']['name'] != '':
			name_arg = '--name=' + cfg['container']['name']
		if cfg['container']['hostname'] != '':
			hostname_arg = '-h=' + cfg['container']['hostname']
		if cfg['host']['resources_dir'] != '':
			volume_arg = '-v=' + cfg['host']['resources_dir'] + ':/resources'
		# Incompatible with do_repository_work
		if cfg['container']['rm']:
			rm_arg = '--rm=true'

		# Multiply-specified options
		port_args = []
		dns_args = []
		ports_list = cfg['container']['ports'].strip().split()
		dns_list = cfg['host']['dns'].strip().split()
		for portmap in ports_list:
			port_args.append('-p=' + portmap)
		for dns in dns_list:
			dns_args.append('-dns=' + dns)

		docker_command = docker + [
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
				cfg['container']['docker_image'],
				'/bin/bash'
			] if arg != ''
		]
		if cfg['build']['interactive'] >= 2:
			print('\n\nAbout to start container. ' +
				'Ports mapped will be: ' + ', '.join(port_args) +
				' (from\n\n[host]\nports:<value>\n\nconfig, building on the ' +
				'configurable base image passed in in:\n\n\t--image <image>\n' +
				'\nor config:\n\n\t[container]\n\tdocker_image:<image>)\n\nBase ' +
				'image in this case is:\n\n\t' + cfg['container']['docker_image'] +
				'\n\n' + util.colour('31','[Hit return to continue]'))
			raw_input('')
		shutit.log('\n\nCommand being run is:\n\n' + ' '.join(docker_command),force_stdout=True,prefix=False)
		shutit.log('\n\nThis may download the image, please be patient\n\n',force_stdout=True,prefix=False)
		container_child = pexpect.spawn(docker_command[0], docker_command[1:])
		if container_child.expect(['assword',cfg['expect_prompts']['base_prompt'].strip()],9999) == 0:
			shutit.send_and_expect(cfg['host']['password'],child=container_child,
				expect=cfg['expect_prompts']['base_prompt'],timeout=9999,check_exit=False)
		# Get the cid
		time.sleep(1) # cidfile creation is sometimes slow...
		cid = open(cfg['build']['cidfile']).read()
		if cid == '' or re.match('^[a-z0-9]+$', cid) == None:
			shutit.fail('Could not get container_id - quitting. Check whether ' +
				'other containers may be clashing on port allocation or name.' +
				'\nYou might want to try running: sudo docker kill ' +
				cfg['container']['name'] + '; sudo docker rm ' +
				cfg['container']['name'] + '\nto resolve a name clash or: ' +
				cfg['host']['docker_executable'] + ' ps -a | grep ' +
				cfg['container']['ports'] + ' | awk \'{print $1}\' | ' +
				'xargs ' + cfg['host']['docker_executable'] + ' kill\nto + '
				'resolve a port clash\n')
		cfg['container']['container_id'] = cid
		# Now let's have a host_child
		shutit.log('Creating host child')
		host_child = pexpect.spawn('/bin/bash')
		# Some pexpect settings
		shutit.pexpect_children['host_child'] = host_child
		shutit.pexpect_children['container_child'] = container_child
		shutit.set_default_expect(cfg['expect_prompts']['base_prompt'])
		host_child.logfile = container_child.logfile = sys.stdout
		host_child.maxread = container_child.maxread = 2000
		host_child.searchwindowsize = container_child.searchwindowsize = 1024
		delay = cfg['build']['command_pause']
		host_child.delaybeforesend = container_child.delaybeforesend = delay
		# Set up prompts and let the user do things before the build
		# host child
		shutit.set_default_child(host_child)
		shutit.log('Setting up default prompt on host child')
		shutit.setup_prompt('real_user_prompt','REAL_USER')
		# container child
		shutit.set_default_child(container_child)
		shutit.log('Setting up default prompt on container child')
		shutit.setup_prompt('pre_build', 'PRE_BUILD')
		shutit.get_distro_info()
		shutit.setup_prompt('root_prompt', 'ROOT')
		shutit.pause_point('Anything you want to do now the container is connected to?')
		return True

	def finalize(self,shutit):
		"""Finalizes the container, exiting for us back to the original shell
		and performing any repository work required.
		"""
		cfg = shutit.cfg
		# Put build info into the container
		shutit.send_and_expect('mkdir -p /root/shutit_build')
		logfile = cfg['build']['container_build_log']
		shutit.send_and_expect('touch ' + logfile)
		print_conf = 'cat > ' + logfile + """ << LOGFILEEND
""" + util.print_config(cfg) + """
LOGFILEEND"""
		shutit.send_and_expect(print_conf,record_command=False)
		build_rep = """cat > """ + logfile + """ << BUILDREPEND
""" + util.build_report('') + """
BUILDREPEND"""
		# Do we need this check_exit=False?
		shutit.send_and_expect(build_rep,record_command=False,check_exit=False)
		# Finish with the container
		shutit.pexpect_children['container_child'].sendline('exit') # Exit container

		host_child = shutit.pexpect_children['host_child']
		shutit.set_default_child(host_child)
		shutit.set_default_expect(cfg['expect_prompts']['real_user_prompt'])
		# Tag and push etc
		if cfg['build']['interactive'] >= 2:
			shutit.pause_point('\nDoing final committing/tagging on the overall container and creating the artifact.',
				child=shutit.pexpect_children['host_child'],print_input=False)
		shutit.do_repository_work(cfg['repository']['name'],docker_executable=cfg['host']['docker_executable'],password=cfg['host']['password'])
		# Final exits
		host_child.sendline('exit') # Exit raw bash
		time.sleep(0.3)
		return True

def conn_module():
	return conn_docker(
		'shutit.tk.conn_docker', -0.1,
		description='Connect ShutIt to docker'
	)

class setup(ShutItModule):

	def is_installed(self,shutit):
		"""Always considered false for ShutIt setup.
		"""
		return False

	def build(self,shutit):
		"""Initializes container ready for build, setting password
		and updating package management.
		"""
		mod_id = 'shutit.tk.setup'
		packages = shutit.cfg[mod_id]['packages']
		do_update = shutit.cfg[mod_id]['do_update']
		if shutit.cfg['container']['install_type'] == 'apt':
			shutit.send_and_expect('export DEBIAN_FRONTEND=noninteractive')
			if do_update:
				shutit.send_and_expect('apt-get update',timeout=9999,check_exit=False)
			shutit.send_and_expect('dpkg-divert --local --rename --add /sbin/initctl')
			shutit.send_and_expect('ln -f -s /bin/true /sbin/initctl')
			for p in packages:
				shutit.install(p)
		elif shutit.cfg['container']['install_type'] == 'yum':
			for p in packages:
				shutit.install(p)
			if do_update:
				shutit.send_and_expect('yum update -y',timeout=9999)
		shutit.set_password(shutit.cfg['container']['password'])
		shutit.pause_point('Anything you want to do to the container before the build starts?')
		return True

	def remove(self,shutit):
		"""Removes anything performed as part of build.
		"""
		cfg = shutit.cfg
		if cfg['container']['install_type'] == 'yum':
			shutit.remove('passwd')
		return True

	def get_config(self, shutit):
		"""Gets the configured core pacakges, and whether to perform the package
		management update.
		"""
		cp = shutit.cfg['config_parser']
		shutit.cfg[self.module_id]['packages']  = json.loads(cp.get(self.module_id,'packages'))
		shutit.cfg[self.module_id]['do_update'] = cp.getboolean(self.module_id,'do_update')
		return True

def module():
	return setup('shutit.tk.setup', 0.0, description='Core ShutIt setup')

