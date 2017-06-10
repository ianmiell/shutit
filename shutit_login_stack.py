"""Represents a ShutItLoginStack object.

Every time ShutItPexpectSession.login() is run a new item is added, and every
time it a corresponding logout() function is called, it is popped.

It also holds within it information about ShutItBackgroundCommand objects
belonging to this login.

"""

import logging
import shutit_global
from shutit_background import ShutItBackgroundCommand

class ShutItLoginStack(object):


	def __init__(self):
		"""
		"""
		self.stack = []


	def append(self, login_id):
		self.stack.append(ShutItLoginStackItem(login_id))
		return True


	def pop(self):
		return self.stack.pop()


	def length(self):
		return len(self.stack)


	def get_current_login_id(self):
		if len(self.stack):
			return self.stack[-1].login_id
		else:
			return None


	def get_current_login_item(self):
		if len(self.stack):
			return self.stack[-1]
		else:
			return None


	def find_sendspec(self):
		for stack_item in self.stack:
			if stack_item.find_sendspec():
				return True
		return False


	def __str__(self):
		string = '\n---- Login stack object ----'
		string += '\nstack: ' + str(self.stack)
		for item in self.stack:
			string += '\nlogin_item: ' + str(item)
		string += '\n----                    ----'
		return string



class ShutItLoginStackItem(object):


	def __init__(self,login_id):
		"""
		"""
		self.login_id                     = login_id
		self.background_objects           = []
		self.background_objects_completed = []


	def append_background_send(self,sendspec):
		shutit_background_command_object = ShutItBackgroundCommand(sendspec)
		self.background_objects.append(shutit_background_command_object)
		return shutit_background_command_object


	def has_blocking_background_send(self):
		"""Check whether any blocking background commands are waiting to run.
        If any are, return True. If none are, return False.
		"""
		for background_object in self.background_objects:
			# If it's running, or not started yet, it should block other tasks.
			if background_object.block_other_commands and background_object.run_state in ('S','N'):
				shutit_global.shutit_global_object.log('All objects are: ' + str(self),level=logging.DEBUG)
				shutit_global.shutit_global_object.log('The current blocking send object is: ' + str(background_object),level=logging.DEBUG)
				return True
			elif background_object.block_other_commands and background_object.run_state in ('F','C','T'):
				assert False, 'Blocking command should have been removed, in run_state: ' + background_object.run_state
			else:
				assert background_object.block_other_commands is False
		shutit_global.shutit_global_object.log('No blocking background objects exist.',level=logging.DEBUG)
		return False


	def check_background_commands_complete(self):
		"""Check whether any background commands are running or to be run.
		If none are, return True. If any are, return False.
		"""
		unstarted_command_exists  = False
		for background_object in self.background_objects:
			shutit_global.shutit_global_object.log('Checking background object: ' + str(background_object),level=logging.DEBUG)
			state = background_object.check_background_command_state()
			shutit_global.shutit_global_object.log('State is: ' + state,level=logging.DEBUG)
			if state in ('C','F','T'):
				self.background_objects.remove(background_object)
				self.background_objects_completed.append(background_object)
			elif state == 'S':
				# Running command exists
				return False, 'S', background_object
			elif state == 'N':
				unstarted_command_exists = True
			else:
				assert False, 'Un-handled: ' + state
			if state == 'F':
				return False, 'F', background_object
		shutit_global.shutit_global_object.log('Checking background objects done.',level=logging.DEBUG)
		if unstarted_command_exists:
			# Start up an unstarted one (in order), and return False
			for background_object in self.background_objects:
				state = background_object.check_background_command_state()
				if state == 'N':
					background_object.run_background_command()
					return False, 'N', background_object
		# Nothing left to do - return True.
		return True, 'OK', None


	def find_sendspec(self,sendspec):
		for background_object in self.background_objects:
			if background_object == sendspec:
				return True
		return False


	def __str__(self):
		string = '\n---- Login stack item object ----'
		string += '\nlogin_id: ' + str(self.login_id)
		for background_object in self.background_objects:
			string += '\nbackground_objects: ' + str(background_object)
		string += '\n----                        ----'
		return string
