"""
shutit.tk.setup (core ShutIt setup module)

Nomenclature:
    - Host machine: Machine on which this pexpect script is run.
    - Target:       Environment on which we deploy (docker container, ssh, or bash shell)
    - Container:    Docker container created to run the modules on.

    - target_child    pexpect-spawned child created to build on target
    - host_child      pexpect spawned child living on the host machine
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
import os
import shutit_util
import time
import re
import subprocess
import os
from distutils import spawn


class ShutItConnModule(ShutItModule):

	def __init__(self, *args, **kwargs):
		super(ShutItConnModule, self).__init__(*args, **kwargs)

	def _setup_prompts(self, shutit, target_child):
		cfg = shutit.cfg
		# Now let's have a host_child
		shutit.log('Creating host child')
		shutit.log('Spawning host child')
		host_child = pexpect.spawn('/bin/bash')
		shutit.log('Spawning done')
		# Some pexpect settings
		shutit.pexpect_children['host_child'] = host_child
		shutit.pexpect_children['target_child'] = target_child
		shutit.log('Setting default expect')
		shutit.set_default_expect(cfg['expect_prompts']['base_prompt'])
		shutit.log('Setting default expect done')
		host_child.logfile_send = target_child.logfile_send = sys.stdout
		host_child.logfile_read = target_child.logfile_read = sys.stdout
		host_child.maxread = target_child.maxread = 2000
		host_child.searchwindowsize = target_child.searchwindowsize = 1024
		delay = cfg['build']['command_pause']
		host_child.delaybeforesend = target_child.delaybeforesend = delay
		# Set up prompts and let the user do things before the build
		# host child
		shutit.log('Setting default child')
		shutit.set_default_child(host_child)
		shutit.log('Setting default child done')
		shutit.log('Setting up default prompt on host child')
		shutit.log('Setting up prompt')
		# ORIGIN_ENV is a special case of the prompt maintained for performance reasons, don't change.
		shutit.setup_prompt('origin_prompt', prefix='ORIGIN_ENV')
		shutit.log('Setting up prompt done')
		# target child
		shutit.set_default_child(target_child)
		shutit.log('Setting up default prompt on target child')
		shutit.setup_prompt('root')
		shutit.login_stack_append('root')

	def _add_begin_build_info(self, shutit, command):
		cfg = shutit.cfg
		if cfg['build']['delivery'] in ('docker','dockerfile'):
			shutit.send('chmod -R 777 ' + cfg['build']['shutit_state_dir'])
			# TODO: debug this, fails on dockerfile builds, eg otto
			# Create the build directory and put the config in it.
			shutit.send(' mkdir -p ' + cfg['build']['build_db_dir'] + \
				 '/' + cfg['build']['build_id'])
			# Record the command we ran and the python env if in debug.
			if cfg['build']['debug']:
				shutit.send_file(cfg['build']['build_db_dir'] + '/' + \
				    cfg['build']['build_id'] + '/python_env.sh', \
				    str(sys.__dict__), log=False)
				shutit.send_file(cfg['build']['build_db_dir'] + '/' + \
				    cfg['build']['build_id'] + '/command.sh', \
				    ' '.join(command), log=False)
		shutit.pause_point('Anything you want to do now the ' +
		    'target is connected to?', level=2)

	def _add_end_build_info(self, shutit):
		cfg = shutit.cfg
		# Put build info into the target
		if cfg['build']['delivery'] in ('docker','dockerfile'):
			shutit.send(' mkdir -p ' + cfg['build']['build_db_dir'] + '/' + \
			    cfg['build']['build_id'])
			shutit.send_file(cfg['build']['build_db_dir'] + '/' + \
			    cfg['build']['build_id'] + '/build.log', \
			    shutit_util.get_commands(shutit))
			shutit.send_file(cfg['build']['build_db_dir'] + '/' + \
			    cfg['build']['build_id'] + '/build_commands.sh', \
			    shutit_util.get_commands(shutit))
			shutit.insert_text(cfg['build']['build_id'], \
			    cfg['build']['build_db_dir'] + '/builds')


class ConnDocker(ShutItConnModule):
	"""Connects ShutIt to docker daemon and starts the container.
	"""

	def is_installed(self, shutit):
		"""Always considered false for ShutIt setup.
		"""
		return False

	def _check_docker(self, shutit):
		"""Private function. Do some docker capability checking
		"""
		cfg = shutit.cfg

		# If we have sudo, kill any current sudo timeout. This is a bit of a
		# hammer and somewhat unfriendly, but tells us if we need a password.
		if spawn.find_executable('sudo') is not None:
			if subprocess.call(['sudo', '-k']) != 0:
				shutit.fail("Couldn't kill sudo timeout")

		# Check the executable is in the path. Not robust (as it could be sudo)
		# but deals with the common case of 'docker.io' being wrong.
		docker = cfg['host']['docker_executable'].split(' ')
		if spawn.find_executable(docker[0]) is None:
			msg = ('Didn\'t find %s on the path, what is the ' +\
			       'executable name (or full path) of docker?') % (docker[0],)
			cfg['host']['docker_executable'] = \
				shutit.prompt_cfg(msg, 'host', 'docker_executable')
			return False

		# First check we actually have docker and password (if needed) works
		check_cmd = docker + ['--version']
		str_cmd = ' '.join(check_cmd)
		cmd_timeout = 10
		needed_password = False
		fail_msg = ''
		try:
			shutit.log('Running: ' + str_cmd, force_stdout=True, prefix=False)
			child = pexpect.spawn(check_cmd[0], check_cmd[1:],
			timeout=cmd_timeout)
		except pexpect.ExceptionPexpect:
			msg = ('Failed to run %s (not sure why this has happened)...try ' +
			       'a different docker executable?') % (str_cmd,)
			cfg['host']['docker_executable'] = shutit.prompt_cfg(msg,
			    'host', 'docker_executable')
			return False
		try:
			if child.expect(['assword', pexpect.EOF]) == 0:
				needed_password = True
				if cfg['host']['password'] == '':
					msg = ('Running "%s" has prompted for a password, please ' +
					       'enter your host password') % (str_cmd,)
					cfg['host']['password'] = shutit.prompt_cfg(msg, 'host',
					    'password', ispass=True)
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
				       'setting seems to be wrong.\nPlease confirm your docker ' +
				       'executable, eg "sudo docker".')
				sec, name, ispass = 'host', 'docker_executable', False
			cfg[sec][name] = shutit.prompt_cfg(msg, sec, name, ispass=ispass)
			return False

		## Now check connectivity to the docker daemon
		#check_cmd = docker + ['info']
		#str_cmd = ' '.join(check_cmd)
		#child = pexpect.spawn(check_cmd[0], check_cmd[1:], timeout=cmd_timeout)
		#try:
		#	if child.expect(['assword', pexpect.EOF]) == 0:
		#		child.sendline(cfg['host']['password'])
		#		child.expect(pexpect.EOF)
		#except pexpect.ExceptionPexpect:
		#	shutit.fail('"' + str_cmd + '" did not complete in ' +
		#	str(cmd_timeout) + 's, ' +
		#	'is the docker daemon overloaded?')
		#child.close()
		#if child.exitstatus != 0:
		#	msg = ('"' + str_cmd + '" didn\'t return a 0 exit code, is the ' +
		#	       'docker daemon running? Do you need to set the ' +
		#	       'docker_executable config to use sudo? Please confirm the ' +
		#	       'docker executable.')
		#	cfg['host']['docker_executable'] = shutit.prompt_cfg(msg, 'host',
		#	    'docker_executable')

		return True

	def build(self, shutit):
		"""Sets up the target ready for building.
		"""
		# Uncomment for testing for "failure" cases.
		#sys.exit(1)
		while not self._check_docker(shutit):
			pass

		cfg = shutit.cfg
		docker = cfg['host']['docker_executable'].split(' ')

		# Always-required options
		if not os.path.exists(cfg['build']['shutit_state_dir'] + '/cidfiles'):
			os.makedirs(cfg['build']['shutit_state_dir'] + '/cidfiles')
		cfg['build']['cidfile'] = cfg['build']['shutit_state_dir'] + '/cidfiles/' + cfg['host']['username'] +\
		    '_cidfile_' + cfg['build']['build_id']
		cidfile_arg = '--cidfile=' + cfg['build']['cidfile']

		# Singly-specified options
		privileged_arg   = ''
		lxc_conf_arg     = ''
		name_arg         = ''
		hostname_arg     = ''
		artifact_arg       = ''
		rm_arg           = ''
		net_arg          = ''
		mount_docker_arg = ''
		shell_arg        = '/bin/bash'
		if cfg['build']['privileged']:
			privileged_arg = '--privileged=true'
		if cfg['build']['lxc_conf'] != '':
			lxc_conf_arg = '--lxc-conf=' + cfg['build']['lxc_conf']
		if cfg['target']['name'] != '':
			name_arg = '--name=' + cfg['target']['name']
		if cfg['target']['hostname'] != '':
			hostname_arg = '-h=' + cfg['target']['hostname']
		if cfg['host']['artifacts_dir'] != '':
			artifacts_arg = '-v=' + cfg['host']['artifacts_dir'] + ':/artifacts'
		if cfg['build']['net'] != '':
			net_arg        = '--net="' + cfg['build']['net'] + '"'
		if cfg['build']['mount_docker']:
			mount_docker_arg = '-v=/var/run/docker.sock:/var/run/docker.sock'
		# Incompatible with do_repository_work
		if cfg['target']['rm']:
			rm_arg = '--rm=true'
		if cfg['build']['base_image'] in ('alpine','busybox'):
			shell_arg = '/bin/ash'
		# Multiply-specified options
		port_args         = []
		dns_args          = []
		volume_args       = []
		volumes_from_args = []
		volumes_list      = cfg['target']['volumes'].strip().split()
		volumes_from_list = cfg['target']['volumes_from'].strip().split()
		ports_list        = cfg['target']['ports'].strip().split()
		dns_list          = cfg['host']['dns'].strip().split()
		for portmap in ports_list:
			port_args.append('-p=' + portmap)
		for dns in dns_list:
			dns_args.append('--dns=' + dns)
		for volume in volumes_list:
			volume_args.append('-v=' + volume)
		for volumes_from in volumes_from_list:
			volumes_from_args.append('--volumes-from=' + volumes_from)

		docker_command = docker + [
			arg for arg in [
				'run',
				cidfile_arg,
				privileged_arg,
				lxc_conf_arg,
				name_arg,
				hostname_arg,
				artifact_arg,
				rm_arg,
				net_arg,
				mount_docker_arg,
			] + volume_args + volumes_from_args + port_args + dns_args + [
				'-t',
				'-i',
				cfg['target']['docker_image'],
				shell_arg
			] if arg != ''
		]
		if cfg['build']['interactive'] >= 3:
			print('\n\nAbout to start container. ' +
			      'Ports mapped will be: ' + ', '.join(port_args) +
			      '\n\n[host]\nports:<value>\n\nconfig, building on the ' +
			      'configurable base image passed in in:\n\n    --image <image>\n' +
			      '\nor config:\n\n    [target]\n    docker_image:<image>)\n\n' +
			      'Base image in this case is:\n\n    ' + 
			      cfg['target']['docker_image'] +
			      '\n\n' + shutit_util.colour('32', '\n[Hit return to continue]'))
			shutit_util.util_raw_input(shutit=shutit)
		cfg['build']['docker_command'] = ' '.join(docker_command)
		shutit.log('\n\nCommand being run is:\n\n' + cfg['build']['docker_command'],
		force_stdout=True, prefix=False)
		shutit.log('\n\nThis may download the image, please be patient\n\n',
		force_stdout=True, prefix=False)
		target_child = pexpect.spawn(docker_command[0], docker_command[1:])
		expect = ['assword', cfg['expect_prompts']['base_prompt'].strip(), \
		          'Waiting', 'ulling', 'endpoint', 'Download']
		res = target_child.expect(expect, 9999)
		while True:
			shutit.log(target_child.before + target_child.after, prefix=False,
				force_stdout=True)
			if res == 0:
				shutit.log('...')
				res = shutit.send(cfg['host']['password'], \
				    child=target_child, expect=expect, timeout=9999, \
				    check_exit=False, fail_on_empty_before=False)
			elif res == 1:
				shutit.log('Prompt found, breaking out')
				break
			else:
				res = target_child.expect(expect, 9999)
				continue
		# Get the cid
		while True:
			try:
				cid = open(cfg['build']['cidfile']).read()
				break
			except Exception:
				sleep(1)
		if cid == '' or re.match('^[a-z0-9]+$', cid) == None:
			shutit.fail('Could not get container_id - quitting. ' +
			            'Check whether ' +
			            'other containers may be clashing on port allocation or name.' +
			            '\nYou might want to try running: sudo docker kill ' +
			            cfg['target']['name'] + '; sudo docker rm ' +
			            cfg['target']['name'] + '\nto resolve a name clash or: ' +
			            cfg['host']['docker_executable'] + ' ps -a | grep ' +
			            cfg['target']['ports'] + ' | awk \'{print $1}\' | ' +
			            'xargs ' + cfg['host']['docker_executable'] + ' kill\nto + '
			            'resolve a port clash\n')
		shutit.log('cid: ' + cid)
		cfg['target']['container_id'] = cid

		self._setup_prompts(shutit, target_child)
		self._add_begin_build_info(shutit, docker_command)

		return True

	def finalize(self, shutit):
		"""Finalizes the target, exiting for us back to the original shell
		and performing any repository work required.
		"""
		self._add_end_build_info(shutit)
		# Finish with the target
		shutit.pexpect_children['target_child'].sendline('exit')

		cfg = shutit.cfg
		host_child = shutit.pexpect_children['host_child']
		shutit.set_default_child(host_child)
		shutit.set_default_expect(cfg['expect_prompts']['origin_prompt'])
		# Tag and push etc
		shutit.pause_point('\nDoing final committing/tagging on the overall \
		                   target and creating the artifact.', \
		                   child=shutit.pexpect_children['host_child'], \
		                   print_input=False, level=3)
		shutit.do_repository_work(cfg['repository']['name'], \
		           docker_executable=cfg['host']['docker_executable'], \
		           password=cfg['host']['password'])
		# Final exits
		host_child.sendline('rm -f ' + cfg['build']['cidfile']) # Exit raw bash
		host_child.sendline('exit') # Exit raw bash
		return True


class ConnBash(ShutItConnModule):
	"""Connects ShutIt to a machine via bash.
	Assumes no docker daemon available for tagging and pushing.
	"""

	def is_installed(self, shutit):
		"""Always considered false for ShutIt setup.
		"""
		return False

	def get_config(self, shutit):
		return True

	def build(self, shutit):
		"""Sets up the machine ready for building.
		"""
		cfg = shutit.cfg
		command = '/bin/bash'
		target_child = pexpect.spawn(command)
		target_child.expect(cfg['expect_prompts']['base_prompt'].strip(), 10)
		self._setup_prompts(shutit, target_child)
		self._add_begin_build_info(shutit, command)
		return True

	def finalize(self, shutit):
		"""Finalizes the target, exiting for us back to the original shell
		and performing any repository work required.
		"""
		self._add_end_build_info(shutit)
		# Finish with the target
		shutit.pexpect_children['target_child'].sendline('exit')
		return True


class ConnSSH(ShutItConnModule):
	"""Connects ShutIt to a machine via ssh.
	Assumes no docker daemon available for tagging and pushing.
	"""

	def is_installed(self, shutit):
		"""Always considered false for ShutIt setup.
		"""
		return False

	def get_config(self, shutit):
		shutit.get_config(self.module_id, 'ssh_host', '')
		shutit.get_config(self.module_id, 'ssh_port', '')
		shutit.get_config(self.module_id, 'ssh_user', '')
		shutit.get_config(self.module_id, 'password', '')
		shutit.get_config(self.module_id, 'ssh_key', '')
		shutit.get_config(self.module_id, 'ssh_cmd', '')
		return True

	def build(self, shutit):
		"""Sets up the machine ready for building.
		"""
		cfg = shutit.cfg
		ssh_host = cfg[self.module_id]['ssh_host']
		ssh_port = cfg[self.module_id]['ssh_port']
		ssh_user = cfg[self.module_id]['ssh_user']
		ssh_pass = cfg[self.module_id]['password']
		ssh_key  = cfg[self.module_id]['ssh_key']
		ssh_cmd  = cfg[self.module_id]['ssh_cmd']
		opts = [
			'-t',
			'-o', 'UserKnownHostsFile=/dev/null',
			'-o', 'StrictHostKeyChecking=no'
		]
		if ssh_pass == '':
			opts += ['-o', 'PasswordAuthentication=no']
		if ssh_port != '':
			opts += ['-p', ssh_port]
		if ssh_key != '':
			opts += ['-i', ssh_key]
		host_arg = ssh_host
		if host_arg == '':
			shutit.fail('No host specified for sshing', throw_exception=False)
		if ssh_user != '':
			host_arg = ssh_user + '@' + host_arg
		cmd_arg = ssh_cmd
		if cmd_arg == '':
			cmd_arg = 'sudo su -s /bin/bash -'
		ssh_command = ['ssh'] + opts + [host_arg, cmd_arg]
		if cfg['build']['interactive'] >= 3:
			print('\n\nAbout to connect to host.' +
				'\n\n' + shutit_util.colour('32', '\n[Hit return to continue]'))
			shutit_util.util_raw_input(shutit=shutit)
		cfg['build']['ssh_command'] = ' '.join(ssh_command)
		shutit.log('\n\nCommand being run is:\n\n' + cfg['build']['ssh_command'],
			force_stdout=True, prefix=False)
		target_child = pexpect.spawn(ssh_command[0], ssh_command[1:])
		expect = ['assword', cfg['expect_prompts']['base_prompt'].strip()]
		res = target_child.expect(expect, 10)
		while True:
			shutit.log(target_child.before + target_child.after, prefix=False,
				force_stdout=True)
			if res == 0:
				shutit.log('...')
				res = shutit.send(ssh_pass,
				             child=target_child, expect=expect, timeout=10,
				             check_exit=False, fail_on_empty_before=False)
			elif res == 1:
				shutit.log('Prompt found, breaking out')
				break
		self._setup_prompts(shutit, target_child)
		self._add_begin_build_info(shutit, ssh_command)
		return True

	def finalize(self, shutit):
		"""Finalizes the target, exiting for us back to the original shell
		and performing any repository work required.
		"""
		self._add_end_build_info(shutit)
		# Finish with the target
		shutit.pexpect_children['target_child'].sendline('exit')
		# Finish with the host
		shutit.set_default_child(shutit.pexpect_children['host_child'])
		# Final exits
		host_child.sendline('exit') # Exit raw bash
		return True


def conn_module():
	"""Connects ShutIt to something
	"""
	return [
		ConnDocker(
			'shutit.tk.conn_docker', -0.1,
			description='Connect ShutIt to docker'
		),
		ConnSSH(
			'shutit.tk.conn_ssh', -0.1,
			description='Connect ShutIt to a host via ssh'
		),
		ConnBash(
			'shutit.tk.conn_bash', -0.1,
			description='Connect ShutIt to a host via bash'
		),
	]


class setup(ShutItModule):

	def is_installed(self, shutit):
		"""Always considered false for ShutIt setup.
		"""
		return False

	def build(self, shutit):
		"""Initializes target ready for build
		and updating package management if in container.
		"""
		cfg = shutit.cfg
		do_update = cfg['build']['do_update']
		if cfg['build']['delivery'] in ('docker','dockerfile'):
			if cfg['environment'][cfg['build']['current_environment_id']]['install_type'] == 'apt':
				shutit.add_to_bashrc('export DEBIAN_FRONTEND=noninteractive')
				if do_update and cfg['build']['delivery'] in ('docker','dockerfile'):
					shutit.send('apt-get update', timeout=9999, check_exit=False)
				if not shutit.command_available('lsb_release'):
					shutit.install('lsb-release')
				shutit.lsb_release()
				shutit.send('dpkg-divert --local --rename --add /sbin/initctl')
				shutit.send('ln -f -s /bin/true /sbin/initctl')
			elif cfg['environment'][cfg['build']['current_environment_id']]['install_type'] == 'yum':
				if do_update:
					# yum updates are so often "bad" that we let exit codes of 1
					# through. TODO: make this more sophisticated
					shutit.send('yum update -y', timeout=9999, exit_values=['0', '1'])
			shutit.pause_point('Anything you want to do to the target host ' + 
				'before the build starts?', level=2)
		return True

	def remove(self, shutit):
		"""Removes anything performed as part of build.
		"""
		return True

	def get_config(self, shutit):
		"""Gets the configured core pacakges, and whether to perform the package
		management update.
		"""
		shutit.get_config(self.module_id, 'do_update', True, boolean=True)
		return True


def module():
	return setup('shutit.tk.setup', 0.0, description='Core ShutIt setup')

