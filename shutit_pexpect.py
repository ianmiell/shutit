# The MIT License (MIT)
# 
# Copyright (C) 2014 OpenBet Limited
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# ITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Represents and manages a pexpect object for ShutIt's purposes.
"""

import pexpect
import shutit_util
import logging
import string
import shutit_global
import shutit_assets
import time
import os


class ShutItPexpectSession(object):

	def __init__(self,
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
		self.default_expect      = [shutit_global.shutit.cfg['expect_prompts']['base_prompt']]
		self.pexpect_session_id  = pexpect_session_id
		self.login_stack         = []
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
		shutit_global.shutit.log('sessions before: ' + str(shutit_global.shutit.shutit_pexpect_sessions),level=logging.DEBUG)
		shutit_global.shutit.shutit_pexpect_sessions.update({self.pexpect_session_id:self})
		shutit_global.shutit.log('sessions after: ' + str(shutit_global.shutit.shutit_pexpect_sessions),level=logging.DEBUG)
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
		cfg = shutit_global.shutit.cfg
		# Be helpful.
		if ' ' in user:
			shutit_global.shutit.fail('user has space in it - did you mean: login(command="' + user + '")?')
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
			shutit_global.shutit.log('WARNING! user is bash - if you see problems below, did you mean: login(command="' + user + '")?',level=loglevel.WARNING)
		shutit_global.shutit._handle_note(note,command=command + ', as user: "' + user + '"',training_input=send)
		# r'[^t] login:' - be sure not to match 'last login:'
		shutit_global.shutit.multisend(send,{'ontinue connecting':'yes','assword':password,r'[^t] login:':password},expect=general_expect,check_exit=False,timeout=timeout,fail_on_empty_before=False,escape=escape)
		if prompt_prefix != None:
			self.setup_prompt(r_id,prefix=prompt_prefix)
		else:
			self.setup_prompt(r_id)
		if go_home:
			shutit_global.shutit.send('cd',shutit_pexpect_child=self.pexpect_child,check_exit=False, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
		self.login_stack_append(r_id)
		shutit_global.shutit._handle_note_after(note=note)



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
		shutit_global.shutit._handle_note(note,training_input=command)
		if len(self.login_stack):
			_ = self.login_stack.pop()
			if len(self.login_stack):
				old_prompt_name	 = self.login_stack[-1]
				# TODO: sort out global expect_prompts
				self.default_expect = shutit_global.shutit.cfg['expect_prompts'][old_prompt_name]
			else:
				# If none are on the stack, we assume we're going to the root prompt
				# set up in shutit_setup.py
				shutit_global.shutit.set_default_shutit_pexpect_session_expect()
		else:
			shutit_global.shutit.fail('Logout called without corresponding login', throw_exception=False)
		# No point in checking exit here, the exit code will be
		# from the previous command from the logged in session
		shutit_global.shutit.send(command, shutit_pexpect_child=self.pexpect_child, expect=expect, check_exit=False, timeout=timeout,echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
		shutit_global.shutit._handle_note_after(note=note)


	def login_stack_append(self,
						   r_id):
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
		
		    shutit.send('su - auser', expect=shutit_global.shutit.cfg['expect_prompts']['base_prompt'], check_exit=False)
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
		cfg = shutit_global.shutit.cfg
		cfg['expect_prompts'][prompt_name] = local_prompt
		# Set up the PS1 value.
		# Unset the PROMPT_COMMAND as this can cause nasty surprises in the output.
		# Set the cols value, as unpleasant escapes are put in the output if the
		# input is > n chars wide.
		# The newline in the expect list is a hack. On my work laptop this line hangs
		# and times out very frequently. This workaround seems to work, but I
		# haven't figured out why yet - imiell.
		shutit_global.shutit.send((" export SHUTIT_BACKUP_PS1_%s=$PS1 && PS1='%s' && unset PROMPT_COMMAND && stty sane && stty cols " + str(cfg['build']['stty_cols'])) % (prompt_name, local_prompt) + ' && export HISTCONTROL=$HISTCONTROL:ignoredups:ignorespace', expect=['\r\n' + cfg['expect_prompts'][prompt_name]], fail_on_empty_before=False, timeout=5, shutit_pexpect_child=self.pexpect_child, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
		shutit_global.shutit.log('Resetting default expect to: ' + cfg['expect_prompts'][prompt_name],level=logging.DEBUG)
		self.default_expect = cfg['expect_prompts'][prompt_name]
		# Ensure environment is set up OK.
		self.setup_environment(prefix)


	def revert_prompt(self,
	                  old_prompt_name,
	                  new_expect=None,
	                  delaybeforesend=0):
		"""Reverts the prompt to the previous value (passed-in).
		
		It should be fairly rare to need this. Most of the time you would just
		exit a subshell rather than resetting the prompt.
		
		    - old_prompt_name -
		    - new_expect      -
		    - child           - See send()
		"""
		expect = new_expect or self.default_expect
		#     v the space is intentional, to avoid polluting bash history.
		shutit_global.shutit.send((' PS1="${SHUTIT_BACKUP_PS1_%s}" && unset SHUTIT_BACKUP_PS1_%s') % (old_prompt_name, old_prompt_name), expect=expect, check_exit=False, fail_on_empty_before=False, echo=False, loglevel=logging.DEBUG,delaybeforesend=delaybeforesend)
		if not new_expect:
			shutit_global.shutit.log('Resetting default expect to default',level=logging.DEBUG)
			shutit_global.shutit.set_default_shutit_pexpect_session_expect()
		self.setup_environment(old_prompt_name)


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
	                      new_target_image_name):
		"""Replaces a container. Assumes we are in Docker context
		"""
		cfg = shutit_global.shutit.cfg
		shutit_global.shutit.log('Replacing container, please wait...',level=logging.INFO)

		# Destroy existing container.
		conn_module = None
		for mod in shutit_global.shutit.conn_modules:
			if mod.module_id == cfg['build']['conn_module']:
				conn_module = mod
				break
		if conn_module is None:
			shutit_global.shutit.fail('''Couldn't find conn_module ''' + cfg['build']['conn_module'])
		container_id = cfg['target']['container_id']
		conn_module.destroy_container(shutit_global.shutit, 'host_child', 'target_child', container_id)
		
		# Start up a new container.
		cfg['target']['docker_image'] = new_target_image_name
		target_child = conn_module.start_container(shutit_global.shutit,self.pexpect_session_id)
		conn_module.setup_target_child(shutit_global.shutit, target_child)

		# set the target child up
		self.pexpect_child = target_child
		shutit_global.shutit.log('z',level=logging.DEBUG)
		shutit_global.shutit.log(self.default_expect,level=logging.DEBUG)
		
		# set up the prompt on startup
		self.default_expect = [cfg['expect_prompts']['base_prompt']]
		self.setup_prompt('root')
		self.login_stack_append('root')
		# Log in and let ShutIt take care of the prompt.
		# Don't go home in case the workdir is different in the docker image!
		self.login(command='bash',go_home=False)
		return


	def whoami(self,
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
		shutit_global.shutit._handle_note(note)
		res = shutit_global.shutit.send_and_get_output(' whoami',shutit_pexpect_child=self.pexpect_child,echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend).strip()
		shutit_global.shutit._handle_note_after(note=note)
		return res


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
		shutit_global.shutit.set_default_shutit_pexpect_session(self)
		cfg = shutit_global.shutit.cfg
		environment_id_dir = cfg['build']['shutit_state_dir'] + '/environment_id'
		if shutit_global.shutit.file_exists(environment_id_dir,directory=True):
			files = shutit_global.shutit.ls(environment_id_dir)
			if len(files) != 1 or type(files) != list:
				if len(files) == 2 and (files[0] == 'ORIGIN_ENV' or files[1] == 'ORIGIN_ENV'):
					for f in files:
						if f != 'ORIGIN_ENV':
							environment_id = f
							cfg['build']['current_environment_id'] = environment_id
							# Workaround for CygWin terminal issues. If the envid isn't in the cfg item
							# Then crudely assume it is. This will drop through and then assume we are in the origin env.
							try:
								_=cfg['environment'][cfg['build']['current_environment_id']]
							except Exception:
								cfg['build']['current_environment_id'] = 'ORIGIN_ENV'
							break
				else:
					# See comment above re: cygwin.
					if shutit_global.shutit.file_exists('/cygdrive'):
						cfg['build']['current_environment_id'] = 'ORIGIN_ENV'
					else:
						shutit_global.shutit.fail('Wrong number of files in environment_id_dir: ' + environment_id_dir)
			else:
				if shutit_global.shutit.file_exists('/cygdrive'):
					environment_id = 'ORIGIN_ENV'
				else:
					environment_id = files[0]
			if cfg['build']['current_environment_id'] != environment_id:
				# Clean out any trace of this new environment, and return the already-existing one.
				shutit_global.shutit.send(' rm -rf ' + environment_id_dir + '/environment_id/' + environment_id, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
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
			shutit_global.shutit.get_distro_info(environment_id)
		fname = environment_id_dir + '/' + environment_id
		shutit_global.shutit.send(' mkdir -p ' + environment_id_dir + ' && chmod -R 777 ' + cfg['build']['shutit_state_dir_base'] + ' && touch ' + fname, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
		cfg['environment'][environment_id]['setup']                        = True
		return environment_id


	def create_command_file(self, expect, send):
		"""Internal function. Do not use.

		Takes a long command, and puts it in an executable file ready to run. Returns the filename.
		"""
		cfg = shutit_global.shutit.cfg
		random_id = shutit_util.random_id()
		fname = cfg['build']['shutit_state_dir_base'] + '/tmp_' + random_id
		working_str = send
		self.sendline(' truncate --size 0 '+ fname)
		self.pexpect_child.expect(expect)
		size = cfg['build']['stty_cols'] - 25
		while len(working_str) > 0:
			curr_str = working_str[:size]
			working_str = working_str[size:]
			self.sendline(' ' + shutit_util.get_command('head') + ''' -c -1 >> ''' + fname + """ << 'END_""" + random_id + """'\n""" + curr_str + """\nEND_""" + random_id)
			self.expect(expect)
		self.sendline(' chmod +x ' + fname)
		self.expect(expect)
		return fname



	def check_last_exit_values(self,
	                           send,
	                           expect=None,
	                           exit_values=None,
	                           retry=0,
	                           retbool=False):
		"""Internal function to check the exit value of the shell. Do not use.
		"""
		cfg = shutit_global.shutit.cfg
		expect = expect or self.default_expect
		if not self.check_exit:
			shutit_global.shutit.log('check_exit configured off, returning', level=logging.DEBUG)
			return
		if exit_values is None:
			exit_values = ['0']
		# Don't use send here (will mess up last_output)!
		# Space before "echo" here is sic - we don't need this to show up in bash history
		self.sendline(' echo EXIT_CODE:$?')
		self.expect(expect)
		res = shutit_util.match_string(self.pexpect_child.before, '^EXIT_CODE:([0-9][0-9]?[0-9]?)$')
		if res == None:
			# Try after - for some reason needed after login
			res = shutit_util.match_string(self.pexpect_child.after, '^EXIT_CODE:([0-9][0-9]?[0-9]?)$')
		if res not in exit_values or res == None:
			if res == None:
				res = str(res)
			shutit_global.shutit.log('shutit_pexpect_child.after: ' + str(self.pexpect_child.after), level=logging.DEBUG)
			shutit_global.shutit.log('Exit value from command: ' + str(send) + ' was:' + res, level=logging.DEBUG)
			msg = ('\nWARNING: command:\n' + send + '\nreturned unaccepted exit code: ' + res + '\nIf this is expected, pass in check_exit=False or an exit_values array into the send function call.')
			cfg['build']['report'] += msg
			if retbool:
				return False
			elif cfg['build']['interactive'] >= 1:
				# This is a failure, so we pass in level=0
				shutit_global.shutit.pause_point(msg + '\n\nInteractive, so not retrying.\nPause point on exit_code != 0 (' + res + '). CTRL-C to quit', shutit_pexpect_child=self.pexpect_child, level=0)
			elif retry == 1:
				shutit_global.shutit.fail('Exit value from command\n' + send + '\nwas:\n' + res, throw_exception=False)
			else:
				return False
		return True



	def pause_point(self,
	                msg='SHUTIT PAUSE POINT',
	                print_input=True,
	                resize=True,
	                colour='32',
	                default_msg=None,
	                wait=-1,
	                delaybeforesend=0):
		"""Inserts a pause in the build session, which allows the user to try
		things out before continuing. Ignored if we are not in an interactive
		mode.
		Designed to help debug the build, or drop to on failure so the
		situation can be debugged.

		@param msg:          Message to display to user on pause point.
		@param print_input:  Whether to take input at this point (i.e. interact), or
		                     simply pause pending any input.
		                     Default: True
		@param resize:       If True, try to resize terminal.
		                     Default: False
		@param colour:       Colour to print message (typically 31 for red, 32 for green)
		@param default_msg:  Whether to print the standard blurb
		@param wait:         Wait a few seconds rather than for input

		@type msg:           string
		@type print_input:   boolean
		@type resize:        boolean
		@type wait:          decimal

		@return:             True if pause point handled ok, else false
		"""
		cfg = shutit_global.shutit.cfg
		if print_input:
			if resize:
				fixterm_filename = '/tmp/shutit_fixterm'
				if not shutit_global.shutit.file_exists(fixterm_filename):
					shutit_global.shutit.send_file(fixterm_filename,shutit_assets.get_fixterm(), shutit_pexpect_child=self.pexpect_child, loglevel=logging.DEBUG, delaybeforesend=delaybeforesend)
					shutit_global.shutit.send(' chmod 777 ' + fixterm_filename, echo=False,loglevel=logging.DEBUG, delaybeforesend=delaybeforesend)
				self.sendline(' ' + fixterm_filename, delaybeforesend=delaybeforesend)
			if default_msg == None:
				if not cfg['build']['video']:
					pp_msg = '\r\nYou now have a standard shell. Hit CTRL and then ] at the same to continue ShutIt run.'
					if cfg['build']['delivery'] == 'docker':
						pp_msg += '\r\nHit CTRL and u to save the state to a docker image'
					shutit_global.shutit.log('\r\n' + 80*'=' + '\r\n' + shutit_util.colourise(colour,msg) +'\r\n'+80*'='+'\r\n' + shutit_util.colourise(colour,pp_msg),transient=True)
				else:
					shutit_global.shutit.log('\r\n' + (shutit_util.colourise(colour, msg)),transient=True)
			else:
				shutit_global.shutit.log(shutit_util.colourise(colour, msg) + '\r\n' + default_msg + '\r\n',transient=True)
			oldlog = self.pexpect_child.logfile_send
			self.pexpect_child.logfile_send = None
			if wait < 0:
				try:
					self.pexpect_child.interact(input_filter=self._pause_input_filter)
					self.handle_pause_point_signals()
				except Exception as e:
					shutit_global.shutit.fail('Terminating ShutIt.\n' + str(e))
			else:
				time.sleep(wait)
			self.pexpect_child.logfile_send = oldlog
		else:
			pass
		cfg['build']['ctrlc_stop'] = False
		return True


	def _pause_input_filter(self, input_string):
		"""Input filter for pause point to catch special keystrokes"""
		# Can get errors with eg up/down chars
		cfg = shutit_global.shutit.cfg
		if len(input_string) == 1:
			# Picked CTRL-u as the rarest one accepted by terminals.
			if ord(input_string) == 21 and cfg['build']['delivery'] == 'docker':
				shutit_global.shutit.log('CTRL and u caught, forcing a tag at least',level=logging.INFO)
				shutit_global.shutit.do_repository_work('tagged_by_shutit', password=cfg['host']['password'], docker_executable=cfg['host']['docker_executable'], force=True)
				shutit_global.shutit.log('Commit and tag done. Hit CTRL and ] to continue with build. Hit return for a prompt.',level=logging.INFO)
			# CTRL-d
			elif ord(input_string) == 4:
				cfg['SHUTIT_SIGNAL']['ID'] = 0
				cfg['SHUTIT_SIGNAL']['ID'] = 4
				if shutit_util.get_input('CTRL-d caught, are you sure you want to quit this ShutIt run?\n\r=> ',default='n',boolean=True):
					shutit_global.shutit.fail('CTRL-d caught, quitting')
				if shutit_util.get_input('Do you want to pass through the CTRL-d to the ShutIt session?\n\r=> ',default='n',boolean=True):
					return '\x04'
				# Return nothing
				return ''
			# CTRL-h
			elif ord(input_string) == 8:
				cfg['SHUTIT_SIGNAL']['ID'] = 8
				# Return the escape from pexpect char
				return '\x1d'
			# CTRL-g
			elif ord(input_string) == 7:
				cfg['SHUTIT_SIGNAL']['ID'] = 7
				# Return the escape from pexpect char
				return '\x1d'
			# CTRL-s
			elif ord(input_string) == 19:
				cfg['SHUTIT_SIGNAL']['ID'] = 19
				# Return the escape from pexpect char
				return '\x1d'
			# CTRL-]
			elif ord(input_string) == 29:
				cfg['SHUTIT_SIGNAL']['ID'] = 29
				# Return the escape from pexpect char
				return '\x1d'
		return input_string


	def handle_pause_point_signals(self):
		cfg = shutit_global.shutit.cfg
		if cfg['SHUTIT_SIGNAL']['ID'] == 29:
			cfg['SHUTIT_SIGNAL']['ID'] = 0
			shutit_global.shutit.log('\r\nCTRL-] caught, continuing with run...',level=logging.INFO,transient=True)


	def file_exists(self,
	                filename,
	                expect=None,
	                directory=False,
	                note=None,
	                delaybeforesend=0,
	                loglevel=logging.DEBUG):
		"""Return True if file exists on the target host, else False

		@param filename:   Filename to determine the existence of.
		@param expect:     See send()
		@param directory:  Indicate that the file is a directory.
		@param note:       See send()

		@type filename:    string
		@type directory:   boolean

		@rtype: boolean
		"""
		shutit_global.shutit._handle_note(note, 'Looking for filename in current environment: ' + filename)
		test_type = '-d' if directory is True else '-a'
		#       v the space is intentional, to avoid polluting bash history.
		test = ' test %s %s' % (test_type, filename)
		output = shutit_global.shutit.send_and_get_output(test + ' && echo FILEXIST-""FILFIN || echo FILNEXIST-""FILFIN', expect=expect, shutit_pexpect_child=self.pexpect_child, record_command=False, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
		res = shutit_util.match_string(output, '^(FILEXIST|FILNEXIST)-FILFIN$')
		ret = False
		if res == 'FILEXIST':
			ret = True
		elif res == 'FILNEXIST':
			pass
		else:
			# Change to log?
			shutit_global.shutit.log(repr('before>>>>:%s<<<< after:>>>>%s<<<<' % (self.pexpect_child.before, self.pexpect_child.after)),transient=True)
			shutit_global.shutit.fail('Did not see FIL(N)?EXIST in output:\n' + output)
		shutit_global.shutit._handle_note_after(note=note)
		return ret

	def chdir(self,
	          path,
	          expect=None,
	          timeout=3600,
	          note=None,
	          delaybeforesend=0,
	          loglevel=logging.DEBUG):
		"""How to change directory will depend on whether we are in delivery mode bash or docker.

		@param path:          Path to send file to.
		@param expect:        See send()
		@param shutit_pexpect_child:         See send()
		@param timeout:       Timeout on response
		@param note:          See send()
		"""
		cfg = shutit_global.shutit.cfg
		shutit_global.shutit._handle_note(note, 'Changing to path: ' + path)
		shutit_global.shutit.log('Changing directory to path: "' + path + '"', level=logging.DEBUG)
		if cfg['build']['delivery'] in ('bash','dockerfile'):
			shutit_global.shutit.send(' cd ' + path, expect=expect, shutit_pexpect_child=self.pexpect_child, timeout=timeout, echo=False,loglevel=loglevel, delaybeforesend=delaybeforesend)
		elif cfg['build']['delivery'] in ('docker','ssh'):
			os.chdir(path)
		else:
			shutit_global.shutit.fail('chdir not supported for delivery method: ' + cfg['build']['delivery'])
		shutit_global.shutit._handle_note_after(note=note)



	def get_file_perms(self,
	                   filename,
	                   expect=None,
	                   note=None,
	                   delaybeforesend=0,
	                   loglevel=logging.DEBUG):
		"""Returns the permissions of the file on the target as an octal
		string triplet.

		@param filename:  Filename to get permissions of.
		@param expect:    See send()
		@param note:      See send()

		@type filename:   string

		@rtype:           string
		"""
		shutit_global.shutit._handle_note(note)
		cmd = 'stat -c %a ' + filename
		shutit_global.shutit.send(' ' + cmd, expect, shutit_pexpect_child=self.pexpect_child, check_exit=False, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
		res = shutit_util.match_string(self.pexpect_child.before, '([0-9][0-9][0-9])')
		shutit_global.shutit._handle_note_after(note=note)
		return res


	def add_to_bashrc(self,
	                  line,
	                  expect=None,
	                  match_regexp=None,
	                  note=None,
	                  loglevel=logging.DEBUG):
		"""Takes care of adding a line to everyone's bashrc
		(/etc/bash.bashrc, /etc/profile).

		@param line:          Line to add.
		@param expect:        See send()
		@param match_regexp:  See add_line_to_file()
		@param note:          See send()

		@return:              See add_line_to_file()
		"""
		shutit_global.shutit._handle_note(note)
		if not shutit_util.check_regexp(match_regexp):
			shutit_global.shutit.fail('Illegal regexp found in add_to_bashrc call: ' + match_regexp)
		# TODO: pass in pexpect_child?
		shutit_global.shutit.add_line_to_file(line, '${HOME}/.bashrc', expect=expect, match_regexp=match_regexp, loglevel=loglevel) # This won't work for root - TODO
		shutit_global.shutit.add_line_to_file(line, '/etc/bash.bashrc', expect=expect, match_regexp=match_regexp, loglevel=loglevel)






	#TODO: create environment object
	#TODO: review items in cfg and see if they make more sense in the pexpect object
	#TODO: replace 'target' in cfg
