import curtsies
import time
import threading
import traceback
import sys


def managing_thread_main():
	#import shutit_global
	#lines = []
	#lines.append("\n*** STACKTRACE - START ***\n")
	#code = []
	#for thread_id, stack in sys._current_frames().items():
	#	# ignore own thread:
	#	if thread_id == threading.current_thread().ident:
	#	if thread_id == threading.get_ident():
	#		continue
	#	code.append("\n# ThreadID: %s" % thread_id)
	#	for filename, lineno, name, line in traceback.extract_stack(stack):
	#		code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
	#		if line:
	#			code.append("  %s" % (line.strip()))
	#for line in code:
	#	lines.append(line)
	#lines.append("\n*** STACKTRACE - END ***\n")
	#lines.append(shutit_global.shutit_global_object)
	print('managing')
	time.sleep(5)
	managing_thread_main()


def track_main_thread():
	t = threading.Thread(target=managing_thread_main)
	t.daemon = True
	t.start()
