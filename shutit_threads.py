import itertools
import time
import threading
import traceback
import sys
import os
from curtsies.input import Input

# There are two threads running in ShutIt. The 'main' one, which drives the
# automation, and the 'watcher' one, which manages either the different view
# panes, or outputs a stack trace of the main thread if 'nothing happens' on it.

# Boolean indicating whether we've already set up a tracker.
tracker_setup = False


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
