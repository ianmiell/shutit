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
		string += '\nnum_resets       = ' + str(self.num_resets)
		string += '\nnum_hints        = ' + str(self.num_hints)
		string += '\nresult           = ' + str(self.result)
		string += '\nstart_time       = ' + str(self.start_time)
		string += '\nend_time         = ' + str(self.end_time)
		return string

	def start_timer(self):
		if self.start_time != None:
			shutit_global.shutit.fail('start_timer called with start_time already set')
		self.start_time = time.time()

	def end_timer(self):
		if self.start_time == None:
			shutit_global.shutit.fail('end_timer called with no start_time set')
		if self.end_time != None:
			shutit_global.shutit.fail('end_time already set')
		self.end_time = time.time()
		self.total_time = self.end_time - self.start_time

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
		n=0
		for stage in self.stages:
			n+=1
			stage_desc = 'Stage ' + str(n) + ' of ' + str(len(self.stages))
			string += '\n' + stage_desc
			string += '\n' + str(stage)
		return string
		
	def new_stage(self,difficulty):
		difficulty = float(difficulty)
		stage = ShutItTestSessionStage(difficulty)
		self.stages.append(stage)
		return stage

	def add_reset(self):
		if self.stages == []:
			shutit_global.shutit.fail('add_reset: no stages to reset')
		stage = self.stages[-1]
		stage.num_resets += 1

	def add_skip(self):
		if self.stages == []:
			shutit_global.shutit.fail('add_skip: no stages to skip')
		stage = self.stages[-1]
		if stage.result != '':
			shutit_global.shutit.fail('add_skip: result already determined')
		else:
			stage.result = 'SKIP'

	def add_fail(self):
		if self.stages == []:
			shutit_global.shutit.fail('add_fail: no stages to fail')
		stage = self.stages[-1]
		if stage.result != '':
			shutit_global.shutit.fail('add_fail: result already determined')
		else:
			stage.result = 'FAIL'

	def add_ok(self):
		if self.stages == []:
			shutit_global.shutit.fail('add_ok: no stages to ok')
		stage = self.stages[-1]
		if stage.result != '':
			shutit_global.shutit.fail('add_ok: result already determined')
		else:
			stage.result = 'OK'

	def add_hint(self):
		if self.stages == []:
			shutit_global.shutit.fail('add_hint: no stages to add hint for')
		stage = self.stages[-1]
		stage.num_hints += 1

	def start_timer(self):
		if self.stages == []:
			shutit_global.shutit.fail('start_timer: no stages to time')
		stage = self.stages[-1]
		stage.start_timer()

	def end_timer(self):
		if self.stages == []:
			shutit_global.shutit.fail('end_timer: no stages to time')
		stage = self.stages[-1]
		stage.end_timer()
