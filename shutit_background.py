"""Manages ShutIt background command objects

send_background function:
    - returns reference to the command object
    - records command in memory in the shutit session
    - boolean for whether to allow other backgrounds in one session (default no)
    - there must be a newline (so no nonewline argument)
    - Object:
        - shutit.background_objects = [] - stored in shutit object
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
		shutit.send(command)
	#shutit_object        = None
	#pid                  = None
	#command              = None
	#return_value         = None
	#block_other_commands = None
	#timeout              = None
	#start_time           = None
	#background           = None
