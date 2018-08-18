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
import fcntl
import pwd
import termios
import struct
import threading
from distutils.dir_util import mkpath
from shutit_session_setup import vagrant
sys.path.insert(0,os.path.abspath(os.path.dirname(__file__)) + '/shutit')
import shutit_threads

if sys.version_info[0] >= 3:
	unicode = str


class ShutItGlobal(object):
	"""Single object to store all the separate ShutIt sessions, and information
	that is global to all sessions.
	"""

	only_one = None
	def __init__(self):
		"""Constructor.
		"""
		self.shutit_objects = []
		# Primitive singleton enforcer.
		assert self.only_one is None, shutit_util.print_debug()
		self.only_one                = True

		# Capture the original working directory.
		self.owd                     = os.getcwd()

		# Python version.
		self.ispy3                   = (sys.version_info[0] >= 3)

		# Threading.
		self.global_thread_lock      = threading.Lock()
		# Acquire the lock by default.
		self.global_thread_lock.acquire()

		# Secret words.
		self.secret_words_set        = set()

		# Logging.
		# global logstream is written to by logger in each shutit_class.py object.
		self.logstream               = None
		self.logstream_size          = 1000000
		self.log_trace_when_idle     = False
		self.signal_id               = None
		self.window_size_max         = 65535
		self.username                = os.environ.get('LOGNAME', '')
		self.default_timeout         = 3600
		self.delaybeforesend         = 0
		self.default_encoding        = 'utf-8'

		# Panes.
		self.managed_panes           = False
		self.pane_manager            = None
		self.lower_pane_rotate_count = 0

		# Errors.
		self.stacktrace_lines_arr    = []

		# Prompts and shell.
		self.bash_startup_command    = "bash --noprofile --rcfile <(sleep .05||sleep 1)"
		# Quotes here are intentional. Some versions of sleep don't support fractional seconds.
		# True is called to take up the time require
		self.prompt_command          = "'sleep .05||sleep 1'"
		# It's important that this has '.*' at the start, so the matched data is reliably 'after' in the
		# child object. Use these where possible to make things more consistent.
		# Attempt to capture any starting prompt (when starting) with this regexp.
		# The '>' is for AIX and explains why we use '2>/dev/null' in some other parts
		# of the code (ie to avoid matching initialiser commands).
		self.base_prompt      = '\n.*[@#$] '
		# There is a problem with lines roughly around this length + the length of the prompt (?3k?)
		self.line_limit          = 3000
		# Terminal size
		def terminal_size():
			h, w, _, _ = struct.unpack('HHHH', fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0)))
			return int(h), int(w)
		try:
			self.root_window_size = terminal_size()
		except IOError:
			# If no terminal exists, set to default.
			self.root_window_size = (24,80)
		# Just override to the max possible
		self.pexpect_window_size = (self.window_size_max,self.window_size_max)
		self.interactive         = 1 # Default to true until we know otherwise

		# Session environments.
		# Environments are kept globally, as different sessions may re-connect to them.
		self.shutit_pexpect_session_environments = set()

		# Real username.
		if self.username == '':
			try:
				if os.getlogin() != '':
					self.username = os.getlogin()
			except Exception:
				self.username = getpass.getuser()
			if self.username == '':
				self.handle_exit(msg='LOGNAME not set in the environment, ' + 'and login unavailable in python; ' + 'please set to your username.', exit_code=1)
		self.real_user        = os.environ.get('SUDO_USER', self.username)
		self.real_user_id     = pwd.getpwnam(self.real_user).pw_uid

		# ShutIt build ID.
		self.build_id         = (socket.gethostname() + '_' + self.real_user + '_' + str(time.time()) + '.' + str(datetime.datetime.now().microsecond))
		# ShutIt state directory.
		shutit_state_dir_base  = '/tmp/shutit_' + self.username
		if not os.access(shutit_state_dir_base,os.F_OK):
			mkpath(shutit_state_dir_base,mode=0o777)
		self.shutit_state_dir       = shutit_state_dir_base + '/' + self.build_id
		os.chmod(shutit_state_dir_base,0o777)
		if not os.access(self.shutit_state_dir,os.F_OK):
			mkpath(self.shutit_state_dir,mode=0o777)
		os.chmod(self.shutit_state_dir,0o777)
		self.shutit_state_dir_build_db_dir = self.shutit_state_dir + '/build_db'

		# Allowed delivery methods.
		self.allowed_delivery_methods = ['ssh','dockerfile','bash','docker','vagrant']

	def __str__(self):
		str_repr = '\n====== SHUTIT_GLOBAL_OBJECT BEGIN ====='
		str_repr += '\tself.signal_id='          + str(self.signal_id)
		str_repr += '\tself.window_size_max='    + str(self.window_size_max)
		str_repr += '\tself.username='           + str(self.username)
		str_repr += '\tbase_prompt='             + str(self.base_prompt)
		str_repr += '\treal_user='               + str(self.real_user)
		str_repr += '\treal_user_id='            + str(self.real_user_id)
		str_repr += '\tbuild_id='                + str(self.build_id)
		str_repr += '\tdelaybeforesend='         + str(self.delaybeforesend)
		str_repr += '\tprompt_command='          + str(self.prompt_command)
		str_repr += '\tself.default_encoding='   + str(self.default_encoding)
		for shutit_object in self.shutit_objects:
			str_repr += str(shutit_object)
		str_repr += '\n====== SHUTIT_GLOBAL_OBJECT DONE ====='
		return str_repr



	def create_session(self,
	                   session_type='bash',
	                   docker_image=None,
	                   rm=None,
	                   echo=False,
	                   walkthrough=False,
	                   walkthrough_wait=-1,
	                   nocolor=False,
	                   loglevel='WARNING'):
		assert isinstance(session_type, str), shutit_util.print_debug()
		new_shutit = ShutIt(standalone=True, session_type=session_type)
		self.shutit_objects.append(new_shutit)
		if session_type == 'bash':
			new_shutit.process_args(ShutItInit('build',
			                                   delivery='bash',
			                                   echo=echo,
			                                   walkthrough=walkthrough,
			                                   walkthrough_wait=walkthrough_wait,
			                                   loglevel=loglevel))
			new_shutit.load_configs()
			new_shutit.setup_host_child_environment()
			return new_shutit
		elif session_type == 'docker':
			new_shutit.process_args(ShutItInit('build',
			                                   delivery='docker',
			                                   base_image=docker_image,
			                                   echo=echo,
			                                   walkthrough=walkthrough,
			                                   walkthrough_wait=walkthrough_wait,
			                                   loglevel=loglevel))
			new_shutit.target['rm'] = rm
			target_child = new_shutit.conn_docker_start_container('target_child')
			new_shutit.setup_host_child_environment()
			new_shutit.setup_target_child_environment(target_child)
			return new_shutit
		new_shutit.fail('unhandled session type: ' + session_type)
		return new_shutit


	def create_session_vagrant(self,
	                           session_name,
	                           num_machines,
	                           vagrant_image,
	                           vagrant_provider,
	                           gui,
	                           memory,
	                           swapsize,
	                           echo,
	                           walkthrough,
	                           walkthrough_wait,
	                           nocolor,
	                           vagrant_version,
	                           virt_method,
	                           root_folder,
	                           loglevel):
		new_shutit = ShutIt(standalone=True, session_type='vagrant')
		self.shutit_objects.append(new_shutit)
		# Vagrant is: delivery over bash, but running the vagrant scripts first.
		new_shutit.process_args(ShutItInit('build',
		                                   delivery='bash',
		                                   echo=echo,
		                                   walkthrough=walkthrough,
		                                   walkthrough_wait=walkthrough_wait,
		                                   loglevel=loglevel))
		new_shutit.load_configs()
		new_shutit.setup_host_child_environment()
		# Run vagrant setup now
		vagrant.pre_build(shutit=new_shutit,
		                  vagrant_version=vagrant_version,
		                  virt_method=virt_method)
		machines = vagrant.setup_machines(new_shutit,
		                                  vagrant_image,
		                                  virt_method,
		                                  gui,
		                                  memory,
		                                  root_folder,
		                                  session_name,
		                                  swapsize,
		                                  num_machines)
		new_shutit.vagrant_machines = machines
		return new_shutit



	def determine_interactive(self):
		"""Determine whether we're in an interactive shell.
		Sets interactivity off if appropriate.
		cf http://stackoverflow.com/questions/24861351/how-to-detect-if-python-script-is-being-run-as-a-background-process
		"""
		try:
			if not sys.stdout.isatty() or os.getpgrp() != os.tcgetpgrp(sys.stdout.fileno()):
				self.interactive = 0
				return False
		except Exception:
			self.interactive = 0
			return False
		if self.interactive == 0:
			return False
		return True


	def setup_panes(self, action=None):
		assert not self.managed_panes or (self.managed_panes and self.logstream)
		assert action is not None
		# TODO: managed_panes and echo are incompatible
		if self.managed_panes:
			self.pane_manager     = PaneManager(self)
			shutit_threads.track_main_thread()
		else:
			if action == 'build':
				shutit_threads.track_main_thread_simple()


	def yield_to_draw(self):
		# Release the lock to allow the screen to be drawn, then acquire again.
		# Only ever yield if there are any sessions to draw.
		if len(get_shutit_pexpect_sessions()) > 0:
			self.global_thread_lock.release()
			# Allow a _little_ time for others to get a look in
			time.sleep(0.001)
			self.global_thread_lock.acquire()


	def handle_exit(self,
	                exit_code=0,
	                msg=None):
		if not msg:
			msg = '\r\nExiting with error code: ' + str(exit_code)
			msg += '\r\nInvoking command was: ' + sys.executable
			for arg in sys.argv:
				msg += ' ' + arg
		if exit_code != 0:
			self.shutit_print('\r\nExiting with error code: ' + str(exit_code))
			self.shutit_print(msg)
			self.shutit_print('\r\nResetting terminal')
			shutit_util.sanitize_terminal()
			shutit_util.exit_cleanup()
		sys.exit(exit_code)


	def shutit_print(self, msg):
		"""Handles simple printing of a msg at the global level.
		"""
		if self.pane_manager is None:
			print(msg)

def get_shutit_pexpect_sessions():
	"""Returns all the shutit_pexpect sessions in existence.
	"""
	sessions = []
	for shutit_object in shutit_global_object.shutit_objects:
		for key in shutit_object.shutit_pexpect_sessions:
			sessions.append(shutit_object.shutit_pexpect_sessions[key])
	return sessions

shutit_global_object = ShutItGlobal()

# Only at this point can we import other modules, otherwise we get race failures.
from shutit_class import ShutIt, ShutItInit
sys.path.insert(0,os.path.abspath(os.path.dirname(__file__)) + '/shutit')
import shutit_util

# Create default shutit object. TODO: do we need this?
shutit_global_object.shutit_objects.append(ShutIt(standalone=False, session_type='bash'))
