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
import pwd
import re
import termios
import signal
import struct
import threading
from distutils.dir_util import mkpath
import curtsies
#from curtsies.fmtfuncs import black, yellow, magenta, cyan, gray, blue, red, green, on_black, on_dark, on_red, on_green, on_yellow, on_blue, on_magenta, on_cyan, on_gray, bold, dark, underline, blink, invert, plain
from curtsies.fmtfuncs import blue, cyan, invert
from shutit_session_setup import vagrant
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


# shutit_global.shutit_objects have the pexpect sessions in their shutit_pexpect_sessions variable.
class PaneManager(object):
	only_one = None
	def __init__(self, shutit_global_object):
		"""

		only_one             - singleton insurance
		"""
		assert self.only_one is None
		self.only_one is True
		# Keep it simple for now by creating four panes
		self.shutit_global             = shutit_global_object
		self.top_left_session_pane     = SessionPane('top_left')
		self.top_right_session_pane    = SessionPane('top_right')
		self.bottom_left_session_pane  = SessionPane('bottom_left')
		self.bottom_right_session_pane = SessionPane('bottom_right')
		self.window                    = None
		self.screen_arr                = None
		self.wheight                   = None
		self.wwidth                    = None
		# Whether to actually draw the screen - defaults to 'True'
		self.do_render                 = True
		# Refresh the window
		self.refresh_window()


	def refresh_window(self):
		self.window               = curtsies.FullscreenWindow(hide_cursor=True)
		self.wheight              = self.window.height
		self.wwidth               = self.window.width
		self.screen_arr           = None
		# Divide the screen up into two, to keep it simple for now
		self.wheight_top_end      = int(self.wheight / 2)
		self.wheight_bottom_start = int(self.wheight / 2)
		self.wwidth_left_end      = int(self.wwidth / 2)
		self.wwidth_right_start   = int(self.wwidth / 2)
		assert self.wheight >= 24, 'Terminal not tall enough: ' + str(self.wheight) + ' < 24'
		assert self.wwidth >= 80, 'Terminal not wide enough: ' + str(self.wwidth) + ' < 80'


	def draw_screen(self, draw_type='default', quick_help=None):
		if quick_help is None:
			quick_help = 'Help: (r)otate shutit sessions | re(d)raw screen | (1,2,3,4) zoom pane in/out | (q)uit'
		assert draw_type in ('default','clearscreen','zoomed1','zoomed2','zoomed3','zoomed4')
		# Header
		header_text = u'  <= Shutit'
		self.screen_arr           = curtsies.FSArray(self.wheight, self.wwidth)
		self.screen_arr[0:1,0:len(header_text)] = [blue(header_text)]
		# Footer
		space = (self.wwidth - len(quick_help))*' '
		footer_text = space + quick_help
		if not self.shutit_global.ispy3:
			footer_text = footer_text.decode('utf-8')
		self.screen_arr[self.wheight-1:self.wheight,0:len(footer_text)] = [invert(blue(footer_text))]
		if draw_type in ('default','zoomed3','zoomed4'):
			# get sessions - for each ShutIt object in shutit_global
			sessions = list(get_shutit_pexpect_sessions())
			# reverse sessions as we're more likely to be interested in later ones.
			sessions.reverse()
			# Update the lower_pane_rotate_count so that it doesn't exceed the length of sessions.
			self.shutit_global.lower_pane_rotate_count = self.shutit_global.lower_pane_rotate_count % len(sessions)
			sessions = sessions[-self.shutit_global.lower_pane_rotate_count:] + sessions[:-self.shutit_global.lower_pane_rotate_count]
		# Truncate logstream if it gets too big.
		if self.shutit_global.logstream.getvalue() > self.shutit_global.logstream_size:
			self.shutit_global.logstream.truncate(self.shutit_global.logstream_size)
		if draw_type == 'default':
			# Draw the sessions.
			self.do_layout_default()
			logstream_lines = []
			logstream_string_lines_list = self.shutit_global.logstream.getvalue().split('\n')
			for line in logstream_string_lines_list:
				logstream_lines.append(SessionPaneLine(line,time.time(),'log'))
			self.write_out_lines_to_fit_pane(self.top_left_session_pane, logstream_lines, u'Logs')
			self.write_out_lines_to_fit_pane(self.top_right_session_pane, self.shutit_global.stacktrace_lines_arr, u'Code Context')
			# Count two sessions
			count = 0
			for shutit_pexpect_session in sessions:
				count += 1
				if count == 2:
					self.write_out_lines_to_fit_pane(self.bottom_left_session_pane,
					                                 shutit_pexpect_session.session_output_lines,
					                                 u'Shutit Session: ' + str(shutit_pexpect_session.pexpect_session_number) + '/' + str(len(sessions)))
				elif count == 1:
					self.write_out_lines_to_fit_pane(self.bottom_right_session_pane,
					                                 shutit_pexpect_session.session_output_lines,
					                                 u'ShutIt Session: ' + str(shutit_pexpect_session.pexpect_session_number) + '/' + str(len(sessions)))
				else:
					break
		elif draw_type == 'zoomed1':
			self.do_layout_zoomed(zoom_number=1)
			logstream_lines = []
			logstream_string_lines_list = self.shutit_global.logstream.getvalue().split('\n')
			for line in logstream_string_lines_list:
				logstream_lines.append(SessionPaneLine(line,time.time(),'log'))
			self.write_out_lines_to_fit_pane(self.top_left_session_pane, logstream_lines, u'Logs')
		elif draw_type == 'zoomed2':
			self.do_layout_zoomed(zoom_number=2)
			self.write_out_lines_to_fit_pane(self.top_left_session_pane, self.shutit_global.stacktrace_lines_arr, u'Code Context')
		elif draw_type == 'zoomed3':
			self.do_layout_zoomed(zoom_number=3)
			# Get first session
			count = 0
			for shutit_pexpect_session in sessions:
				count += 1
				if count == 2:
					self.write_out_lines_to_fit_pane(self.top_left_session_pane,
					                                 shutit_pexpect_session.session_output_lines,
					                                 u'Shutit Session: ' + str(shutit_pexpect_session.pexpect_session_number) + '/' + str(len(sessions)))
				elif count > 2:
					break
		elif draw_type == 'zoomed4':
			self.do_layout_zoomed(zoom_number=4)
			# Get second session
			for shutit_pexpect_session in sessions:
				self.write_out_lines_to_fit_pane(self.top_left_session_pane,
					                                 shutit_pexpect_session.session_output_lines,
					                                 u'ShutIt Session: ' + str(shutit_pexpect_session.pexpect_session_number) + '/' + str(len(sessions)))
				break
		elif draw_type == 'clearscreen':
			for y in range(0,self.wheight):
				line = u' '*self.wwidth
				self.screen_arr[y:y+1,0:len(line)] = [line]
		else:
			assert False, 'Layout not handled: ' + draw_type
		if self.do_render:
			self.window.render_to_terminal(self.screen_arr, cursor_pos=(0,0))


	def write_out_lines_to_fit_pane(self, pane, p_lines, title):
		assert pane is not None
		assert isinstance(pane, SessionPane)
		assert isinstance(title, unicode)
		pane_width  = pane.get_width()
		pane_height = pane.get_height()
		assert pane_width > 39
		assert pane_height > 19
		# We reserve one row at the end as a pane status line
		available_pane_height   = pane.get_height() - 1
		lines_in_pane_str_arr   = []
		p_lines_str = []
		for session_pane_line in p_lines:
			assert isinstance(session_pane_line, SessionPaneLine)
			p_lines_str.append(session_pane_line.line_str)
		p_lines = p_lines_str
		p_lines_str = None
		# Scrub any ansi escape sequences.
		ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
		if not self.shutit_global.ispy3:
			lines = [ ansi_escape.sub('', line).strip().decode('utf-8') for line in p_lines ]
		else:
			lines = [ ansi_escape.sub('', line).strip() for line in p_lines ]
		# If the last line is blank we can just skip it.
		if len(lines) > 0 and lines[-1] == '':
			lines = lines[:-1]
		for line in lines:
			# Take the next line in the stream. If it's greater than the pane_width,
			# Then parcel over multiple lines
			while len(line) > pane_width-1 and len(line) > 0:
				lines_in_pane_str_arr.append(line[:pane_width-1])
				line = line[pane_width-1:]
			lines_in_pane_str_arr.append(line)
		# Status line:
		lines_in_pane_str_arr.append(title)
		top_y                                      = pane.top_left_y
		bottom_y                                   = pane.bottom_right_y
		for i, line in zip(reversed(range(top_y,bottom_y)), reversed(lines_in_pane_str_arr)):
			# Status on bottom line
			# If    this is on the top, and height + top_y value == i (ie this is the last line of the pane)
			#    OR this is on the bottom (ie top_y is not 1), and height + top_y == i
			# One or both of these help prevent glitches on the screen. Don't know why. Maybe replace with more standard list TODO
			if (top_y == 1 and available_pane_height + top_y == i) or (top_y != 1 and available_pane_height + top_y == i):
				self.screen_arr[i:i+1, pane.top_left_x:pane.top_left_x+len(line)] = [cyan(invert(line))]
			else:
				self.screen_arr[i:i+1, pane.top_left_x:pane.top_left_x+len(line)] = [line]



	def do_layout_zoomed(self, zoom_number):
		# Only one window - the top left.
		self.top_left_session_pane.set_position    (top_left_x=0,
		                                            top_left_y=1,
		                                            bottom_right_x=self.wwidth,
		                                            bottom_right_y=self.wheight-1)


	def do_layout_default(self):
		self.top_left_session_pane.set_position    (top_left_x=0,
		                                            top_left_y=1,
		                                            bottom_right_x=self.wwidth_left_end,
		                                            bottom_right_y=self.wheight_bottom_start)
		self.top_right_session_pane.set_position   (top_left_x=self.wwidth_right_start,
		                                            top_left_y=1,
		                                            bottom_right_x=self.wwidth,
		                                            bottom_right_y=self.wheight_bottom_start)
		self.bottom_right_session_pane.set_position(top_left_x=self.wwidth_right_start,
		                                            top_left_y=self.wheight_bottom_start,
		                                            bottom_right_x=self.wwidth,
		                                            bottom_right_y=self.wheight-1)
		self.bottom_left_session_pane.set_position (top_left_x=0,
		                                            top_left_y=self.wheight_bottom_start,
		                                            bottom_right_x=self.wwidth_left_end,
		                                            bottom_right_y=self.wheight-1)


# Represents a window pane with no concept of context or content.
class SessionPane(object):

	def __init__(self, name):
		self.name                 = name
		self.top_left_x           = -1
		self.top_left_y           = -1
		self.bottom_right_x       = -1
		self.bottom_right_y       = -1
		self.line_buffer_size     = 1000
		assert self.name in ('top_left','bottom_left','top_right','bottom_right')

	def __str__(self):
		string =  '\n============= SESSION PANE OBJECT BEGIN ==================='
		string += '\nname: '           + str(self.name)
		string += '\ntop_left_x: '     + str(self.top_left_x)
		string += '\ntop_left_y: '     + str(self.top_left_y)
		string += '\nbottom_right_x: ' + str(self.bottom_right_x)
		string += '\nbottom_right_y: ' + str(self.bottom_right_y)
		string += '\nwidth: '          + str(self.get_width())
		string += '\nheight: '         + str(self.get_width())
		string += '\n============= SESSION PANE OBJECT END   ==================='
		return string

	def set_position(self, top_left_x, top_left_y, bottom_right_x, bottom_right_y):
		self.top_left_x     = top_left_x
		self.top_left_y     = top_left_y
		self.bottom_right_x = bottom_right_x
		self.bottom_right_y = bottom_right_y

	def get_width(self):
		return self.bottom_right_x - self.top_left_x

	def get_height(self):
		return self.bottom_right_y - self.top_left_y


# Represents a line in the array of output
class SessionPaneLine(object):

	def __init__(self, line_str, time_seen, line_type):
		assert line_type in ('log','output')
		self.line_str        = line_str
		if isinstance(line_str, bytes):
			line_str = line_str.decode('utf-8')
		assert isinstance(line_str, unicode), 'line_str type: ' + str(type(line_str))
		self.time_seen       = time_seen
		self.time_seen       = time_seen

	def __str__(self):
		return self.line_str


def setup_signals():
	"""Set up the signal handlers.
	"""
	signal.signal(signal.SIGINT, shutit_util.ctrl_c_signal_handler)
	signal.signal(signal.SIGQUIT, shutit_util.ctrl_quit_signal_handler)


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
import shutit_util

# Create default shutit object. TODO: do we need this?
shutit_global_object.shutit_objects.append(ShutIt(standalone=False, session_type='bash'))
