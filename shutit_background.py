r"""Represents a ShutIt background command.

    - options to:
        - cancel command
        - get status (running, suspended etc)
        - check_timeout

     state     The state is given by a sequence of characters, for example, ``RWNA''.  The first character indicates the run state of the process:

               I       Marks a process that is idle (sleeping for longer than about 20 seconds).
               R       Marks a runnable process.
               S       Marks a process that is sleeping for less than about 20 seconds.
               T       Marks a stopped process.
               U       Marks a process in uninterruptible wait.
               Z       Marks a dead process (a ``zombie'').


               Additional characters after these, if any, indicate additional state information:

               +       The process is in the foreground process group of its control terminal.
               <       The process has raised CPU scheduling priority.
               >       The process has specified a soft limit on memory requirements and is currently exceeding that limit; such a process is (necessarily) not swapped.
               A       the process has asked for random page replacement (VA_ANOM, from vadvise(2), for example, lisp(1) in a garbage collect).
               E       The process is trying to exit.
               L       The process has pages locked in core (for example, for raw I/O).
               N       The process has reduced CPU scheduling priority (see setpriority(2)).
               S       The process has asked for FIFO page replacement (VA_SEQL, from vadvise(2), for example, a large image processing program using virtual memory to sequentially
                       address voluminous data).
               s       The process is a session leader.
               V       The process is suspended during a vfork(2).
               W       The process is swapped out.
               X       The process is being traced or debugged.

ps -o stat= | sed 's/^\(.\)\(.*\)/\1/'
"""

import time
import logging
import shutit_global
import shutit_util


class ShutItBackgroundCommand(object):
	"""Background command in ShutIt
	"""
	def __init__(self,
	             sendspec):
		# Stub this with a simple command for now
		self.sendspec             = sendspec
		self.block_other_commands = sendspec.block_other_commands
		self.retry                = sendspec.retry
		self.tries                = 0
		self.pid                  = None
		self.return_value         = None
		self.start_time           = None
		self.run_state            = 'N' # State as per ps man page, but 'C' == Complete, 'N' == not started, 'F' == failed
		self.cwd                  = self.sendspec.shutit_pexpect_child.send_and_get_output(' command pwd')
		self.id                   = shutit_util.random_id()
		self.output_file          = '/tmp/shutit_background_output_' + self.id + '.log'
		self.exit_code_file       = '/tmp/shutit_background_exit_code_file_' + self.id + '.log'
		self.sendspec.send        = ' set +m && { : $(command cd ' + self.cwd + '>' + self.output_file + ' && ' + self.sendspec.send + ' >>' + self.output_file + ' 2>&1; echo $? >' + self.exit_code_file + ') & } 2>/dev/null'


	def __str__(self):
		string = '\nSendspec: '
		string += str(self.sendspec)
		string += '\nBackground object: '
		string += '\nblock_other_commands: ' + str(self.block_other_commands)
		string += '\ncwd:                  ' + str(self.cwd)
		string += '\npid:                  ' + str(self.pid)
		string += '\nretry:                ' + str(self.block_other_commands)
		string += '\nreturn_value:         ' + str(self.return_value)
		string += '\nrun_state:            ' + str(self.run_state)
		string += '\nstart_time:           ' + str(self.start_time)
		return string


	def run_background_command(self):
		# reset object
		self.pid              = None
		self.return_value     = None
		self.run_state        = 'N'
		self.start_time = time.localtime() # record start time

		# run command
		self.tries            += 1
		self.sendspec.shutit_pexpect_child.quick_send(self.sendspec.send)

		self.sendspec.started = True

		# Put into an 'S' state as that seems to mean 'running'
		self.run_state        = 'S'
		# Required to reset terminal after a background send. (TODO: why?)
		self.sendspec.shutit_pexpect_child.reset_terminal()
		# record pid
		self.pid = self.sendspec.shutit_pexpect_child.send_and_get_output(" echo ${!}")
		return True


	def check_background_command_state(self):
		shutit_pexpect_child = self.sendspec.shutit_pexpect_child
		# Check the command has been started
		if not self.sendspec.started:
			return self.run_state
		self.run_state = shutit_pexpect_child.send_and_get_output(""" command ps -o stat """ + self.pid + """ | command sed '1d' """)
		# If the job is complete, collect the return value
		if self.run_state == '':
			shutit_global.shutit_global_object.log('background task: ' + self.sendspec.send + ' complete')
			self.run_state = 'C'
			# Stop this from blocking other commands from here.
			self.block_other_commands = False
		if isinstance(self.run_state,str) and self.run_state == 'C' and self.return_value is None:
			shutit_pexpect_child.quick_send(' wait ' + self.pid)
			self.return_value = shutit_pexpect_child.send_and_get_output(' cat ' + self.exit_code_file)
			# TODO: options for return values
			if self.return_value != '0':
				shutit_global.shutit_global_object.log('background task: ' + self.sendspec.send + ' failed with error code: ' + self.return_value, level=logging.DEBUG)
				shutit_global.shutit_global_object.log('background task: ' + self.sendspec.send + ' failed with output: ' + self.sendspec.shutit_pexpect_child.send_and_get_output(' cat ' + self.output_file), level=logging.DEBUG)
				if self.retry > 0:
					shutit_global.shutit_global_object.log('background task: ' + self.sendspec.send + ' retrying',level=logging.DEBUG)
					self.retry -= 1
					self.run_background_command()
					# recurse
					return self.check_background_command_state()
				else:
					shutit_global.shutit_global_object.log('background task final failure: ' + self.sendspec.send + ' failed with error code: ' + self.return_value, level=logging.DEBUG)
					self.run_state = 'F'
			else:
				shutit_global.shutit_global_object.log('background task: ' + self.sendspec.send + ' succeeded with error code: ' + self.return_value, level=logging.DEBUG)
		if isinstance(self.run_state,str) and self.run_state == 'C' and self.return_value is not None:
			pass
		# TODO: honour sendspec.timeout
		return self.run_state
