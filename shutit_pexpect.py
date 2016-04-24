#The MIT License (MIT)
#
#Copyright (C) 2014 OpenBet Limited
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of
#this software and associated documentation files (the "Software"), to deal in
#the Software without restriction, including without limitation the rights to
#use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#of the Software, and to permit persons to whom the Software is furnished to do
#so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFeWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#ITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.
"""Represents and manages a pexpect object for ShutIt's purposes.
"""

import pexpect
import shutit_util
import shutit_setup
import logging
import string


class ShutItPexpectSession(object):

	def __init__(self,
				 shutit,
	             pexpect_session_id,
				 command,
	             args=[],
				 timeout=300,
	             maxread=2000,
	             searchwindowsize=None,
	             logfile=None,
	             cwd=None,
	             env=None,
	             ignore_sighup=False,
	             echo=True,
	             preexec_fn=None,
	             encoding=None,
	             codec_errors='strict',
	             dimensions=None,
	             delaybeforesend=0):
		"""spawn a child, and manage the delaybefore send setting to 0
		"""
		self.check_exit          = True
		self.default_expect      = [shutit.cfg['expect_prompts']['base_prompt']]
		self.pexpect_session_id  = pexpect_session_id
		self.login_stack         = []
		self.shutit_object       = shutit
		self.pexpect_child       = self._spawn_child(command=command,
		                                             args=args,
		                                             timeout=timeout,
		                                             maxread=maxread,
		                                             searchwindowsize=searchwindowsize,
		                                             logfile=logfile,
		                                             cwd=cwd,
		                                             env=env,
		                                             ignore_sighup=ignore_sighup,
		                                             echo=echo,
		                                             preexec_fn=preexec_fn,
		                                             encoding=encoding,
		                                             codec_errors=codec_errors,
		                                             dimensions=dimensions,
		                                             delaybeforesend=delaybeforesend)


	def _spawn_child(self,
					command,
					args=[],
					timeout=30,
					maxread=2000,
					searchwindowsize=None,
					logfile=None,
					cwd=None,
					env=None,
					ignore_sighup=False,
					echo=True,
					preexec_fn=None,
					encoding=None,
					codec_errors='strict',
					dimensions=None,
					delaybeforesend=0):
		"""spawn a child, and manage the delaybefore send setting to 0
		"""
		pexpect_child = pexpect.spawn(command,
		                              args=args,
		                              timeout=timeout,
		                              maxread=maxread,
		                              searchwindowsize=searchwindowsize,
		                              logfile=logfile,
		                              cwd=cwd,
		                              env=env,
		                              ignore_sighup=ignore_sighup,
		                              echo=echo,
		                              preexec_fn=preexec_fn,
		                              encoding=encoding,
		                              codec_errors=codec_errors,
		                              dimensions=dimensions)
		pexpect_child.delaybeforesend=delaybeforesend
		self.shutit_object.log('sessions before: ' + str(self.shutit_object.shutit_pexpect_sessions),level=logging.DEBUG)
		self.shutit_object.shutit_pexpect_sessions.update({self.pexpect_session_id:self})
		self.shutit_object.log('sessions after: ' + str(self.shutit_object.shutit_pexpect_sessions),level=logging.DEBUG)
		return pexpect_child




	def login(self,
			  user='root',
			  command='su -',
			  password=None,
			  prompt_prefix=None,
			  expect=None,
			  timeout=180,
			  escape=False,
			  note=None,
			  go_home=True,
			  delaybeforesend=0.05,
			  loglevel=logging.DEBUG):
		"""Logs the user in with the passed-in password and command.
		Tracks the login. If used, used logout to log out again.
		Assumes you are root when logging in, so no password required.
		If not, override the default command for multi-level logins.
		If passwords are required, see setup_prompt() and revert_prompt()

		@param user:          User to login with. Default: root
		@param command:       Command to login with. Default: "su -"
		@param escape:        See send(). We default to true here in case
		                      matches an expect we add.
		@param password:      Password.
		@param prompt_prefix: Prefix to use in prompt setup.
		@param expect:        See send()
		@param timeout:		  How long to wait for a response. Default: 20.
		@param note:          See send()
		@param go_home:       Whether to automatically cd to home.

		@type user:           string
		@type command:        string
		@type password:       string
		@type prompt_prefix:  string
		@type timeout:        integer
		"""
		# We don't get the default expect here, as it's either passed in, or a base default regexp.
		r_id = shutit_util.random_id()
		if prompt_prefix == None:
			prompt_prefix = r_id
		cfg = self.shutit_object.cfg
		# Be helpful.
		if ' ' in user:
			self.shutit_object.fail('user has space in it - did you mean: login(command="' + user + '")?')
		if cfg['build']['delivery'] == 'bash' and command == 'su -':
			# We want to retain the current working directory
			command = 'su'
		if command == 'su -' or command == 'su' or command == 'login':
			send = command + ' ' + user
		else:
			send = command
		if expect == None:
			login_expect = cfg['expect_prompts']['base_prompt']
		else:
			login_expect = expect
		# We don't fail on empty before as many login programs mess with the output.
		# In this special case of login we expect either the prompt, or 'user@' as this has been seen to work.
		general_expect = [login_expect]
		# Add in a match if we see user+ and then the login matches. Be careful not to match against 'user+@...password:'
		general_expect = general_expect + [user+'@.*'+'[@#$]']
		# If not an ssh login, then we can match against user + @sign because it won't clash with 'user@adasdas password:'
		if not string.find(command,'ssh') == 0:
			general_expect = general_expect + [user+'@']
			general_expect = general_expect + ['.*[@#$]']
		if user == 'bash' and command == 'su -':
			self.shutit_object.log('WARNING! user is bash - if you see problems below, did you mean: login(command="' + user + '")?',level=loglevel.WARNING)
		self.shutit_object._handle_note(note,command=command + ', as user: "' + user + '"',training_input=send)
		# r'[^t] login:' - be sure not to match 'last login:'
		self.shutit_object.multisend(send,{'ontinue connecting':'yes','assword':password,r'[^t] login:':password},expect=general_expect,check_exit=False,timeout=timeout,fail_on_empty_before=False,escape=escape)
		if prompt_prefix != None:
			self.setup_prompt(r_id,prefix=prompt_prefix)
		else:
			self.setup_prompt(r_id)
		if go_home:
			self.shutit_object.send('cd',shutit_pexpect_child=self.pexpect_child,check_exit=False, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
		self.login_stack_append(r_id)
		self.shutit_object._handle_note_after(note=note)


	def logout(self,
			   expect=None,
			   command='exit',
			   note=None,
			   timeout=5,
			   delaybeforesend=0,
			   loglevel=logging.DEBUG):
		"""Logs the user out. Assumes that login has been called.
		If login has never been called, throw an error.

			@param shutit_pexpect_child:		   See send()
			@param expect:		  See send()
			@param command:		 Command to run to log out (default=exit)
			@param note:			See send()
		"""
		old_expect = expect or self.default_expect
		self.shutit_object._handle_note(note,training_input=command)
		if len(self.login_stack):
			current_prompt_name = self.login_stack.pop()
			if len(self.login_stack):
				old_prompt_name	 = self.login_stack[-1]
				# TODO: sort out global expect_prompts
				self.default_expect = self.shutit_object.cfg['expect_prompts'][old_prompt_name]
			else:
				# If none are on the stack, we assume we're going to the root prompt
				# set up in shutit_setup.py
				self.shutit_object.set_default_shutit_pexpect_session_expect()
		else:
			self.fail('Logout called without corresponding login', throw_exception=False)
		# No point in checking exit here, the exit code will be
		# from the previous command from the logged in session
		self.shutit_object.send(command, shutit_pexpect_child=self.pexpect_child, expect=expect, check_exit=False, timeout=timeout,echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
		self.shutit_object._handle_note_after(note=note)


	def login_stack_append(self,
						   r_id,
						   expect=None,
						   new_user=''):
		child = self.pexpect_child
		self.login_stack.append(r_id)


	def setup_prompt(self,
	                 prompt_name,
	                 prefix='default',
	                 delaybeforesend=0,
	                 loglevel=logging.DEBUG):
		"""Use this when you've opened a new shell to set the PS1 to something
		sane. By default, it sets up the default expect so you don't have to
		worry about it and can just call shutit.send('a command').
		
		If you want simple login and logout, please use login() and logout()
		within this module.
		
		Typically it would be used in this boilerplate pattern::
		
		    shutit.send('su - auser', expect=shutit.cfg['expect_prompts']['base_prompt'], check_exit=False)
		    shutit.setup_prompt('tmp_prompt')
		    shutit.send('some command')
		    [...]
		    shutit.set_default_shutit_pexpect_session_expect()
		    shutit.send('exit')
		
		This function is assumed to be called whenever there is a change
		of environment.
		
		@param prompt_name:         Reference name for prompt.
		@param prefix:              Prompt prefix. Default: 'default'
		@param shutit_pexpect_child:               See send()
		                            to the new prompt. Default: True
		
		@type prompt_name:          string
		@type prefix:               string
		"""
		local_prompt = prefix + '#' + shutit_util.random_id() + '> '
		cfg = self.shutit_object.cfg
		cfg['expect_prompts'][prompt_name] = local_prompt
		# Set up the PS1 value.
		# Unset the PROMPT_COMMAND as this can cause nasty surprises in the output.
		# Set the cols value, as unpleasant escapes are put in the output if the
		# input is > n chars wide.
		# The newline in the expect list is a hack. On my work laptop this line hangs
		# and times out very frequently. This workaround seems to work, but I
		# haven't figured out why yet - imiell.
		self.shutit_object.send((" export SHUTIT_BACKUP_PS1_%s=$PS1 && PS1='%s' && unset PROMPT_COMMAND && stty sane && stty cols " + str(cfg['build']['stty_cols'])) % (prompt_name, local_prompt), expect=['\r\n' + cfg['expect_prompts'][prompt_name]], fail_on_empty_before=False, timeout=5, shutit_pexpect_child=self.pexpect_child, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
		self.shutit_object.log('Resetting default expect to: ' + cfg['expect_prompts'][prompt_name],level=logging.DEBUG)
		self.default_expect = cfg['expect_prompts'][prompt_name]
		# Ensure environment is set up OK.
		self.setup_environment(prefix)


	def revert_prompt(self,
	                  old_prompt_name,
	                  new_expect=None,
	                  delaybeforesend=0,
	                  shutit_pexpect_child=None):
		"""Reverts the prompt to the previous value (passed-in).
		
		It should be fairly rare to need this. Most of the time you would just
		exit a subshell rather than resetting the prompt.
		
		    - old_prompt_name -
		    - new_expect      -
		    - child           - See send()
		"""
		expect = expect or self.default_expect
		#     v the space is intentional, to avoid polluting bash history.
		self.shutit_object.send((' PS1="${SHUTIT_BACKUP_PS1_%s}" && unset SHUTIT_BACKUP_PS1_%s') % (old_prompt_name, old_prompt_name), expect=expect, check_exit=False, fail_on_empty_before=False, echo=False, loglevel=logging.DEBUG,delaybeforesend=delaybeforesend)
		if not new_expect:
			self.shutit_object.log('Resetting default expect to default',level=logging.DEBUG)
			self.set_default_shutit_pexpect_session_expect()
		self.setup_environment()


	def send(self, string, delaybeforesend=0):
		prev_delaybeforesend = self.pexpect_child.delaybeforesend
		self.pexpect_child.delaybeforesend = delaybeforesend
		self.pexpect_child.send(string)
		self.pexpect_child.delaybeforesend = prev_delaybeforesend


	def sendline(self, string, delaybeforesend=0):
		self.send(string+'\n',delaybeforesend=delaybeforesend)


	def expect(self,
			   expect,
			   timeout=None):
		"""Handle child expects, with EOF and TIMEOUT handled
		"""
		if type(expect) == str:
			expect = [expect]
		return self.pexpect_child.expect(expect + [pexpect.TIMEOUT] + [pexpect.EOF], timeout=timeout)


	def replace_container(self,
	                      new_target_image_name,
	                      delaybeforesend=0):
		"""Replaces a container. Assumes we are in Docker context
		"""
		shutit = self.shutit_object
		cfg = shutit.cfg
		shutit.log('Replacing container, please wait...',level=logging.INFO)

		# Destroy existing container.
		conn_module = None
		for mod in shutit.conn_modules:
			if mod.module_id == cfg['build']['conn_module']:
				conn_module = mod
				break
		if conn_module is None:
			shutit.fail('''Couldn't find conn_module ''' + cfg['build']['conn_module'])
		container_id = cfg['target']['container_id']
		conn_module.destroy_container(self.shutit_object, 'host_child', 'target_child', container_id)
		
		# Start up a new container.
		cfg['target']['docker_image'] = new_target_image_name
		target_child = conn_module.start_container(shutit,self.pexpect_session_id)
		conn_module.setup_target_child(shutit, target_child)

		# set the target child up
		self.pexpect_child = target_child
		shutit.log('z',level=logging.DEBUG)
		shutit.log(self.default_expect,level=logging.DEBUG)
		
		# set up the prompt on startup
		self.default_expect = [cfg['expect_prompts']['base_prompt']]
		self.setup_prompt('root')
		self.login_stack_append('root')
		# Log in and let ShutIt take care of the prompt.
		# Don't go home in case the workdir is different in the docker image!
		self.login(command='bash',go_home=False)
		return


	def whoami(self,
	           expect=None,
	           note=None,
	           delaybeforesend=0,
	           loglevel=logging.DEBUG):
		"""Returns the current user by executing "whoami".

		@param shutit_pexpect_child:    See send()
		@param expect:   See send()
		@param note:     See send()

		@return: the output of "whoami"
		@rtype: string
		"""
		self.shutit_object._handle_note(note)
		res = self.shutit_object.send_and_get_output('whoami',shutit_pexpect_child=self.pexpect_child,echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend).strip()
		self.shutit_object._handle_note_after(note=note)
		return res




	#TODO: move setup_environment - create environment object
	#TODO: review items in cfg and see if they make more sense in the pexpect object
	#TODO: replace 'target' in cfg


	def setup_environment(self,
	                      prefix,
	                      delaybeforesend=0,
	                      loglevel=logging.DEBUG):
		"""If we are in a new environment then set up a new data structure.
		A new environment is a new machine environment, whether that's
		over ssh, docker, whatever.
		If we are not in a new environment ensure the env_id is correct.
		Returns the environment id every time.
		"""
		# Set this to be the default session.
		self.shutit_object.set_default_shutit_pexpect_session(self)
		cfg = self.shutit_object.cfg
		environment_id_dir = cfg['build']['shutit_state_dir'] + '/environment_id'
		if self.shutit_object.file_exists(environment_id_dir,directory=True):
			files = self.shutit_object.ls(environment_id_dir)
			if len(files) != 1 or type(files) != list:
				if len(files) == 2 and (files[0] == 'ORIGIN_ENV' or files[1] == 'ORIGIN_ENV'):
					for f in files:
						if f != 'ORIGIN_ENV':
							environment_id = f
							cfg['build']['current_environment_id'] = environment_id
							# Workaround for CygWin terminal issues. If the envid isn't in the cfg item
							# Then crudely assume it is. This will drop through and then assume we are in the origin env.
							try:
								cfg['environment'][cfg['build']['current_environment_id']]
							except Exception:
								cfg['build']['current_environment_id'] = 'ORIGIN_ENV'
							break
				else:
					# See comment above re: cygwin.
					if self.shutit_object.file_exists('/cygdrive'):
						cfg['build']['current_environment_id'] = 'ORIGIN_ENV'
					else:
						self.shutit_object.fail('Wrong number of files in environment_id_dir: ' + environment_id_dir)
			else:
				if self.shutit_object.file_exists('/cygdrive'):
					environment_id = 'ORIGIN_ENV'
				else:
					environment_id = files[0]
			if cfg['build']['current_environment_id'] != environment_id:
				# Clean out any trace of this new environment, and return the already-existing one.
				self.shutit_object.send(' rm -rf ' + environment_id_dir + '/environment_id/' + environment_id, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
				return cfg['build']['current_environment_id']
			if not environment_id == 'ORIGIN_ENV':
				return environment_id
		# Origin environment is a special case.
		if prefix == 'ORIGIN_ENV':
			environment_id = prefix
		else:
			environment_id = shutit_util.random_id()
		cfg['build']['current_environment_id']                             = environment_id
		cfg['environment'][environment_id] = {}
		# Directory to revert to when delivering in bash and reversion to directory required.
		cfg['environment'][environment_id]['module_root_dir']              = '/'
		cfg['environment'][environment_id]['modules_installed']            = [] # has been installed (in this build)
		cfg['environment'][environment_id]['modules_not_installed']        = [] # modules _known_ not to be installed
		cfg['environment'][environment_id]['modules_ready']                = [] # has been checked for readiness and is ready (in this build)
		# Installed file info
		cfg['environment'][environment_id]['modules_recorded']             = []
		cfg['environment'][environment_id]['modules_recorded_cache_valid'] = False
		cfg['environment'][environment_id]['setup']                        = False
		# Exempt the ORIGIN_ENV from getting distro info
		if prefix != 'ORIGIN_ENV':
			self.shutit_object.get_distro_info(environment_id)
		fname = environment_id_dir + '/' + environment_id
		self.shutit_object.send(' mkdir -p ' + environment_id_dir + ' && chmod -R 777 ' + cfg['build']['shutit_state_dir_base'] + ' && touch ' + fname, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
		cfg['environment'][environment_id]['setup']                        = True
		return environment_id


