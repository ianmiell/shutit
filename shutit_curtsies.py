import curtsies
import time
import threading
import traceback
import sys


def managing_thread_main():
	time.sleep(1)
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
			level+=1
			code.append('%d, File: "%s", line %d, in %s, line %s: ' % (level, filename, lineno, name, str(line.strip())))
	# TODO: if the file is in the same folder or subfolder as a folder in: self.host['shutit_module_path']
	#       then show that context
	for line in code:
		shutit_global.shutit_global_object.stacktrace_lines_arr.append(line)
		#print(line)
	shutit_global.shutit_global_object.stacktrace_lines_arr.append("*** STACKTRACE - END ***")
	shutit_global.shutit_global_object.pane_manager.draw_screen(draw_type='default')
	managing_thread_main()


def track_main_thread():
	t = threading.Thread(target=managing_thread_main)
	t.daemon = True
	t.start()
