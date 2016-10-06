import sys
import time
import shutit_global

PY3 = (sys.version_info[0] >= 3)

class ShutItTestSessionStage(object):

	def __init__(self, difficulty=1.0):
		self.difficulty = difficulty
		self.result     = ''
		self.num_resets = 0
		self.num_hints  = 0
		self.start_time = None
		self.end_time   = None

	def __str__(self):
		string = ''
		string += '\nnum_skips        = ' + str(self.num_skips)
		string += '\nnum_resets       = ' + str(self.num_resets)
		string += '\nnum_oks          = ' + str(self.num_oks)
		string += '\nnum_hints        = ' + str(self.num_hints)
		string += '\nnum_fails        = ' + str(self.num_fails)
		string += '\ncurrent_stage    = ' + str(self.current_stage)
		string += '\ntotal_stages     = ' + str(self.total_stages)
		string += '\ntimes            = ' + str(self.times)
		string += '\ntimer_start_time = ' + str(self.timer_start_time)
		return string

	def start_timer(self):
		self.timer_start_time = time.time()

	def end_timer(self):
		if self.timer_start_time == None:
			shutit_global.fail('end_timer called with no timer_start_time set')
		times.append(time.time() - self.timer_start_time)
		self.timer_start_time = None

	def is_complete(self):
		if self.result == '':
			return False
		else:
			return True



class ShutItTestSession(object):

	def __init__(self):
		self.stages           = []

	def __str__(self):
		string = ''
		for stage in self.stages:
			string += '\n' + str(stage)
		return string
		
	def new_stage(self,difficulty):
		difficulty = float(difficulty)
		stage = ShutItTestSessionStage(difficulty))
		self.stages.append(stage)
		return stage

	def add_reset():
		pass

	def add_skip():
		pass

	def add_fail():
		pass

	def add_ok():
		pass

	def add_hint():
		pass
