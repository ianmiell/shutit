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
import subprocess
from distutils import spawn

class conn_docker(ShutItModule):
	"""Connects ShutIt to docker daemon and starts the container.
	"""

	def is_installed(self, shutit):
		"""Always considered false for ShutIt setup.
		"""
		return False

	def _check_docker(self, shutit):
		# Do some docker capability checking
		cfg = shutit.cfg
		cp = cfg['config_parser']

		# If we have sudo, kill any current sudo timeout. This is a bit of a
		# hammer and somewhat unfriendly, but tells us if we need a password.
		if spawn.find_executable('sudo') is not None:
			if subprocess.call(['sudo', '-k']) != 0:
				shutit.fail('Couldn\'t kill sudo timeout')

		# Check the executable is in the path. Not robust (as it could be sudo)
		# but deals with the common case of 'docker.io' being wrong.
		docker = cfg['host']['docker_executable'].split(' ')
		if spawn.find_executable(docker[0]) is None:
			msg = ('Didn\'t find %s on the path, what is the ' +
				'executable name (or full path) of docker?') % (docker[0],)
			cfg['host']['docker_executable'] = shutit.prompt_cfg(msg, 'host', 'docker_executable')
			return False

		# First check we actually have docker and password (if needed) works
		check_cmd = docker + ['--version']
		str_cmd = ' '.join(check_cmd)
		cmd_timeout = 10
		needed_password = False
		fail_msg = ''
		try:
			shutit.log('Running: ' + str_cmd, force_stdout=True, prefix=False)
			child = pexpect.spawn(check_cmd[0], check_cmd[1:], timeout=cmd_timeout)
		except pexpect.ExceptionPexpect:
			msg = ('Failed to run %s (not sure why this has happened)...try ' +
				'a different docker executable?') % (str_cmd,)
			cfg['host']['docker_executable'] = shutit.prompt_cfg(msg, 'host', 'docker_executable')
			return False
		try:
			if child.expect(['assword', pexpect.EOF]) == 0:
				needed_password = True
				if cfg['host']['password'] == '':
					msg = ('Running "%s" has prompted for a password, please ' +
						'enter your host password') % (str_cmd,)
					cfg['host']['password'] = shutit.prompt_cfg(msg, 'host', 'password', ispass=True)
				child.sendline(cfg['host']['password'])
				child.expect(pexpect.EOF)
		except pexpect.ExceptionPexpect:
			fail_msg = '"%s" did not complete in %ss' % (str_cmd, cmd_timeout)
		child.close()
		if child.exitstatus != 0:
			fail_msg = '"%s" didn\'t return a 0 exit code' % (str_cmd,)

		if fail_msg:
			# TODO: Ideally here we'd split up our checks so if it asked for a
			# password, kill the sudo timeout and run `sudo -l`. We then know if
			# the password is right or not so we know what we need to prompt
			# for. At the moment we assume the password if it was asked for.
			if needed_password:
				msg = (fail_msg + ', your host password or ' +
					'docker_executable config may be wrong (I will assume ' +
					'password).\nPlease confirm your host password.')
				sec, name, ispass = 'host', 'password', True
			else:
				msg = (fail_msg + ', your docker_executable ' +
					'setting seems to be wrong.\nPlease confirm your host ' +
					'password.')
				sec, name, ispass = 'host', 'docker_executable', False
			cfg[sec][name] = shutit.prompt_cfg(msg, sec, name, ispass=ispass)
			return False

		# Now check connectivity to the docker daemon
		check_cmd = docker + ['info']
		str_cmd = ' '.join(check_cmd)
		child = pexpect.spawn(check_cmd[0], check_cmd[1:], timeout=cmd_timeout)
		try:
			if child.expect(['assword', pexpect.EOF]) == 0:
				child.sendline(cfg['host']['password'])
				child.expect(pexpect.EOF)
		except pexpect.ExceptionPexpect:
			shutit.fail('"' + str_cmd + '" did not complete in ' + str(cmd_timeout) + 's, ' +
				'is the docker daemon overloaded?')
		child.close()
		if child.exitstatus != 0:
			msg = ('"' + str_cmd + '" didn\'t return a 0 exit code, is the ' +
				'docker daemon running? Do you need to set the ' +
				'docker_executable config to use sudo? Please confirm the ' +
				'docker executable.')
			cfg['host']['docker_executable'] = shutit.prompt_cfg(msg, 'host', 'docker_executable')

		return True

	def build(self, shutit):
		"""Sets up the container ready for building.
		"""
		# Uncomment for testing for "failure" cases.
		#sys.exit(1)
		while not self._check_docker(shutit):
			pass

		cfg = shutit.cfg
		docker = cfg['host']['docker_executable'].split(' ')

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
		net_arg        = ''
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
		if cfg['build']['net'] != '':
			net_arg        = '--net="' + cfg['build']['net'] + '"'
		# Incompatible with do_repository_work
		if cfg['container']['rm']:
			rm_arg = '--rm=true'

		# Multiply-specified options
		port_args  = []
		dns_args   = []
		ports_list = cfg['container']['ports'].strip().split()
		dns_list   = cfg['host']['dns'].strip().split()
		for portmap in ports_list:
			port_args.append('-p=' + portmap)
		for dns in dns_list:
			dns_args.append('--dns=' + dns)

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
				net_arg,
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
		shutit.log('\n\nCommand being run is:\n\n' + ' '.join(docker_command), force_stdout=True, prefix=False)
		shutit.log('\n\nThis may download the image, please be patient\n\n', force_stdout=True, prefix=False)

		container_child = pexpect.spawn(docker_command[0], docker_command[1:])
		expect = ['assword', cfg['expect_prompts']['base_prompt'].strip(),'Waiting','ulling','endpoint','Download']
		res = container_child.expect(expect,9999)
		while True:
			shutit.log(""">>>\n""" + container_child.before + container_child.after + """\n<<<""")
			if res == 0:
				shutit.log('...')
				res = shutit.send(cfg['host']['password'], child=container_child, expect=expect, timeout=9999, check_exit=False, fail_on_empty_before=False)
			elif res == 1:
				shutit.log('Prompt found, breaking out')
				break
			else:
				res = container_child.expect(expect,9999)
				continue
		# Get the cid
		time.sleep(5) # cidfile creation is sometimes slow...
		shutit.log('Slept')
		cid = open(cfg['build']['cidfile']).read()
		shutit.log('Opening file')
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
		shutit.log('cid: ' + cid)
		cfg['container']['container_id'] = cid
		# Now let's have a host_child
		shutit.log('Creating host child')
		shutit.log('Spawning host child')
		host_child = pexpect.spawn('/bin/bash')
		shutit.log('Spawning done')
		# Some pexpect settings
		shutit.pexpect_children['host_child'] = host_child
		shutit.pexpect_children['container_child'] = container_child
		shutit.log('Setting default expect')
		shutit.set_default_expect(cfg['expect_prompts']['base_prompt'])
		shutit.log('Setting default expect done')
		host_child.logfile_send = container_child.logfile_send = sys.stdout
		host_child.logfile_read = container_child.logfile_read = sys.stdout
		host_child.maxread = container_child.maxread = 2000
		host_child.searchwindowsize = container_child.searchwindowsize = 1024
		delay = cfg['build']['command_pause']
		host_child.delaybeforesend = container_child.delaybeforesend = delay
		# Set up prompts and let the user do things before the build
		# host child
		shutit.log('Setting default child')
		shutit.set_default_child(host_child)
		shutit.log('Setting default child done')
		shutit.log('Setting up default prompt on host child')
		shutit.log('Setting up prompt')
		shutit.setup_prompt('real_user_prompt', prefix='REAL_USER')
		shutit.log('Setting up prompt done')
		# container child
		shutit.set_default_child(container_child)
		shutit.log('Setting up default prompt on container child')
		shutit.setup_prompt('pre_build', prefix='PRE_BUILD')
		shutit.send('export HOME=/root')
		shutit.get_distro_info()
		shutit.setup_prompt('root_prompt', prefix='ROOT')
		# Create the build directory and put the config in it.
		shutit.send('mkdir -p ' + shutit.cfg ['build']['build_db_dir'] + '/' + shutit.cfg['build']['build_id'])
		# Record the command we ran and the python env.
		# TODO: record the image id we ran against - wait for "docker debug" command
		shutit.send_file(shutit.cfg['build']['build_db_dir'] + '/' + shutit.cfg['build']['build_id'] + '/python_env.sh', str(sys.__dict__), log=False)
		shutit.send_file(shutit.cfg['build']['build_db_dir'] + '/' + shutit.cfg['build']['build_id'] + '/docker_command.sh',' '.join(docker_command), log=False)
		shutit.pause_point('Anything you want to do now the container is connected to?', level=2)
		return True

	def finalize(self, shutit):
		"""Finalizes the container, exiting for us back to the original shell
		and performing any repository work required.
		"""
		# Put build info into the container
		shutit.send('mkdir -p ' + shutit.cfg ['build']['build_db_dir'] + '/' + shutit.cfg['build']['build_id'])
		shutit.send_file(shutit.cfg['build']['build_db_dir'] + '/' + shutit.cfg['build']['build_id'] + '/build.log', util.get_commands(shutit))
		shutit.send_file(shutit.cfg['build']['build_db_dir'] + '/' + shutit.cfg['build']['build_id'] + '/build_commands.sh', util.get_commands(shutit))
		shutit.add_line_to_file(shutit.cfg['build']['build_id'], shutit.cfg ['build']['build_db_dir'] + '/builds')
		# Finish with the container
		shutit.pexpect_children['container_child'].sendline('exit') # Exit container

		host_child = shutit.pexpect_children['host_child']
		shutit.set_default_child(host_child)
		shutit.set_default_expect(shutit.cfg['expect_prompts']['real_user_prompt'])
		# Tag and push etc
		shutit.pause_point('\nDoing final committing/tagging on the overall container and creating the artifact.',
			child=shutit.pexpect_children['host_child'], print_input=False, level=3)
		shutit.do_repository_work(shutit.cfg['repository']['name'], docker_executable=shutit.cfg['host']['docker_executable'], password=shutit.cfg['host']['password'])
		# Final exits
		host_child.sendline('exit') # Exit raw bash
		return True

def conn_module():
	return conn_docker(
		'shutit.tk.conn_docker', -0.1,
		description='Connect ShutIt to docker'
	)

class setup(ShutItModule):

	def is_installed(self, shutit):
		"""Always considered false for ShutIt setup.
		"""
		return False

	def build(self, shutit):
		"""Initializes container ready for build, setting password
		and updating package management.
		"""
		do_update = True
		# Seems to be broken
		#do_update = shutit.cfg[self.module_id]['do_update']
		if shutit.cfg['container']['install_type'] == 'apt':
			shutit.send('export DEBIAN_FRONTEND=noninteractive')
			if do_update:
				shutit.send('apt-get update', timeout=9999, check_exit=False)
			shutit.send('dpkg-divert --local --rename --add /sbin/initctl')
			shutit.send('ln -f -s /bin/true /sbin/initctl')
		elif shutit.cfg['container']['install_type'] == 'yum':
			if do_update:
				shutit.send('yum update -y', timeout=9999)
		shutit.set_password(shutit.cfg['container']['password'])
		shutit.pause_point('Anything you want to do to the container before the build starts?', level=2)
		return True

	def remove(self, shutit):
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
		shutit.get_config(self.module_id,'do_update','yes')
		return True

def module():
	return setup('shutit.tk.setup', 0.0, description='Core ShutIt setup')

