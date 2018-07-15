"""
shutit.tk.setup (core ShutIt setup module)

Nomenclature:
    - Host machine:   Machine on which this script is run.
    - Target:         Environment to which we deploy (docker container or bash shell)
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

from __future__ import print_function
import shutit_global
import shutit_util
from shutit_module import ShutItModule
from shutit_sendspec import ShutItSendSpec
from shutit_pexpect import ShutItPexpectSession


class ShutItConnModule(ShutItModule):


	def __init__(self, *args, **kwargs):
		super(ShutItConnModule, self).__init__(*args, **kwargs)


	def setup_host_child(self, shutit):
		shutit.setup_host_child_environment()


	def setup_target_child(self, shutit, target_child, target_child_id='target_child',prefix='root'):
		shutit.setup_target_child_environment(target_child, target_child_id=target_child_id,prefix=prefix)


	def build(self, shutit):
		return True


class ConnDocker(ShutItConnModule):
	"""Connects ShutIt to docker daemon and starts the container.
	"""

	def is_installed(self, shutit):
		"""Always considered false for ShutIt setup.
		"""
		return False


	def destroy_container(self, shutit, host_shutit_session_name, container_shutit_session_name, container_id):
		host_child = shutit.get_shutit_pexpect_session_from_id(host_shutit_session_name).pexpect_child
		shutit.conn_docker_destroy_container(host_shutit_session_name, container_shutit_session_name, container_id)
		shutit.send(' command docker rm -f ' + container_id + ' && rm -f ' + shutit.build['cidfile'],shutit_pexpect_child=host_child,expect=shutit.expect_prompts['ORIGIN_ENV'])


	def start_container(self, shutit, shutit_session_name):
		return shutit.conn_docker_start_container(shutit_session_name)


	def build(self, shutit):
		"""Sets up the target ready for building.
		"""
		target_child = self.start_container(shutit, 'target_child')
		self.setup_host_child(shutit)
		# TODO: on the host child, check that the image running has bash as its cmd/entrypoint.
		self.setup_target_child(shutit, target_child)
		shutit.send('chmod -R 777 ' + shutit_global.shutit_global_object.shutit_state_dir + ' && mkdir -p ' + shutit_global.shutit_global_object.shutit_state_dir_build_db_dir + '/' + shutit_global.shutit_global_object.build_id, shutit_pexpect_child=target_child, echo=False)
		return True


	def finalize(self, shutit):
		"""Finalizes the target, exiting for us back to the original shell
		and performing any repository work required.
		"""
		# Finish with the target
		target_child_pexpect_session = shutit.get_shutit_pexpect_session_from_id('target_child')
		assert not target_child_pexpect_session.sendline(ShutItSendSpec(target_child_pexpect_session,'exit',ignore_background=True)), shutit_util.print_debug()
		host_child_pexpect_session = shutit.get_shutit_pexpect_session_from_id('host_child')
		host_child = host_child_pexpect_session.pexpect_child
		shutit.set_default_shutit_pexpect_session(host_child_pexpect_session)
		shutit.set_default_shutit_pexpect_session_expect(shutit.expect_prompts['ORIGIN_ENV'])
		shutit.do_repository_work(shutit.repository['name'], docker_executable=shutit.host['docker_executable'], password=shutit.host['password'])
		# Final exits
		host_child.sendline('rm -f ' + shutit.build['cidfile']) # Ignore response, just send.
		host_child.sendline('exit') # Exit raw bash. Ignore response, just send.
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
		shutit_pexpect_session = ShutItPexpectSession(shutit, 'target_child','/bin/bash')
		target_child = shutit_pexpect_session.pexpect_child
		shutit_pexpect_session.expect(shutit_global.shutit_global_object.base_prompt.strip(), timeout=10)
		self.setup_host_child(shutit)
		self.setup_target_child(shutit, target_child)
		return True


	def finalize(self, shutit):
		"""Finalizes the target, exiting for us back to the original shell
		and performing any repository work required.
		"""
		# Finish with the target
		target_child_pexpect_session = shutit.get_shutit_pexpect_session_from_id('target_child')
		assert not target_child_pexpect_session.sendline(ShutItSendSpec(target_child_pexpect_session,'exit',ignore_background=True)), shutit_util.print_debug()
		return True


def conn_module():
	"""Connects ShutIt to something
	"""
	return [
		ConnDocker('shutit.tk.conn_docker', -0.1, description='Connect ShutIt to docker'),
		ConnBash  ('shutit.tk.conn_bash',   -0.1, description='Connect ShutIt to a host via bash'),
	]


class setup(ShutItModule):


	def is_installed(self, shutit):
		"""Always considered false for ShutIt setup.
		"""
		return False


	def build(self, shutit):
		"""Initializes target ready for build and updating package management if in container.
		"""
		if shutit.build['delivery'] in ('docker','dockerfile'):
			if shutit.get_current_shutit_pexpect_session_environment().install_type == 'apt':
				shutit.add_to_bashrc('export DEBIAN_FRONTEND=noninteractive')
				if not shutit.command_available('lsb_release'):
					shutit.install('lsb-release')
				shutit.lsb_release()
			elif shutit.get_current_shutit_pexpect_session_environment().install_type == 'yum':
				# yum updates are so often "bad" that we let exit codes of 1 through.
				# TODO: make this more sophisticated
				shutit.send('yum update -y', timeout=9999, exit_values=['0', '1'])
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
