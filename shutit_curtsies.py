import curtsies
import time
import threading
import traceback
import sys


def main_tracker():
	import shutit_global
	lines = []
	lines.append("\n*** STACKTRACE - START ***\n")
	code = []
	for thread_id, stack in sys._current_frames().items():
		# ignore own thread:
		# TODO: does not work in python2
		if thread_id == threading.get_ident():
			continue
		code.append("\n# ThreadID: %s" % thread_id)
		for filename, lineno, name, line in traceback.extract_stack(stack):
			code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
			if line:
				code.append("  %s" % (line.strip()))
	for line in code:
		lines.append(line)
	lines.append("\n*** STACKTRACE - END ***\n")
	lines.append(shutit_global.shutit_global_object)
	time.sleep(5)
	main_tracker()


def track_main_thread():
	t = threading.Thread(target=main_tracker)
	t.daemon = True
	t.start()


# shutit_global.shutit_objects have the pexpect sessions in their shutit_pexpect_sessions variable.
class PaneManager(object):
	only_one = None
	def __init__(self):
		"""
		
		only_one             - singleton insurance
		"""
		assert self.only_one is None
		self.only_one is True
		# TODO: screen width and height
		# Keep it simple for now by creating four panes
		top_left     = SessionPane('top_left')
		top_right    = SessionPane('top_right')
		bottom_left  = SessionPane('bottom_left')
		bottom_right = SessionPane('bottom_right')
		self.window     = None
		self.screen_arr = None
		self.wheight    = None
		self.wwidth     = None
		self.refresh_window()
	# TODO: place panes in appropriate locations.
	# TODO: logs directed to one pane. https://stackoverflow.com/questions/31999627/storing-logger-messages-in-a-string - log to stringio and then clear
	# TODO: send/expect to another
	# TODO: code context to another


	def refresh_window(self):
		self.window               = curtsies.FullscreenWindow(hide_cursor=True)
		self.screen_arr           = None
		self.wheight              = self.window.height
		self.wwidth               = self.window.width
		# Divide the screen up into two, to keep it simple for now
		self.wheight_top_end      = int(self.wheight / 2)
		self.wheight_bottom_start = int(self.wheight / 2)
		self.wwidth_left_end      = int(self.wwidth / 2)
		self.wwidth_right_start   = int(self.wwidth / 2)
		assert self.wheight >= 24, self.quit_autotrace('Terminal not tall enough!')
		assert self.wwidth >= 80, self.quit_autotrace('Terminal not wide enough!')


	def draw_screen(self, clear_screen=False, quick_help='HELP TODO'):
		assert draw_type in ('sessions','help','clearscreen')
		self.screen_arr = curtsies.FSArray(self.wheight, self.wwidth)
		# Header
		header_text = 'Shutit'
		self.screen_arr[0:1,0:len(header_text)] = [blue(header_text)]
		# Footer
		space = (self.wwidth - len(quick_help))*' '
		footer_text = space + quick_help
		self.screen_arr[self.wheight-1:self.wheight,0:len(footer_text)] = [invert(blue(footer_text))]
		# Draw the sessions.
		# Is there a zoomed session? Just write that one out.
		# TODO: get sessions and write write_out_session_to_fit_pane function
		if clear_screen:
			for y in range(0,self.wheight):
				line = ' '*self.wwidth
				self.screen_arr[y:y+1,0:len(line)] = [line]
		for session in self.pexpect_sessions:
			session.write_out_session_to_fit_pane()


# Represents a line in the array of output
class PexpectSessionLine(object):
	def __init__(self, line_str, time_seen):
		self.line_str        = line_str
		self.time_seen       = time_seen


# Represents a pane with no concept of context or content.
class SessionPane(object):

	def __init__(self, name):
		self.name                 = name
		self.top_left_x           = -1
		self.top_left_y           = -1
		self.bottom_right_x       = -1
		self.bottom_right_y       = -1
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
		return self.bottom_right_y - self.top_left_
