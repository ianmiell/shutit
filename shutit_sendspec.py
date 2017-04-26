import logging
class ShutItSendSpec(object):
	"""Specification for arguments to send to shutit functions.
	"""
	def __init__(self,
	             send,
	             expect=None,
	             shutit_pexpect_child=None,
	             timeout=None,
	             check_exit=None,
	             fail_on_empty_before=True,
	             record_command=True,
	             exit_values=None,
	             echo=None,
	             escape=False,
	             retry=3,
	             note=None,
	             assume_gnu=True,
	             follow_on_commands=None,
	             searchwindowsize=None,
	             maxread=None,
	             delaybeforesend=None,
	             secret=False,
	             nonewline=False,
	             loglevel=logging.INFO):
		self.send                    = send
		self.expect                  = expect
		self.shutit_pexpect_child    = shutit_pexpect_child
		self.timeout                 = timeout
		self.check_exit              = check_exit
		self.fail_on_empty_before    = fail_on_empty_before
		self.record_command          = record_command
		self.exit_values             = exit_values
		self.echo                    = echo
		self.escape                  = escape
		self.retry                   = retry
		self.note                    = note
		self.assume_gnu              = assume_gnu
		self.follow_on_commands      = follow_on_commands
		self.searchwindowsize        = searchwindowsize
		self.maxread                 = maxread
		self.delaybeforesend         = delaybeforesend
		self.secret                  = secret
		self.nonewline               = nonewline
		self.loglevel                = loglevel
