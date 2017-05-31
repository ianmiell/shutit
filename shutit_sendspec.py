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
	             user=None,
	             password=None,
	             is_ssh=None,
	             go_home=True,
	             prompt_prefix=None,
	             remove_on_match=None,
	             fail_on_fail=True,
	             ignore_background=False,
	             run_in_background=False,
	             block_other_commands=True,
	             wait_cadence=2,
	             loglevel=logging.INFO):
		"""Specification for arguments to send to shutit functions.

			@param send:                 String to send, ie the command being issued. If set to
			                             None, we consume up to the expect string, which is useful if we
			                             just matched output that came before a standard command that
			                             returns to the prompt.
			@param send_dict:            dict of sends and expects, eg:
			                             {'interim prompt:',['some input',False],'input password:':['mypassword',True]}
			                             Note that the boolean indicates whether the match results in the removal of the send dict expects from the interaction and assumes a prompt follows.
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
			@param check_sudo:           Check whether we have sudo available and if we already have sudo rights
                                         cached.
			@param retry:                Number of times to retry the command if the first attempt
			                             doesn't work. Useful if going to the network
			@param note:                 If a note is passed in, and we are in walkthrough mode,
			                             pause with the note printed
			@param assume_gnu:           Assume the gnu version of commands, which are not in
			@param follow_on_commands:   TODO
			@param searchwindowsize:     Passed into pexpect session
			@param maxread:              Passed into pexpect session
			@param delaybeforesend:      Passed into pexpect session
			@param secret:               Whether what is being sent is a secret
			@param nonewline:            Whether to omit the newline from the send
			@param user:                 If logging in, user to use. Default is 'root'.
			@param password:             If logging in, password to use. Default is 'root'.
			@param is_ssh:               Indicates whether the login is an ssh one if it is not an ssh command
			@param go_home:              On logging in, whether to go to the home dir. Default is True.
			@param prompt_prefix:        Override of random prompt prefix created by prompt setup.
			@param remove_on_match:      If the item matches, remove the send_dict from future expects (eg if
                                         it's a password). This makes the 'am I logged in yet?' checking more robust.
			@param ignore_background:    Whether to block if there are background tasks
			                             running in this session that are block, or ignore ALL
			                             background tasks and run anyway. Default is False.
			@param run_in_background:    Whether to run in the background
			@param block_other_commands: Whether to block other commands from running
			                             (unless ignore_background is set on those other commands).
			                             Default is True.
			@param wait_cadence:         If blocked and waiting on a background tasks, wait this
			                             number of seconds before re-checking. Default is 2.
			@param loglevel:             Log level at which to operate.
		"""
		self.send                    = send
		self.original_send           = send
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
		self.wait_cadence            = wait_cadence

		# BEGIN Setup/checking
		self.started                 = False
		if self.check_exit and self.run_in_background:
			self.check_exit = False
		#if send_dict and run_in_background:
			#shutit_global.shutit_global_object.log('run_in_background and send_dict make no sense',level=logging.CRITICAL)
			#assert False, ''
		# END Setup/checking

		# send_dict can come in with items that are: val:string, or val:[string,boolean]
		# ensure they end up as the latter, defaulting to false.
		if self.send_dict is not None:
			assert isinstance(self.send_dict, dict)
			for key in self.send_dict:
				val = self.send_dict[key]
				assert isinstance(val,(str,list))
				if isinstance(val,str):
					self.send_dict.update({key:[val,False]})
				elif isinstance(val,list):
					assert len(val) == 2
				else:
					assert False, 'send_dict check should not get here'

		if self.exit_values is None:
			self.exit_values = ['0',]


	def __str__(self):
		string = '\n---- Sendspec object ----'
		string += '\nassume_gnu              = ' + str(self.assume_gnu)
		string += '\nblock_other_commands    = ' + str(self.block_other_commands)
		string += '\ncheck_exit              = ' + str(self.check_exit)
		string += '\ncheck_sudo              = ' + str(self.check_sudo)
		string += '\ndelaybeforesend         = ' + str(self.delaybeforesend)
		string += '\necho                    = ' + str(self.echo)
		string += '\nescape                  = ' + str(self.escape)
		string += '\nexit_values             = ' + str(self.exit_values)
		string += '\nexpect                  = ' + str(self.expect)
		string += '\nfail_on_empty_before    = ' + str(self.fail_on_empty_before)
		string += '\nfail_on_fail            = ' + str(self.fail_on_fail)
		string += '\nfollow_on_commands      = ' + str(self.follow_on_commands)
		string += '\ngo_home                 = ' + str(self.go_home)
		string += '\nignore_background       = ' + str(self.ignore_background)
		string += '\nis_ssh                  = ' + str(self.is_ssh)
		string += '\nloglevel                = ' + str(self.loglevel)
		string += '\nmaxread                 = ' + str(self.maxread)
		string += '\nnonewline               = ' + str(self.nonewline)
		string += '\nnote                    = ' + str(self.note)
		string += '\noriginal_send           = ' + str(self.original_send)
		if self.original_send[-1] != '\n':
			string += '\n'
		string += 'password                = ' + str(self.password)
		string += '\nprompt_prefix           = ' + str(self.prompt_prefix)
		string += '\nrecord_command          = ' + str(self.record_command)
		string += '\nremove_on_match         = ' + str(self.remove_on_match)
		string += '\nretry                   = ' + str(self.retry)
		string += '\nrun_in_background       = ' + str(self.run_in_background)
		string += '\nsearchwindowsize        = ' + str(self.searchwindowsize)
		string += '\nsecret                  = ' + str(self.secret)
		string += '\nsend                    = ' + str(self.send)
		if self.send[-1] != '\n':
			string += '\n'
		string += 'send_dict               = ' + str(self.send_dict)
		string += '\nstarted                 = ' + str(self.started)
		string += '\ntimeout                 = ' + str(self.timeout)
		string += '\nuser                    = ' + str(self.user)
		string += '\nwait_cadence            = ' + str(self.wait_cadence)
		string += '\n----                 ----'
		return string
