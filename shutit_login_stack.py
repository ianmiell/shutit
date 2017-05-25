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
		string = ''
		string += '\nstack: ' + str(self.stack)
		for item in self.stack:
			string += '\nlogin_item: ' + str(item)
		return string



class ShutItLoginStackItem(object):


	def __init__(self,login_id):
		"""
		"""
		self.login_id           = login_id
		self.background_objects = []


	def append_background_send(self,sendspec):
		shutit_background_command_object = ShutItBackgroundCommand(sendspec)
		self.background_objects.append(shutit_background_command_object)
		return shutit_background_command_object


	def has_blocking_background_send(self):
		for background_object in self.background_objects:
			if background_object.block_other_commands:
				shutit_global.shutit_global_object.log('The blocking send object is: ' + str(background_object),level=logging.DEBUG)
				return True


	def check_background_commands(self):
		unstarted_command_exists  = False
		incomplete_command_exists = False
		for background_object in self.background_objects:
			state = background_object.check_background_command_state()
			if state != 'C':
				if state == 'N':
					unstarted_command_exists = True
				else:
					incomplete_command_exists = True
		if incomplete_command_exists:
			# Started
			return False
		if unstarted_command_exists:
			# Start up an unstarted one (in order), and return False
			for background_object in self.background_objects:
				state = background_object.check_background_command_state()
				if state == 'N':
					background_object.run_background_command()
					return False
		# Nothing left to do - return True.
		return True

	def find_sendspec(self,sendspec):
		for background_object in self.background_objects:
			if background_object == sendspec:
				return True
		return False

	def __str__(self):
		string = ''
		string += '\nlogin_id: ' + str(self.login_id)
		for background_object in self.background_objects:
			string += '\nbackground_objects: ' + str(background_object)
		return string
