"""Contains all the core ShutIt methods and functionality, and public interface
off to internal objects such as shutit_pexpect.
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

import sys
import os
import socket
import time
import getpass
import datetime
import logging
import fcntl
import termios
import signal
import struct
from distutils.dir_util import mkpath
from shutit_class import ShutIt, ShutItInit
import shutit_util


class ShutItGlobal(object):
	"""Single object to store all the separate ShutIt sessions.
	"""

	only_one = None
	report_final_messages = ''
	def __init__(self):
		"""Constructor.
		"""
		self.shutit_objects = []
		# Primitive singleton enforcer.
		assert self.only_one is None
		self.only_one         = True

		self.secret_words_set = set()
		self.logfile          = None
		self.loglevel         = None
		self.signal_id        = None
		self.username         = os.environ.get('LOGNAME', '')
		# It's important that this has '.*' at the start, so the matched data is reliably 'after' in the
		# child object. Use these where possible to make things more consistent.
		# Attempt to capture any starting prompt (when starting) with this regexp.
		self.base_prompt      = '\r\n.*[@#$] '
		# Environments are kept globally, as different sessions may re-connect to them.
		self.shutit_pexpect_session_environments = set()
		if self.username == '':
			try:
				if os.getlogin() != '':
					self.username = os.getlogin()
			except Exception:
				self.username = getpass.getuser()
			if self.username == '':
				self.handle_exit(msg='LOGNAME not set in the environment, ' + 'and login unavailable in python; ' + 'please set to your username.', exit_code=1)
		self.real_user        = os.environ.get('SUDO_USER', self.username)
		self.build_id         = (socket.gethostname() + '_' + self.real_user + '_' + str(time.time()) + '.' + str(datetime.datetime.now().microsecond))
		shutit_state_dir_base  = '/tmp/shutit_' + self.username
		if not os.access(shutit_state_dir_base,os.F_OK):
			mkpath(shutit_state_dir_base)
		self.shutit_state_dir       = shutit_state_dir_base + '/' + self.build_id
		if not os.access(self.shutit_state_dir,os.F_OK):
			mkpath(self.shutit_state_dir)
		os.chmod(self.shutit_state_dir,0o777)
		self.shutit_state_dir_build_db_dir = self.shutit_state_dir + '/build_db'
		self.shutit_state_pickle_file  = self.shutit_state_dir + '/shutit_pickle'
		def terminal_size():
			h, w, _, _ = struct.unpack('HHHH', fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0)))
			return int(h), int(w)
		try:
			self.root_window_size = terminal_size()
		except IOError:
			# If no terminal exists, set to default.
			self.root_window_size = (24,80)
		# Just override to the max possible
		self.pexpect_window_size = (65535,65535)

		# There is a problem with lines roughly around this length + the length of the prompt (?3k?)
		self.line_limit          = 3000

		self.interactive         = 1 # Default to true until we know otherwise

		self.allowed_delivery_methods = ['ssh','dockerfile','bash','docker','vagrant']


	def add_shutit_session(self, shutit):
		self.shutit_objects.append(shutit)




	def create_session(self,
	                   session_type='bash',
	                   docker_image=None,
	                   rm=None):
		assert isinstance(session_type, str)
		new_shutit = ShutIt(standalone=True)
		self.add_shutit_session(new_shutit)
		if session_type == 'bash':
			new_shutit.process_args(ShutItInit('build',
			                                   delivery='bash'))
			# TODO: can we get rid of/rationalise load_configs?
			new_shutit.load_configs()
			new_shutit.setup_host_child_environment()
			return new_shutit
		elif session_type == 'docker':
			new_shutit.process_args(ShutItInit('build',
			                                   delivery='docker',
			                                   base_image=docker_image))
			new_shutit.target['rm'] = rm
			# TODO: can we get rid of/rationalise load_configs?
			new_shutit.load_configs()
			target_child = new_shutit.conn_docker_start_container('target_child')
			new_shutit.setup_host_child_environment()
			new_shutit.setup_target_child_environment(target_child)
			return new_shutit
		else:
			new_shutit.fail('unhandled session type: ' + session_type)


	def do_final_messages(self):
		# Show final report messages (ie messages to show after standard report).
		if self.report_final_messages != '':
			self.shutit_objects[0].log(shutit_util.colourise(31,'\r\n\r\n' + self.report_final_messages + '\r\n\r\n'), level=logging.INFO, transient=True)


	def log(self, msg, add_final_message=False, level=logging.INFO, transient=False, newline=True, mask_password=True):
		"""Logging function.

		@param add_final_message: Add this log line to the final message output to the user
		@param level:             Python log level
		@param transient:         Just write to terminal, no new line. If not a
		                          terminal, write nothing.
		"""
		if mask_password:
			for password in shutit_global_object.secret_words_set:
				if password in msg:
					msg.replace(password,'REDACTED')
		if transient:
			if sys.stdout.isatty():
				if newline:
					msg += '\r\n'
				sys.stdout.write(msg)
			else:
				return True
		else:
			logging.log(level,msg)
			if add_final_message:
				self.report_final_messages = self.report_final_messages + '\r\n' + msg + '\r\n'
		return True


	def set_noninteractive(self, msg="setting non-interactive"):
		self.log(msg,level=logging.DEBUG)
		self.interactive = 0


	def determine_interactive(self):
		"""Determine whether we're in an interactive shell.
		Sets interactivity off if appropriate.
		cf http://stackoverflow.com/questions/24861351/how-to-detect-if-python-script-is-being-run-as-a-background-process
		"""
		try:
			if not sys.stdout.isatty() or os.getpgrp() != os.tcgetpgrp(sys.stdout.fileno()):
				self.set_noninteractive()
				return False
		except Exception:
			self.set_noninteractive(msg='Problems determining interactivity, assuming not.')
			return False
		if self.interactive == 0:
			return False
		return True


	def print_stack_trace(self):
		self.log('================================================================================',transient=True)
		self.log('Stack trace was:\n================================================================================',transient=True)
		import traceback
		(a,b,c) = sys.exc_info()
		self.log('sys.exc_info: ' + a + '\n' + b + '\n' + c, transient=True)
		traceback.print_tb(c)
		self.log('================================================================================',transient=True)


	def setup_logging(self):
		# If loglevel is an int, this has already been set up.
		if isinstance(self.loglevel, int):
			return
		logformat='%(asctime)s %(levelname)s: %(message)s'
		if self.logfile == '':
			self.loglevel = self.loglevel.upper()
			if self.loglevel == 'DEBUG':
				logging.basicConfig(format=logformat,level=logging.DEBUG)
			elif self.loglevel == 'ERROR':
				logging.basicConfig(format=logformat,level=logging.ERROR)
			elif self.loglevel in ('WARN','WARNING'):
				logging.basicConfig(format=logformat,level=logging.WARNING)
			elif self.loglevel == 'CRITICAL':
				logging.basicConfig(format=logformat,level=logging.CRITICAL)
			elif self.loglevel == 'INFO':
				logging.basicConfig(format=logformat,level=logging.INFO)
			else:
				logging.basicConfig(format=logformat,level=logging.DEBUG)
		else:
			self.loglevel = self.loglevel.upper()
			if self.loglevel == 'DEBUG':
				logging.basicConfig(format=logformat,filename=self.logfile,level=logging.DEBUG)
			elif self.loglevel == 'ERROR':
				logging.basicConfig(format=logformat,filename=self.logfile,level=logging.ERROR)
			elif self.loglevel in ('WARN','WARNING'):
				logging.basicConfig(format=logformat,filename=self.logfile,level=logging.WARNING)
			elif self.loglevel == 'CRITICAL':
				logging.basicConfig(format=logformat,filename=self.logfile,level=logging.CRITICAL)
			elif self.loglevel == 'INFO':
				logging.basicConfig(format=logformat,filename=self.logfile,level=logging.INFO)
			else:
				logging.basicConfig(format=logformat,filename=self.logfile,level=logging.DEBUG)
		self.loglevel = logging.getLogger().getEffectiveLevel()


	def handle_exit(self,exit_code=0,loglevel=logging.DEBUG,msg=None):
		if not msg:
			msg = '\nExiting with error code: ' + str(exit_code)
		if exit_code != 0:
			self.log('Exiting with error code: ' + str(exit_code),level=loglevel)
			self.log('Resetting terminal',level=loglevel)
		shutit_util.sanitize_terminal()
		sys.exit(exit_code)


def setup_signals():
	signal.signal(signal.SIGINT, shutit_util.ctrl_c_signal_handler)
	signal.signal(signal.SIGQUIT, shutit_util.ctrl_quit_signal_handler)


shutit_global_object = ShutItGlobal()
shutit_global_object.add_shutit_session(ShutIt(standalone=False))
