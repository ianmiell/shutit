import itertools
import time
import threading
import traceback
import re
import sys
import os
import curtsies
#from curtsies.fmtfuncs import black, yellow, magenta, cyan, gray, blue, red, green, on_black, on_dark, on_red, on_green, on_yellow, on_blue, on_magenta, on_cyan, on_gray, bold, dark, underline, blink, invert, plain
from curtsies.fmtfuncs import blue, cyan, invert
from curtsies.input import Input

# There are two threads running in ShutIt. The 'main' one, which drives the
# automation, and the 'watcher' one, which manages either the different view
# panes, or outputs a stack trace of the main thread if 'nothing happens' on it.

# Boolean indicating whether we've already set up a tracker.
tracker_setup = False

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


# TODO: reject tmux sessions - it does not seem to play nice
# TODO: keep a time counter after the line
# TODO: show context of line (ie lines around)
# TODO: put the lines into an array of objects and mark the lines as inverted/not
def gather_module_paths():
	import shutit_global
	shutit_global_object = shutit_global.shutit_global_object
	owd = shutit_global_object.owd
	shutit_module_paths = set()
	for shutit_object in shutit_global.shutit_global_object.shutit_objects:
		shutit_module_paths = shutit_module_paths.union(set(shutit_object.host['shutit_module_path']))
	if '.' in shutit_module_paths:
		shutit_module_paths.remove('.')
		shutit_module_paths.add(owd)
	for path in shutit_module_paths:
		if path[0] != '/':
			shutit_module_paths.remove(path)
			shutit_module_paths.add(owd + '/' + path)
	return shutit_module_paths


def managing_thread_main():
	import shutit_global
	from shutit_global import SessionPaneLine
	shutit_global.shutit_global_object.global_thread_lock.acquire()
	shutit_module_paths = gather_module_paths()
	shutit_global.shutit_global_object.global_thread_lock.release()
	shutit_global.shutit_global_object.stacktrace_lines_arr = [SessionPaneLine('',time.time(),'log'),]
	last_code = []
	draw_type = 'default'
	zoom_state = None
	while True:
		# We have acquired the lock, so read in input
		with Input() as input_generator:
			input_char = input_generator.send(0.001)
			if input_char == 'r':
				# Rotate sessions at the bottom
				shutit_global.shutit_global_object.lower_pane_rotate_count += 1
			elif input_char == '1':
				if zoom_state == 1:
					draw_type = 'default'
					zoom_state = None
				else:
					draw_type = 'zoomed1'
					zoom_state = 1
			elif input_char == '2':
				if zoom_state == 2:
					draw_type = 'default'
					zoom_state = None
				else:
					draw_type = 'zoomed2'
					zoom_state = 2
			elif input_char == '3':
				if zoom_state == 3:
					draw_type = 'default'
					zoom_state = None
				else:
					draw_type = 'zoomed3'
					zoom_state = 3
			elif input_char == '4':
				if zoom_state == 4:
					draw_type = 'default'
					zoom_state = None
				else:
					draw_type = 'zoomed4'
					zoom_state = 4
			elif input_char == 'q':
				draw_type = 'clearscreen'
				shutit_global.shutit_global_object.pane_manager.draw_screen(draw_type=draw_type)
				os.system('reset')
				os._exit(1)
		# Acquire lock to write screen. Prevents nasty race conditions.
		# Different depending PY2/3
		if shutit_global.shutit_global_object.ispy3:
			if not shutit_global.shutit_global_object.global_thread_lock.acquire(blocking=False):
				time.sleep(0.01)
				continue
		else:
			if not shutit_global.shutit_global_object.global_thread_lock.acquire(False):
				time.sleep(0.01)
				continue
		code      = []
		for thread_id, stack in sys._current_frames().items():
			# ignore own thread:
			if thread_id == threading.current_thread().ident:
				continue
			for filename, lineno, name, line in traceback.extract_stack(stack):
				# if the file is in the same folder or subfolder as a folder in: self.host['shutit_module_path']
				# then show that context
				for shutit_module_path in shutit_module_paths:
					if filename.find(shutit_module_path) == 0:
						if len(shutit_global.shutit_global_object.stacktrace_lines_arr) == 0 or shutit_global.shutit_global_object.stacktrace_lines_arr[-1] != line:
							linearrow = '===> ' + str(line)
							code.append('_' * 80)
							code.append('=> %s:%d:%s' % (filename, lineno, name))
							code.append('%s' % (linearrow,))
							from_lineno = lineno - 5
							if from_lineno < 0:
								from_lineno = 0
								to_lineno   = 10
							else:
								to_lineno = lineno + 5
							lineno_count = from_lineno
							with open(filename, "r") as f:
								for line in itertools.islice(f, from_lineno, to_lineno):
									line = line.replace('\t','  ')
									lineno_count += 1
									if lineno_count == lineno:
										code.append('***' + str(lineno_count) + '> ' + line.rstrip())
									else:
										code.append('===' + str(lineno_count) + '> ' + line.rstrip())
							code.append('_' * 80)
		if code != last_code:
			for line in code:
				shutit_global.shutit_global_object.stacktrace_lines_arr.append(SessionPaneLine(line,time.time(),'log'))
			last_code = code
		shutit_global.shutit_global_object.pane_manager.draw_screen(draw_type=draw_type)
		shutit_global.shutit_global_object.global_thread_lock.release()



def managing_thread_main_simple():
	"""Simpler thread to track whether main thread has been quiet for long enough
	that a thread dump should be printed.
	"""
	import shutit_global
	last_msg = ''
	while True:
		printed_anything = False
		if shutit_global.shutit_global_object.log_trace_when_idle and time.time() - shutit_global.shutit_global_object.last_log_time > 10:
			this_msg = ''
			this_header = ''
			for thread_id, stack in sys._current_frames().items():
				# ignore own thread:
				if thread_id == threading.current_thread().ident:
					continue
				printed_thread_started = False
				for filename, lineno, name, line in traceback.extract_stack(stack):
					if not printed_anything:
						printed_anything = True
						this_header += '\n='*80 + '\n'
						this_header += 'STACK TRACES PRINTED ON IDLE: THREAD_ID: ' + str(thread_id) + ' at ' + time.strftime('%c') + '\n'
						this_header += '='*80 + '\n'
					if not printed_thread_started:
						printed_thread_started = True
					this_msg += '%s:%d:%s' % (filename, lineno, name) + '\n'
					if line:
						this_msg += '  %s' % (line,) + '\n'
			if printed_anything:
				this_msg += '='*80 + '\n'
				this_msg += 'STACK TRACES DONE\n'
				this_msg += '='*80 + '\n'
			if this_msg != last_msg:
				print(this_header + this_msg)
				last_msg = this_msg
		time.sleep(5)


def track_main_thread():
	global tracker_setup
	if not tracker_setup:
		tracker_setup = True
		t = threading.Thread(target=managing_thread_main)
		t.daemon = True
		t.start()


def track_main_thread_simple():
	global tracker_setup
	if not tracker_setup:
		tracker_setup = True
		t = threading.Thread(target=managing_thread_main_simple)
		t.daemon = True
		t.start()
