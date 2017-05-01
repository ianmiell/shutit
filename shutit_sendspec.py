import logging

class ShutItSendSpec(object):
	"""Specification for arguments to send to shutit functions.
	"""
	def __init__(self,
	             shutit_pexpect_child,
	             send=None,
	             send_dict=None,
	             expect=None,
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
	             ignore_background=False,
	             run_in_background=False,
	             block_other_commands=True,
	             loglevel=logging.INFO):
		"""Specification for arguments to send to shutit functions.

			@param send:                 String to send, ie the command being issued. If set to
			                             None, we consume up to the expect string, which is useful if we
			                             just matched output that came before a standard command that
			                             returns to the prompt.
			@param send_dict:            dict of sends and expects, eg:
			                             {'interim prompt:','some input','other prompt','some other input'}
			@param expect:               String that we expect to see in the output. Usually a
			                             prompt. Defaults to currently-set expect string (see
			                             set_default_shutit_pexpect_session_expect)
			@param shutit_pexpect_child: pexpect child to issue command to.
			@param timeout:              Timeout on response
			@param check_exit:           Whether to check the shell exit code of the passed-in
			                             command.  If the exit value was non-zero an error is thrown.
			                             (default=None, which takes the currently-configured check_exit
			                             value) See also fail_on_empty_before.
			@param fail_on_empty_before: If debug is set, fail on empty match output
			                             string (default=True) If this is set to False, then we don't
			                             check the exit value of the command.
			@param record_command:       Whether to record the command for output at end.
			                             As a safety measure, if the command matches any 'password's then
			                             we don't record it.
			@param exit_values:          Array of acceptable exit values as strings
			@param echo:                 Whether to suppress any logging output from pexpect to the
			                             terminal or not.  We don't record the command if this is set to
			                             False unless record_command is explicitly passed in as True.
			@param escape:               Whether to escape the characters in a bash-friendly way, eg $'\\Uxxxxxx'
			@param retry:                Number of times to retry the command if the first attempt
			                             doesn't work. Useful if going to the network
			@param note:                 If a note is passed in, and we are in walkthrough mode,
			                             pause with the note printed
			@param assume_gnu:           Assume the gnu version of commands, which are not in
			@param secret:               Whether what is being sent is a secret
			@param nonewline:            Whether to omit the newline from the send
			@param user:                 If logging in, user to use. Default is 'root'.
			@param user:                 If logging in, password to use. Default is 'root'.
			@param go_home:              On logging in, whether to go to the home dir. Default is True.
			@param ignore_background:    Whether to block if there are background tasks
			                             running in this session that are block, or ignore ALL
			                             background tasks and run anyway. Default is False
			@param run_in_background:    Whether to run in the background
			@param block_other_commands: Whether to block other commands from running
			                             (unless ignore_background is set on those other commands)

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
		self.ignore_background       = ignore_background
		self.run_in_background       = run_in_background
		self.block_other_commands    = block_other_commands

		# Setup/checking
		self.started                 = False
		if check_exit and run_in_background:
			check_exit = False
		if send_dict and run_in_background:
			# run_in_background and send_dict make no sense
			assert False

	def __str__(self):
		# TODO: extend to all
		string = ''
		string += '\nsend                    = ' + str(self.send)
		if self.send[-1] != '\n':
			string += '\n'
		string += 'ignore_background         = ' + str(self.ignore_background)
		string += '\nrun_in_background       = ' + str(self.run_in_background)
		string += '\nstarted                 = ' + str(self.started)
		string += '\nexpect                  = ' + str(self.expect)
		string += '\nnonewline               = ' + str(self.nonewline)
		string += '\n send_dict              = ' + str(self.send_dict)
		string += '\n expect                 = ' + str(self.expect)
		string += '\n timeout                = ' + str(self.timeout)
		string += '\n check_exit             = ' + str(self.check_exit)
		string += '\n fail_on_empty_before   = ' + str(self.fail_on_empty_before)
		string += '\n record_command         = ' + str(self.record_command)
		string += '\n exit_values            = ' + str(self.exit_values)
		string += '\n echo                   = ' + str(self.echo)
		string += '\n escape                 = ' + str(self.escape)
		string += '\n check_sudo             = ' + str(self.check_sudo)
		string += '\n retry                  = ' + str(self.retry)
		string += '\n note                   = ' + str(self.note)
		string += '\n assume_gnu             = ' + str(self.assume_gnu)
		string += '\n follow_on_commands     = ' + str(self.follow_on_commands)
		string += '\n searchwindowsize       = ' + str(self.searchwindowsize)
		string += '\n maxread                = ' + str(self.maxread)
		string += '\n delaybeforesend        = ' + str(self.delaybeforesend)
		string += '\n secret                 = ' + str(self.secret)
		string += '\n loglevel               = ' + str(self.loglevel)
		string += '\n user                   = ' + str(self.user)
		string += '\n password               = ' + str(self.password)
		string += '\n is_ssh                 = ' + str(self.is_ssh)
		string += '\n go_home                = ' + str(self.go_home)
		string += '\n prompt_prefix          = ' + str(prompt_prefix)
		string += '\n remove_on_match        = ' + str(remove_on_match)
		string += '\n fail_on_fail           = ' + str(fail_on_fail)
		string += '\n ignore_background      = ' + str(ignore_background)
		string += '\n run_in_background      = ' + str(run_in_background)
		string += '\n block_other_commands   = ' + str(block_other_commands)
		return string
