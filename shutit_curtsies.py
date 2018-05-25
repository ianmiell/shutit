import curtsies
import time
import threading
import traceback
import sys


# Example queue code:
if sys.version_info[0] >= 3:
	import queue
else:
	import Queue
	queue = Queue


def main_tracker():
	import shutit_global
	lines = []
	lines.append("\n*** STACKTRACE - START ***\n")
	code = []
	for thread_id, stack in sys._current_frames().items():
		# ignore own thread:
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


# Represents a line in the array of output
class PexpectSessionLine(object):
	def __init__(self, line_str, time_seen, line_type):
		self.line_str        = line_str
		self.time_seen       = time_seen
		self.line_type       = line_type
		# A 'display_sync_line' is an empty line designed to ensure that display syncs time-wise.
		assert self.line_type in ('program_output','display_sync_line')


# Represents a pane with no concept of context or content.
class SessionPane(object):

	def __init__(self, name, color):
		self.name                 = name
		self.top_left_x           = -1
		self.top_left_y           = -1
		self.bottom_right_x       = -1
		self.bottom_right_y       = -1
		self.color                = color
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
