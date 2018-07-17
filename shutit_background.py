r"""Represents a ShutIt background command.

    - options to:
        - cancel command
        - get status (running, suspended etc)
        - check_timeout
"""

from __future__ import print_function
import sys
import time
import logging
import traceback
import shutit_global
import shutit_util


class ShutItBackgroundCommand(object):
	"""Background command in ShutIt
	"""
	def __init__(self,
	             sendspec,
	             shutit_obj):
		# Stub this with a simple command for now
		self.sendspec               = sendspec
		self.block_other_commands   = sendspec.block_other_commands
		self.retry                  = sendspec.retry
		self.tries                  = 0
		self.pid                    = None
		self.return_value           = None
		self.start_time             = None
		self.run_state              = 'N' # State as per ps man page, but 'C' == Complete, 'N' == not started, 'F' == failed, 'S' == sleeping/running, 'T' == timed out by ShutIt
		self.cwd                    = self.sendspec.shutit_pexpect_child.send_and_get_output(' command pwd', ignore_background=True)
		self.id                     = shutit_util.random_id()
		self.output_file            = '/tmp/shutit_background_' + self.id + '_output.log'
		self.exit_code_file         = '/tmp/shutit_background_' + self.id + '_exit_code_file.log'
		self.command_file           = '/tmp/shutit_background_' + self.id + '_command.log'
		if self.sendspec.run_in_background:
			# TODO: consider separating out into a simple send for the part that creates the command file, the cd and the output file. Perhaps send file first and run that in the background?
			self.sendspec.send          = ' set +m && { : $(echo "' + self.sendspec.original_send + '" >' + self.command_file + ' && command cd "' + self.cwd + '">' + self.output_file + ' && ' + self.sendspec.send + ' >>' + self.output_file + ' 2>&1; echo $? >' + self.exit_code_file + ') & } 2>/dev/null'
		self.shutit_obj             = shutit_obj


	def __str__(self):
		string = str(self.sendspec)
		string += '\n---- Background object BEGIN ----'
		string += '\n block_other_commands: ' + str(self.block_other_commands)
		string += '| cwd: ' + str(self.cwd)
		string += '| pid: ' + str(self.pid)
		string += '| retry: ' + str(self.retry)
		string += '| return_value: ' + str(self.return_value)
		string += '| run_state: ' + str(self.run_state)
		string += '| start_time: ' + str(self.start_time)
		string += '| tries: ' + str(self.tries)
		string += '|---- Background object END ----'
		return string


	def run_background_command(self):
		# reset object
		self.pid              = None
		self.return_value     = None
		self.run_state        = 'N'
		self.start_time = time.time() # record start time

		# run command
		self.tries            += 1
		if self.sendspec.run_in_background:
			## Required to reset terminal before a background send. (TODO: why?)
			#self.sendspec.shutit_pexpect_child.reset_terminal()
			# Run in the background
			self.sendspec.shutit_pexpect_child.quick_send(self.sendspec.send)
			# Put into an 'S' state as that means 'running'
			self.run_state        = 'S'
			# Required to reset terminal after a background send. (TODO: why?)
			self.sendspec.shutit_pexpect_child.reset_terminal()
			# record pid
			self.pid = self.sendspec.shutit_pexpect_child.send_and_get_output(" echo ${!}",ignore_background=True)
		else:
			# Run synchronously and mark complete
			# We need to set this to ignore background before we run it, so that
			# it does not block itself and end up in an infinite loop.
			self.sendspec.ignore_background = True
			self.sendspec.shutit_pexpect_child.send(self.sendspec)
			self.run_state = 'C'

		self.sendspec.started = True

		assert self.run_state in ('C','S','F'), shutit_util.print_debug()
		return True


	def check_background_command_state(self):
		self.shutit_obj.log('CHECKING background task: ' + self.sendspec.send + ', id: ' + self.id,level=logging.DEBUG)
		assert self.start_time is not None, shutit_util.print_debug()
		# Check the command has been started
		if not self.sendspec.started:
			assert self.run_state == 'N', shutit_util.print_debug()
			return self.run_state
		if self.run_state in ('C','F'):
			assert self.sendspec.started, shutit_util.print_debug()
			return self.run_state
		try:
			assert self.run_state in ('S',), shutit_util.print_debug(msg='State should be in S, is in fact: ' + self.run_state)
		except AssertionError:
			_, _, tb = sys.exc_info()
			traceback.print_tb(tb) # Fixed format
			tb_info = traceback.extract_tb(tb)
			_, line, _, text = tb_info[-1]
			shutit_global.shutit_global_object.shutit_print('An error occurred on line {} in statement {}'.format(line, text))
		# Update the run state.
		updated_run_state = self.sendspec.shutit_pexpect_child.send_and_get_output(""" command ps -o stat """ + self.pid + """ | command sed '1d' """, ignore_background=True)
		# Ensure we get the first character only, if one exists.
		if len(updated_run_state) > 0:
			# Task is unfinished.
			self.run_state = updated_run_state[0]
			updated_run_state = None
     		# state     The state is given by a sequence of characters, for example, ``RWNA''.  The first character indicates the run state of the process:
            #   I       Marks a process that is idle (sleeping for longer than about 20 seconds).
            #   R       Marks a runnable process.
            #   S       Marks a process that is sleeping for less than about 20 seconds.
            #   T       Marks a stopped process.
            #   U       Marks a process in uninterruptible wait.
            #   Z       Marks a dead process (a ``zombie'').
			if self.run_state in ('I','R','T','U','Z'):
				self.shutit_obj.log('background task run state: ' + self.run_state, level=logging.DEBUG)
				self.run_state = 'S'
			try:
				assert self.run_state in ('S',), shutit_util.print_debug(msg='State should be in S having gleaned from ps, is in fact: ' + self.run_state)
			except AssertionError:
				_, _, tb = sys.exc_info()
				traceback.print_tb(tb) # Fixed format
				tb_info = traceback.extract_tb(tb)
				_, line, _, text = tb_info[-1]
				shutit_global.shutit_global_object.shutit_print('An error occurred on line {} in statement {}'.format(line, text))
				shutit_global.shutit_global_object.shutit_print(self)
			# honour sendspec.timeout
			if self.sendspec.timeout is not None:
				current_time = time.time()
				time_taken = current_time - self.start_time
				if time_taken > self.sendspec.timeout:
					# We've timed out, kill with prejudice.
					self.sendspec.shutit_pexpect_child.quick_send(' kill -9 ' + self.pid)
					self.run_state = 'T'
			assert self.run_state in ('S','T'), shutit_util.print_debug()
			return self.run_state
		else:
			# Task is finished.
			self.run_state = 'C'
			self.shutit_obj.log('background task: ' + self.sendspec.send + ', id: ' + self.id + ' complete',level=logging.DEBUG)
			# Stop this from blocking other commands from here.
			assert self.return_value is None, shutit_util.print_debug(msg='check_background_command_state called with self.return_value already set?' + str(self))
			self.sendspec.shutit_pexpect_child.quick_send(' wait ' + self.pid)
			# Get the exit code.
			self.return_value = self.sendspec.shutit_pexpect_child.send_and_get_output(' cat ' + self.exit_code_file, ignore_background=True)
			# If the return value is deemed a failure:
			if self.return_value not in self.sendspec.exit_values:
				self.shutit_obj.log('background task: ' + self.sendspec.send + ' failed with exit code: ' + self.return_value, level=logging.DEBUG)
				self.shutit_obj.log('background task: ' + self.sendspec.send + ' failed with output: ' + self.sendspec.shutit_pexpect_child.send_and_get_output(' cat ' + self.output_file, ignore_background=True), level=logging.DEBUG)
				if self.retry > 0:
					self.shutit_obj.log('background task: ' + self.sendspec.send + ' retrying',level=logging.DEBUG)
					self.retry -= 1
					self.run_background_command()
					# recurse
					return self.check_background_command_state()
				else:
					self.shutit_obj.log('background task final failure: ' + self.sendspec.send + ' failed with exit code: ' + self.return_value, level=logging.DEBUG)
					self.run_state = 'F'
				assert self.run_state in ('C','F'), shutit_util.print_debug()
				return self.run_state
			else:
				# Task succeeded.
				self.shutit_obj.log('background task: ' + self.sendspec.send + ' succeeded with exit code: ' + self.return_value, level=logging.DEBUG)
			assert self.run_state in ('C',), shutit_util.print_debug()
			return self.run_state
		# Should never get here.
		assert False, shutit_util.print_debug()
