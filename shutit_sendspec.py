import logging
class ShutItSendSpec(object):
	"""Specification for arguments to send to shutit functions.
	"""
	def __init__(self,
	             send=None,
	             send_dict=None,
	             expect=None,
	             shutit_pexpect_child=None,
	             timeout=None,
	             check_exit=None,
	             fail_on_empty_before=True,
	             record_command=True,
	             exit_values=None,
	             echo=None,
	             escape=False,
	             check_sudo=True,
	             retry=3,
	             note=None,
	             assume_gnu=True,
	             follow_on_commands=None,
	             searchwindowsize=None,
	             maxread=None,
	             delaybeforesend=None,
	             secret=False,
	             nonewline=False,
	             user='root',
	             password=None,
	             is_ssh=None,
	             go_home=True,
	             prompt_prefix=None,
	             remove_on_match=None,
	             fail_on_fail=True,
	             loglevel=logging.INFO):
		"""Specification for arguments to send to shutit functions.
	
	
			@param send: String to send, ie the command being issued. If set to
			       None, we consume up to the expect string, which is useful if we
			       just matched output that came before a standard command that
			       returns to the prompt.
			@param send_dict: dict of sends and expects, eg: {'interim prompt:','some input','other prompt','some other input'}
			@param expect: String that we expect to see in the output. Usually a
			       prompt. Defaults to currently-set expect string (see
			       set_default_shutit_pexpect_session_expect)
			@param shutit_pexpect_child: pexpect child to issue command to.
			@param timeout: Timeout on response
			@param check_exit: Whether to check the shell exit code of the passed-in
			       command.  If the exit value was non-zero an error is thrown.
			       (default=None, which takes the currently-configured check_exit
			       value) See also fail_on_empty_before.
			@param fail_on_empty_before: If debug is set, fail on empty match output
			       string (default=True) If this is set to False, then we don't
			       check the exit value of the command.
			@param record_command: Whether to record the command for output at end.
			       As a safety measure, if the command matches any 'password's then
			       we don't record it.
			@param exit_values: Array of acceptable exit values as strings
			@param echo: Whether to suppress any logging output from pexpect to the
			       terminal or not.  We don't record the command if this is set to
			       False unless record_command is explicitly passed in as True.
			@param escape: Whether to escape the characters in a bash-friendly way,
			       ie $'\\Uxxxxxx'
			@param retry: Number of times to retry the command if the first attempt
			       doesn't work. Useful if going to the network
			@param note: If a note is passed in, and we are in walkthrough mode,
			       pause with the note printed
			@param assume_gnu: Assume the gnu version of commands, which are not in
			@param secret: Whether what is being sent is a secret
			@param nonewline: Whether to omit the newline from the send
			@param user: If logging in, user to use. Default is 'root'.
			@param user: If logging in, password to use. Default is 'root'.
			@param go_home: On logging in, whether to go to the home dir. Default is True.

			TODO: document
	             check_sudo=True,
	             follow_on_commands=None,
	             searchwindowsize=None,
	             maxread=None,
	             delaybeforesend=None,
	             is_ssh=None,
	             prompt_prefix=None,
	             remove_on_match=None,
	             loglevel=logging.INFO):
		"""
		self.send                    = send
		self.send_dict               = send_dict
		self.expect                  = expect
		self.shutit_pexpect_child    = shutit_pexpect_child
		self.timeout                 = timeout
		self.check_exit              = check_exit
		self.fail_on_empty_before    = fail_on_empty_before
		self.record_command          = record_command
		self.exit_values             = exit_values
		self.echo                    = echo
		self.escape                  = escape
		self.check_sudo              = check_sudo
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
		self.user                    = user
		self.password                = password
		self.is_ssh                  = is_ssh
		self.go_home                 = go_home
		self.prompt_prefix           = prompt_prefix
		self.remove_on_match         = remove_on_match
		self.fail_on_fail            = fail_on_fail
