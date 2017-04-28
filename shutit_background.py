"""Manages ShutIt background command objects

send_background function:
    - returns reference to the command object
    - records command in memory in the shutit session
    - boolean for whether to allow other backgrounds in one session (default no)
    - there must be a newline (so no nonewline argument)
    - Object:
        - pid
        - command
        - return value
        - other_background_commands_allowed
        - timeout?
        - start_time
    - options to:
        - cancel command
        - get status (running, suspended etc)
        - check_timeout

	- For send et al - if there are any ShutItBackgroundCommands still active, then the send is queued behind it as a background command.
		- Should a standard send create a Background command (and then immediately remove it when done?)
"""


class ShutItBackgroundCommand(object):
	"""Background command in ShutIt
	"""
	def __init__(self,
	             shutit,
	             command,
	             block_other_commands=True,
	             timeout=None,
	             background=True):
		# Stub this with a simple command for now
		self.shutit               = shutit
		self.command              = command
		self.block_other_commands = block_other_commands
		self.timeout              = timeout
		self.background           = background
		self.pid                  = None
		self.return_value         = None
		self.start_time           = None
		shutit.background_objects.append(self)
		shutit.send(command)
