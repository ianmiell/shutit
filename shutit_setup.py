"""
shutit.tk.setup (core ShutIt setup module)

Nomenclature:
    - Host machine:   Machine on which this script is run.
    - Target:         Environment to which we deploy (docker container, ssh, or bash shell)
    - Container:      Docker container created to run the modules on.

    - target_child    pexpect-spawned child created to build on target
    - host_child      pexpect spawned child living on the host machine
"""

# The MIT License (MIT)
# 
# Copyright (C) 2014 OpenBet Limited
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# ITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from shutit_module import ShutItModule
import pexpect
import os
import shutit_util
import time
import re
import subprocess
from distutils import spawn
import logging
import shutit_pexpect
import string
import shutit_global


class ShutItConnModule(ShutItModule):

	def __init__(self, *args, **kwargs):
		super(ShutItConnModule, self).__init__(*args, **kwargs)

	def setup_host_child(self, shutit):
		cfg = shutit.cfg
		# Now let's have a host_child
		shutit.log('Spawning host child',level=logging.DEBUG)
		shutit_pexpect_session = shutit_pexpect.ShutItPexpectSession('host_child', '/bin/bash')
		# Set up prompts and let the user do things before the build
		shutit.set_default_shutit_pexpect_session(shutit_pexpect_session)
		shutit.set_default_shutit_pexpect_session_expect(cfg['expect_prompts']['base_prompt'])
		# ORIGIN_ENV is a special case of the prompt maintained for performance reasons, don't change.
		prefix = 'ORIGIN_ENV'
		shutit_pexpect_session.setup_prompt('origin_prompt', prefix=prefix)
		shutit_pexpect_session.login_stack_append(prefix)

	def setup_target_child(self, shutit, target_child):
		cfg = shutit.cfg
		# Some pexpect settings
		shutit_pexpect_session = shutit.get_shutit_pexpect_session_from_id('target_child')
		shutit_pexpect_session.pexpect_child = target_child
		shutit.set_default_shutit_pexpect_session_expect(cfg['expect_prompts']['base_prompt'])
		# target child
		shutit.set_default_shutit_pexpect_session(shutit_pexpect_session)
		prefix='root'
		shutit_pexpect_session.setup_prompt('root',prefix=prefix)
		shutit_pexpect_session.login_stack_append(prefix)


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
			msg = ('Didn\'t find %s on the path, what is the executable name (or full path) of docker?') % (docker[0],)
			cfg['host']['docker_executable'] = shutit.prompt_cfg(msg, 'host', 'docker_executable')
			return False

		# First check we actually have docker and password (if needed) works
		check_cmd = docker + ['--version']
		str_cmd = ' '.join(check_cmd)
		cmd_timeout = 10
		needed_password = False
		fail_msg = ''
		try:
			shutit.log('Running: ' + str_cmd,level=logging.DEBUG)
			shutit_pexpect_session = shutit_pexpect.ShutItPexpectSession('tmp_child', check_cmd[0], check_cmd[1:], timeout=cmd_timeout)
			child = shutit_pexpect_session.pexpect_child
		except pexpect.ExceptionPexpect:
			msg = ('Failed to run %s (not sure why this has happened)...try a different docker executable?') % (str_cmd,)
			cfg['host']['docker_executable'] = shutit.prompt_cfg(msg, 'host', 'docker_executable')
			return False
		try:
			if shutit.child_expect(child,'assword') == 0:
				needed_password = True
				if cfg['host']['password'] == '':
					msg = ('Running "%s" has prompted for a password, please enter your host password') % (str_cmd,)
					cfg['host']['password'] = shutit.prompt_cfg(msg, 'host', 'password', ispass=True)
			shutit_pexpect_session.sendline(cfg['host']['password'])
			shutit_pexpect_session.expect([])
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
				msg = (fail_msg + ', your host password or docker_executable config may be wrong (I will assume password).\nPlease confirm your host password.')
				sec, name, ispass = 'host', 'password', True
			else:
				msg = (fail_msg + ', your docker_executable setting seems to be wrong.\nPlease confirm your docker executable, eg "sudo docker".')
				sec, name, ispass = 'host', 'docker_executable', False
			cfg[sec][name] = shutit.prompt_cfg(msg, sec, name, ispass=ispass)
			return False
		return True


	def destroy_container(self, shutit, host_shutit_session_name, container_shutit_session_name, container_id, loglevel=logging.DEBUG):
		cfg = shutit.cfg
		# Close connection.
		shutit.get_shutit_pexpect_session_from_id(container_shutit_session_name).pexpect_child.close()
		host_child = shutit.get_shutit_pexpect_session_from_id(host_shutit_session_name).pexpect_child
		shutit.send(' docker rm -f ' + container_id + ' && rm -f ' + cfg['build']['cidfile'],shutit_pexpect_child=host_child,expect=cfg['expect_prompts']['origin_prompt'],loglevel=loglevel)


	def start_container(self, shutit, shutit_session_name, loglevel=logging.DEBUG):
		cfg = shutit.cfg
		docker = cfg['host']['docker_executable'].split(' ')
		# Always-required options
		if not os.path.exists(cfg['build']['shutit_state_dir'] + '/cidfiles'):
			os.makedirs(cfg['build']['shutit_state_dir'] + '/cidfiles')
		cfg['build']['cidfile'] = cfg['build']['shutit_state_dir'] + '/cidfiles/' + cfg['host']['username'] + '_cidfile_' + cfg['build']['build_id']
		cidfile_arg = '--cidfile=' + cfg['build']['cidfile']
		# Singly-specified options
		privileged_arg   = ''
		name_arg         = ''
		hostname_arg     = ''
		rm_arg           = ''
		net_arg          = ''
		mount_docker_arg = ''
		shell_arg        = '/bin/bash'
		if cfg['build']['privileged']:
			privileged_arg = '--privileged=true'
		if cfg['target']['name'] != '':
			name_arg = '--name=' + cfg['target']['name']
		if cfg['target']['hostname'] != '':
			hostname_arg = '-h=' + cfg['target']['hostname']
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
				name_arg,
				hostname_arg,
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
			print('\n\nAbout to start container. Ports mapped will be: ' + ', '.join(port_args) + '\n\n[host]\nports:<value>\n\nconfig, building on the configurable base image passed in in:\n\n    --image <image>\n\nor config:\n\n    [target]\n    docker_image:<image>)\n\nBase image in this case is:\n\n    ' + cfg['target']['docker_image'] + '\n\n' + shutit_util.colourise('32', '\n[Hit return to continue]'))
			shutit_util.util_raw_input()
		cfg['build']['docker_command'] = ' '.join(docker_command)
		shutit.log('Command being run is: ' + cfg['build']['docker_command'],level=logging.DEBUG)
		shutit.log('Downloading image, please be patient',level=logging.INFO)
		was_sent = string.join(docker_command,' ')
		shutit_pexpect_session = shutit_pexpect.ShutItPexpectSession(shutit_session_name, docker_command[0], docker_command[1:])
		target_child = shutit_pexpect_session.pexpect_child
		expect = ['assword', cfg['expect_prompts']['base_prompt'].strip(), 'Waiting', 'ulling', 'endpoint', 'Download','o such file']
		res = shutit_pexpect_session.expect(expect, timeout=9999)
		while True:
			try:
				shutit.log(target_child.before + target_child.after,level=loglevel)
			except:
				pass
			if res == 0:
				res = shutit.send(cfg['host']['password'], child=target_child, expect=expect, timeout=9999, check_exit=False, fail_on_empty_before=False, echo=False, loglevel=loglevel)
			elif res == 1:
				shutit.log('Prompt found, breaking out',level=logging.DEBUG)
				break
			elif res == 6:
				shutit.fail('Docker not installed. Is this a mac? If so, install Docker Toolbox - see https://docker.com')
				break
			else:
				res = shutit_pexpect_session.expect(expect, timeout=9999)
				continue
		# Did the pull work?
		if not shutit_pexpect_session.check_last_exit_values(was_sent):
			shutit_global.shutit.pause_point('Command:\n\n' + was_sent + '\n\nfailed, you have a shell to try rectifying the problem before continuing.')
		# Get the cid
		while True:
			try:
				cid = open(cfg['build']['cidfile']).read()
				break
			except Exception:
				time.sleep(1)
		if cid == '' or re.match('^[a-z0-9]+$', cid) == None:
			shutit.fail('Could not get container_id - quitting. Check whether other containers may be clashing on port allocation or name.\nYou might want to try running: sudo docker kill ' + cfg['target']['name'] + '; sudo docker rm ' + cfg['target']['name'] + '\nto resolve a name clash or: ' + cfg['host']['docker_executable'] + ' ps -a | grep ' + cfg['target']['ports'] + " | awk '{print $1}' | " + 'xargs ' + cfg['host']['docker_executable'] + ' kill\nto ' + 'resolve a port clash\n')
		shutit.log('cid: ' + cid,level=logging.DEBUG)
		cfg['target']['container_id'] = cid
		return target_child


	def build(self, shutit, loglevel=logging.DEBUG):
		"""Sets up the target ready for building.
		"""
		cfg = shutit.cfg
		target_child = self.start_container(shutit, 'target_child', loglevel=loglevel)
		self.setup_host_child(shutit)
		self.setup_target_child(shutit, target_child)
		shutit.send('chmod -R 777 ' + cfg['build']['shutit_state_dir'] + ' && mkdir -p ' + cfg['build']['build_db_dir'] + '/' + cfg['build']['build_id'], echo=False, loglevel=loglevel)
		return True


	def finalize(self, shutit):
		"""Finalizes the target, exiting for us back to the original shell
		and performing any repository work required.
		"""
		# Finish with the target
		
		shutit.get_shutit_pexpect_session_from_id('target_child').sendline('exit')

		cfg = shutit.cfg
		host_child = shutit.get_shutit_pexpect_session_from_id('host_child').pexpect_child
		shutit.set_default_shutit_pexpect_session(host_child)
		shutit.set_default_shutit_pexpect_session_expect(cfg['expect_prompts']['origin_prompt'])
		shutit.do_repository_work(cfg['repository']['name'], docker_executable=cfg['host']['docker_executable'], password=cfg['host']['password'])
		# Final exits
		host_child.sendline('rm -f ' + cfg['build']['cidfile']) # Exit raw bash
		host_child.sendline('exit') # Exit raw bash
		return True


	def get_config(self, shutit):
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
		shutit_pexpect_session = shutit_pexpect.ShutItPexpectSession('target_child','/bin/bash')
		target_child = shutit_pexpect_session.pexpect_child
		shutit_pexpect_session.expect(cfg['expect_prompts']['base_prompt'].strip(), timeout=10)
		self.setup_host_child(shutit)
		self.setup_target_child(shutit, target_child)
		return True

	def finalize(self, shutit):
		"""Finalizes the target, exiting for us back to the original shell
		and performing any repository work required.
		"""
		# Finish with the target
		shutit.get_shutit_pexpect_session_from_id('target_child').sendline('exit')
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

	def build(self, shutit, loglevel=logging.DEBUG):
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
			print('\n\nAbout to connect to host.' + '\n\n' + shutit_util.colourise('32', '\n[Hit return to continue]'))
			shutit_util.util_raw_input()
		cfg['build']['ssh_command'] = ' '.join(ssh_command)
		shutit.log('Command being run is: ' + cfg['build']['ssh_command'],level=logging.INFO)
		shutit_pexpect_session = shutit_pexpect.ShutItPexpectSession('target_child', ssh_command[0], ssh_command[1:])
		target_child = shutit_pexpect_session.pexpect_child
		expect = ['assword', cfg['expect_prompts']['base_prompt'].strip()]
		res = shutit.child_expect(target_child,expect, timeout=10)
		while True:
			shutit.log(target_child.before + target_child.after,level=logging.DEBUG)
			if res == 0:
				shutit.log('...',level=logging.DEBUG)
				res = shutit.send(ssh_pass, child=target_child, expect=expect, timeout=10, check_exit=False, fail_on_empty_before=False, echo=False, loglevel=loglevel)
			elif res == 1:
				shutit.log('Prompt found, breaking out',level=logging.DEBUG)
				break
		self.setup_host_child(shutit)
		self.setup_target_child(shutit, target_child)
		return True

	def finalize(self, shutit):
		"""Finalizes the target, exiting for us back to the original shell
		and performing any repository work required.
		"""
		# Finish with the target
		shutit.get_shutit_pexpect_session_from_id('target_child').sendline('exit')
		shutit.set_default_shutit_pexpect_session(shutit.get_shutit_pexpect_session_from_id('host_child'))
		# Final exits
		host_child.sendline('exit') # Exit raw bash
		return True


def conn_module():
	"""Connects ShutIt to something
	"""
	return [
		ConnDocker('shutit.tk.conn_docker', -0.1, description='Connect ShutIt to docker'),
		ConnSSH('shutit.tk.conn_ssh', -0.1, description='Connect ShutIt to a host via ssh'),
		ConnBash('shutit.tk.conn_bash', -0.1, description='Connect ShutIt to a host via bash'),
	]


class setup(ShutItModule):

	def is_installed(self, shutit):
		"""Always considered false for ShutIt setup.
		"""
		return False

	def build(self, shutit, loglevel=logging.DEBUG):
		"""Initializes target ready for build and updating package management if in container.
		"""
		cfg = shutit.cfg
		if cfg['build']['delivery'] in ('docker','dockerfile'):
			if cfg['environment'][cfg['build']['current_environment_id']]['install_type'] == 'apt':
				shutit.add_to_bashrc('export DEBIAN_FRONTEND=noninteractive')
				if not shutit.command_available('lsb_release'):
					shutit.install('lsb-release')
				shutit.lsb_release()
			elif cfg['environment'][cfg['build']['current_environment_id']]['install_type'] == 'yum':
				# yum updates are so often "bad" that we let exit codes of 1 through.
				# TODO: make this more sophisticated
				shutit.send('yum update -y', timeout=9999, exit_values=['0', '1'], loglevel=loglevel)
			shutit.pause_point('Anything you want to do to the target host ' + 'before the build starts?', level=2)
		return True

	def remove(self, shutit):
		"""Removes anything performed as part of build.
		"""
		return True

	def get_config(self, shutit):
		"""Gets the configured core pacakges, and whether to perform the package
		management update.
		"""
		return True



def module():
	return setup('shutit.tk.setup', 0.0, description='Core ShutIt setup')

#DATA[0]="   SSSSSSSSSSSSS hhhhh                          ttt      IIIIIII    ttt     "; DATA[1]=" SS:::::::::::::Sh:::h                        tt::t      I:::::I  tt::t     "; DATA[2]="S::::SSSSSS:::::Sh:::h                        t:::t      I:::::I  t:::t     "; DATA[3]="S::::S     SSSSSSh:::h                        t:::t      II:::II  t:::t     "; DATA[4]="S::::S           h::h hhhh     uuuu   uuuutttt:::ttttt    I::Itttt:::ttttt  "; DATA[5]="S::::S           h::hh::::hh   u::u   u::ut::::::::::t    I::I:::::::::::t  "; DATA[6]=" S:::SSSS        h::::::::::h  u::u   u::ut::::::::::t    I::I:::::::::::t  "; DATA[7]="  SS:::::SSSSS   h:::::hh::::h u::u   u::uttt:::::tttt    I::Ittt:::::tttt  "; DATA[8]="    SS::::::::S  h::::h  h::::hu::u   u::u   t:::t        I::I   t:::t      "; DATA[9]="      SSSSSS:::S h:::h    h:::hu::u   u::u   t:::t        I::I   t:::t      "; DATA[10]="           S::::Sh:::h    h:::hu::u   u::u   t:::t        I::I   t:::t      "; DATA[11]="           S::::Sh:::h    h:::hu:::uuu:::u   t:::t  tttt  I::I   t:::t  tttt"; DATA[12]="SSSSSS     S::::Sh:::h    h:::hu::::::::::uu t::::tt:::tII::::I  t::::tt:::t"; DATA[13]="S:::::SSSSSS::::Sh:::h    h:::h u::::::::::u tt::::::::tI:::::I  tt::::::::t"; DATA[14]="S:::::::::::::SS h:::h    h:::h  :::::::u::u   t::::::ttI:::::I    t::::::tt"; DATA[15]=" SSSSSSSSSSSSS   hhhhh    hhhhh  uuuuuuu uuu    tttttt  IIIIIII     tttttt  "; REALoOFFSEToX=0 ;REALoOFFSEToY=0; drawochar() { VoCOORDoX=$1; VoCOORDoY=$2; tput cup $((REALoOFFSEToY + VoCOORDoY)) $((REALoOFFSEToX + VoCOORDoX)); printf %c ${DATA[VoCOORDoY]:VoCOORDoX:1}; }; trap 'exit 1' INT TERM; trap 'tput setaf 9; tput cvvis; clear' EXIT; tput civis; clear; for ((b=0; b<1; b++)); do for ((c=1; c <= 1; c++)); do tput setaf $c; for ((x=0; x<${#DATA[0]}; x++)); do for ((y=0; y<=15; y++)); do drawochar $x $y; done; done; done; done;
