import curtsies
import time
import threading
import traceback
import sys


def managing_thread_main():
	import shutit_global
	shutit_global.shutit_global_object.stacktrace_lines_arr = []
	shutit_global.shutit_global_object.stacktrace_lines_arr.append("*** STACKTRACE - START ***")
	code = []
	for thread_id, stack in sys._current_frames().items():
		# ignore own thread:
		if thread_id == threading.current_thread().ident:
			continue
		code.append("# ThreadID: %s" % thread_id)
		level = 0
		for filename, lineno, name, line in traceback.extract_stack(stack):
			level += 1
			if level < 5:
				continue
			code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
			if line:
				code.append("  %s" % (line.strip()))
	for line in code:
		shutit_global.shutit_global_object.stacktrace_lines_arr.append(line)
	shutit_global.shutit_global_object.stacktrace_lines_arr.append("*** STACKTRACE - END ***")
	
	#lines.append(shutit_global.shutit_global_object)
	time.sleep(0.25)
	#shutit_global.shutit_global_object.pane_manager.draw_screen(draw_type='clearscreen')
	shutit_global.shutit_global_object.pane_manager.draw_screen()
	managing_thread_main()


def track_main_thread():
	t = threading.Thread(target=managing_thread_main)
	t.daemon = True
	t.start()
