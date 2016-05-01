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

import logging
import string
import time
import os
import pexpect
import shutit_util
import shutit_global
import shutit_assets
from shutit_module import ShutItFailException
import package_map
import re
import base64


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
		self.multisend(send,{'ontinue connecting':'yes','assword':password,r'[^t] login:':password},expect=general_expect,check_exit=False,timeout=timeout,fail_on_empty_before=False,escape=escape)
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

		@param note:     See send()

		@return: the output of "whoami"
		@rtype: string
		"""
		shutit_global.shutit._handle_note(note)
		res = self.send_and_get_output(' whoami',echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend).strip()
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
		if self.file_exists(environment_id_dir,directory=True):
			files = self.ls(environment_id_dir)
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
					if self.file_exists('/cygdrive'):
						cfg['build']['current_environment_id'] = 'ORIGIN_ENV'
					else:
						shutit_global.shutit.fail('Wrong number of files in environment_id_dir: ' + environment_id_dir)
			else:
				if self.file_exists('/cygdrive'):
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
				if not self.file_exists(fixterm_filename):
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
	                directory=False,
	                note=None,
	                delaybeforesend=0,
	                loglevel=logging.DEBUG):
		"""Return True if file exists on the target host, else False

		@param filename:   Filename to determine the existence of.
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
		output = self.send_and_get_output(test + ' && echo FILEXIST-""FILFIN || echo FILNEXIST-""FILFIN', record_command=False, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
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
	          timeout=3600,
	          note=None,
	          delaybeforesend=0,
	          loglevel=logging.DEBUG):
		"""How to change directory will depend on whether we are in delivery mode bash or docker.

		@param path:          Path to send file to.
		@param timeout:       Timeout on response
		@param note:          See send()
		"""
		cfg = shutit_global.shutit.cfg
		shutit_global.shutit._handle_note(note, 'Changing to path: ' + path)
		shutit_global.shutit.log('Changing directory to path: "' + path + '"', level=logging.DEBUG)
		if cfg['build']['delivery'] in ('bash','dockerfile'):
			shutit_global.shutit.send(' cd ' + path, shutit_pexpect_child=self.pexpect_child, timeout=timeout, echo=False,loglevel=loglevel, delaybeforesend=delaybeforesend)
		elif cfg['build']['delivery'] in ('docker','ssh'):
			os.chdir(path)
		else:
			shutit_global.shutit.fail('chdir not supported for delivery method: ' + cfg['build']['delivery'])
		shutit_global.shutit._handle_note_after(note=note)



	def get_file_perms(self,
	                   filename,
	                   note=None,
	                   delaybeforesend=0,
	                   loglevel=logging.DEBUG):
		"""Returns the permissions of the file on the target as an octal
		string triplet.

		@param filename:  Filename to get permissions of.
		@param note:      See send()

		@type filename:   string

		@rtype:           string
		"""
		shutit_global.shutit._handle_note(note)
		cmd = 'stat -c %a ' + filename
		shutit_global.shutit.send(' ' + cmd, shutit_pexpect_child=self.pexpect_child, check_exit=False, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
		res = shutit_util.match_string(self.pexpect_child.before, '([0-9][0-9][0-9])')
		shutit_global.shutit._handle_note_after(note=note)
		return res


	def add_to_bashrc(self,
	                  line,
	                  match_regexp=None,
	                  note=None,
	                  loglevel=logging.DEBUG):
		"""Takes care of adding a line to everyone's bashrc
		(/etc/bash.bashrc, /etc/profile).

		@param line:          Line to add.
		@param match_regexp:  See add_line_to_file()
		@param note:          See send()

		@return:              See add_line_to_file()
		"""
		shutit_global.shutit._handle_note(note)
		if not shutit_util.check_regexp(match_regexp):
			shutit_global.shutit.fail('Illegal regexp found in add_to_bashrc call: ' + match_regexp)
		shutit_global.shutit.add_line_to_file(line, '${HOME}/.bashrc', match_regexp=match_regexp, loglevel=loglevel) # This won't work for root - TODO
		shutit_global.shutit.add_line_to_file(line, '/etc/bash.bashrc', match_regexp=match_regexp, loglevel=loglevel)



	def is_user_id_available(self,
	                         user_id,
	                         note=None,
	                         delaybeforesend=0,
	                         loglevel=logging.DEBUG):
		"""Determine whether the specified user_id available.

		@param user_id:  User id to be checked.
		@param note:     See send()

		@type user_id:   integer

		@rtype:          boolean
		@return:         True is the specified user id is not used yet, False if it's already been assigned to a user.
		"""
		shutit_global.shutit._handle_note(note)
		# v the space is intentional, to avoid polluting bash history.
		shutit_global.shutit.send(' cut -d: -f3 /etc/paswd | grep -w ^' + user_id + '$ | wc -l', shutit_pexpect_child=self.pexpect_child, expect=self.default_expect, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
		shutit_global.shutit._handle_note_after(note=note)
		if shutit_util.match_string(self.pexpect_child.before, '^([0-9]+)$') == '1':
			return False
		else:
			return True



	def set_password(self,
	                 password,
	                 user='',
	                 delaybeforesend=0.05,
	                 note=None):
		"""Sets the password for the current user or passed-in user.

		As a side effect, installs the "password" package.

		@param user:        username to set the password for. Defaults to '' (i.e. current user)
		@param password:    password to set for the user
		@param note:        See send()
		"""

		cfg = shutit_global.shutit.cfg
		shutit_global.shutit._handle_note(note)
		self.install('passwd')
		if cfg['environment'][cfg['build']['current_environment_id']]['install_type'] == 'apt':
			shutit_global.shutit.send('passwd ' + user, expect='Enter new', shutit_pexpect_child=self.pexpect_child, check_exit=False, delaybeforesend=delaybeforesend)
			shutit_global.shutit.send(password, shutit_pexpect_child=self.pexpect_child, expect='Retype new', check_exit=False, echo=False, delaybeforesend=delaybeforesend)
			shutit_global.shutit.send(password, shutit_pexpect_child=self.pexpect_child, expect=self.default_expect, echo=False, delaybeforesend=delaybeforesend)
		elif shutit_global.shutit['environment'][cfg['build']['current_environment_id']]['install_type'] == 'yum':
			shutit_global.shutit.send('passwd ' + user, shutit_pexpect_child=self.pexpect_child, expect='ew password', check_exit=False,delaybeforesend=delaybeforesend)
			shutit_global.shutit.send(password, shutit_pexpect_child=self.pexpect_child, expect='ew password', check_exit=False, echo=False, delaybeforesend=delaybeforesend)
			shutit_global.shutit.send(password, shutit_pexpect_child=self.pexpect_child, expect=self.default_expect, echo=False, delaybeforesend=delaybeforesend)
		else:
			shutit_global.shutit.send('passwd ' + user, expect='Enter new', shutit_pexpect_child=self.pexpect_child, check_exit=False, delaybeforesend=delaybeforesend)
			shutit_global.shutit.send(password, shutit_pexpect_child=self.pexpect_child, expect='Retype new', check_exit=False, echo=False, delaybeforesend=delaybeforesend)
			shutit_global.shutit.send(password, shutit_pexpect_child=self.pexpect_child, expect=self.default_expect, echo=False, delaybeforesend=delaybeforesend)
		shutit_global.shutit._handle_note_after(note=note)



	def lsb_release(self,
	                delaybeforesend=0,
	                loglevel=logging.DEBUG):
		"""Get distro information from lsb_release.
		"""
		#          v the space is intentional, to avoid polluting bash history.
		shutit_global.shutit.send(' lsb_release -a',check_exit=False, echo=False, loglevel=loglevel,delaybeforesend=delaybeforesend)
		dist_string = shutit_util.match_string(self.pexpect_child.before, '^Distributor[\s]*ID:[\s]*(.*)$')
		version_string = shutit_util.match_string(self.pexpect_child.before, '^Release:[\s*](.*)$')
		d = {}
		if dist_string:
			d['distro']         = dist_string.lower().strip()
			d['distro_version'] = version_string
			d['install_type'] = (package_map.INSTALL_TYPE_MAP[dist_string.lower()])
		return d



	def get_url(self,
	            filename,
	            locations,
	            command='curl',
	            timeout=3600,
	            fail_on_empty_before=True,
	            record_command=True,
	            exit_values=None,
	            retry=3,
	            note=None,
	            delaybeforesend=0,
	            loglevel=logging.DEBUG):
		"""Handles the getting of a url for you.

		Example:
		get_url('somejar.jar', ['ftp://loc.org','http://anotherloc.com/jars'])

		@param filename:             name of the file to download
		@param locations:            list of URLs whence the file can be downloaded
		@param command:              program to use to download the file (Default: wget)
		@param timeout:              See send()
		@param fail_on_empty_before: See send()
		@param record_command:       See send()
		@param exit_values:          See send()
		@param retry:                How many times to retry the download
		                             in case of failure. Default: 3
		@param note:                 See send()

		@type filename:              string
		@type locations:             list of strings
		@type retry:                 integer

		@return: True if the download was completed successfully, False otherwise.
		@rtype: boolean
		"""
		shutit_global.shutit._handle_note(note)
		if len(locations) == 0 or type(locations) != list:
			raise ShutItFailException('Locations should be a list containing base of the url.')
		retry_orig = retry
		if not self.command_available(command):
			self.install('curl')
			if not self.command_available('curl'):
				self.install('wget')
				command = 'wget -qO- '
				if not self.command_available('wget'):
					shutit_global.shutit.fail('Could not install curl or wget, inform maintainers.')
		for location in locations:
			retry = retry_orig
			if location[-1] == '/':
				location = location[0:-1]
			while retry >= 0:
				send = command + ' ' + location + '/' + filename + ' > ' + filename
				shutit_global.shutit.send(send,check_exit=False,shutit_pexpect_child=self.pexpect_child,expect=self.default_expect,timeout=timeout,fail_on_empty_before=fail_on_empty_before,record_command=record_command,echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
				if retry == 0:
					self.check_last_exit_values(send, self.default_expect, timeout, exit_values, retbool=False)
				elif not self.check_last_exit_values(send, self.default_expect, timeout, exit_values, retbool=True):
					shutit_global.shutit.log('Sending: ' + send + ' failed, retrying', level=logging.DEBUG)
					retry -= 1
					continue
				# If we get here, all is ok.
				shutit_global.shutit._handle_note_after(note=note)
				return True
		# If we get here, it didn't work
		return False



	def user_exists(self,
	                user,
	                note=None,
	                delaybeforesend=0,
 	                loglevel=logging.DEBUG):
		"""Returns true if the specified username exists.
		
		@param user:   username to check for
		@param note:   See send()

		@type user:    string

		@rtype:        boolean
		"""
		shutit_global.shutit._handle_note(note)
		exists = False
		if user == '':
			return exists
		#v the space is intentional, to avoid polluting bash history.
		ret = shutit_global.shutit.send(' id %s && echo E""XIST || echo N""XIST' % user, expect=['NXIST', 'EXIST'], shutit_pexpect_child=self.pexpect_child, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
		if ret:
			exists = True
		# sync with the prompt
		self.expect(self.default_expect)
		shutit_global.shutit._handle_note_after(note=note)
		return exists


	def package_installed(self,
	                      package,
	                      note=None,
	                      delaybeforesend=0,
	                      loglevel=logging.DEBUG):
		"""Returns True if we can be sure the package is installed.

		@param package:   Package as a string, eg 'wget'.
		@param note:      See send()

		@rtype:           boolean
		"""
		cfg = shutit_global.shutit.cfg
		shutit_global.shutit._handle_note(note)
		if cfg['environment'][cfg['build']['current_environment_id']]['install_type'] == 'apt':
			#            v the space is intentional, to avoid polluting bash history.
			shutit_global.shutit.send(""" dpkg -l | awk '{print $2}' | grep "^""" + package + """$" | wc -l""", expect=self.default_expect, check_exit=False, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
		elif cfg['environment'][cfg['build']['current_environment_id']]['install_type'] == 'yum':
			#            v the space is intentional, to avoid polluting bash history.
			shutit_global.shutit.send(""" yum list installed | awk '{print $1}' | grep "^""" + package + """$" | wc -l""", expect=self.default_expect, check_exit=False, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
		else:
			return False
		if shutit_util.match_string(self.pexpect_child.before, '^([0-9]+)$') != '0':
			return True
		else:
			return False



	def command_available(self,
	                      command,
	                      note=None,
	                      delaybeforesend=0,
	                      loglevel=logging.DEBUG):
		shutit_global.shutit._handle_note(note)
		if self.send_and_get_output(' command -v ' + command, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend) != '':
			return True
		else:
			return False



	def is_shutit_installed(self,
	                        module_id,
	                        note=None,
	                        delaybeforesend=0,
	                        loglevel=logging.DEBUG):
		"""Helper proc to determine whether shutit has installed already here by placing a file in the db.
	
		@param module_id: Identifying string of shutit module
		@param note:      See send()
		"""
		# If it's already in cache, then return True.
		# By default the cache is invalidated.
		cfg = shutit_global.shutit.cfg
		shutit_global.shutit._handle_note(note)
		if not cfg['environment'][cfg['build']['current_environment_id']]['modules_recorded_cache_valid']:
			if self.file_exists(cfg['build']['build_db_dir'] + '/module_record',directory=True):
				# Bit of a hack here to get round the long command showing up as the first line of the output.
				cmd = 'find ' + cfg['build']['build_db_dir'] + r"""/module_record/ -name built | sed 's@^.""" + cfg['build']['build_db_dir'] + r"""/module_record.\([^/]*\).built@\1@' > """ + cfg['build']['build_db_dir'] + '/' + cfg['build']['build_id']
				shutit_global.shutit.send(' ' + cmd, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
				built = self.send_and_get_output('cat ' + cfg['build']['build_db_dir'] + '/' + cfg['build']['build_id'], echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend).strip()
				shutit_global.shutit.send(' rm -rf ' + cfg['build']['build_db_dir'] + '/' + cfg['build']['build_id'], echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
				built_list = built.split('\r\n')
				cfg['environment'][cfg['build']['current_environment_id']]['modules_recorded'] = built_list
			# Either there was no directory (so the cache is valid), or we've built the cache, so mark as good.
			cfg['environment'][cfg['build']['current_environment_id']]['modules_recorded_cache_valid'] = True
		# Modules recorded cache will be valid at this point, so check the pre-recorded modules and the in-this-run installed cache.
		shutit_global.shutit._handle_note_after(note=note)
		if module_id in cfg['environment'][cfg['build']['current_environment_id']]['modules_recorded'] or module_id in cfg['environment'][cfg['build']['current_environment_id']]['modules_installed']:
			return True
		else:
			return False


	def ls(self,
	       directory,
	       note=None,
	       delaybeforesend=0,
	       loglevel=logging.DEBUG):
		"""Helper proc to list files in a directory

		@param directory:   directory to list.  If the directory doesn't exist, shutit.fail() is called (i.e.  the build fails.)
		@param note:        See send()

		@type directory:    string

		@rtype:             list of strings
		"""
		# should this blow up?
		shutit_global.shutit._handle_note(note)
		if not self.file_exists(directory,directory=True):
			shutit_global.shutit.fail('ls: directory\n\n' + directory + '\n\ndoes not exist', throw_exception=False)
		files = self.send_and_get_output(' ls ' + directory,echo=False, loglevel=loglevel, fail_on_empty_before=False, delaybeforesend=delaybeforesend)
		files = files.split(' ')
		# cleanout garbage from the terminal - all of this is necessary cause there are
		# random return characters in the middle of the file names
		files = filter(bool, files)
		files = [_file.strip() for _file in files]
		f = []
		for _file in files:
			spl = _file.split('\r')
			f = f + spl
		files = f
		# this is required again to remove the '\n's
		files = [_file.strip() for _file in files]
		shutit_global.shutit._handle_note_after(note=note)
		return files


	def install(self,
	            package,
	            options=None,
	            timeout=3600,
	            force=False,
	            check_exit=True,
	            reinstall=False,
	            note=None,
	            delaybeforesend=0,
	            loglevel=logging.DEBUG):
		"""Distro-independent install function.
		Takes a package name and runs the relevant install function.

		@param package:    Package to install, which is run through package_map
		@param timeout:    Timeout (s) to wait for finish of install. Defaults to 3600.
		@param options:    Dictionary for specific options per install tool.
		                   Overrides any arguments passed into this function.
		@param force:      Force if necessary. Defaults to False
		@param check_exit: If False, failure to install is ok (default True)
		@param reinstall:  Advise a reinstall where possible (default False)
		@param note:       See send()

		@type package:     string
		@type timeout:     integer
		@type options:     dict
		@type force:       boolean
		@type check_exit:  boolean
		@type reinstall:   boolean

		@return: True if all ok (ie it's installed), else False.
		@rtype: boolean
		"""
		cfg = shutit_global.shutit.cfg
		# If separated by spaces, install separately
		if package.find(' ') != -1:
			ok = True
			for p in package.split(' '):
				if not self.install(p,options,timeout,force,check_exit,reinstall,note):
					ok = False
			return ok
		# Some packages get mapped to the empty string. If so, bail out with 'success' here.
		shutit_global.shutit._handle_note(note)
		shutit_global.shutit.log('Installing package: ' + package,level=loglevel)
		if options is None: options = {}
		install_type = cfg['environment'][cfg['build']['current_environment_id']]['install_type']
		if install_type == 'src':
			# If this is a src build, we assume it's already installed.
			return True
		opts = ''
		whoiam = self.whoami()
		if whoiam != 'root' and install_type != 'brew':
			if not self.command_available('sudo'):
				shutit_global.shutit.pause_point('Please install sudo and then continue with CTRL-]',shutit_pexpect_child=self.pexpect_child)
			cmd = 'sudo '
			pw = self.get_env_pass(whoiam,'Please input your sudo password in case it is needed (for user: ' + whoiam + ')\nJust hit return if you do not want to submit a password.\n')
		else:
			cmd = ''
			pw = ''
		if install_type == 'apt':
			if not cfg['build']['apt_update_done']:
				shutit_global.shutit.send('apt-get update',loglevel=logging.INFO, delaybeforesend=delaybeforesend)
			cmd += 'apt-get install'
			if 'apt' in options:
				opts = options['apt']
			else:
				opts = '-y'
				if not cfg['build']['loglevel'] <= logging.DEBUG:
					opts += ' -qq'
				if force:
					opts += ' --force-yes'
				if reinstall:
					opts += ' --reinstall'
		elif install_type == 'yum':
			cmd += 'yum install'
			if 'yum' in options:
				opts = options['yum']
			else:
				opts += ' -y'
			if reinstall:
				opts += ' reinstall'
		elif install_type == 'apk':
			cmd += 'apk add'
			if 'apk' in options:
				opts = options['apk']
		elif install_type == 'emerge':
			cmd += 'emerge'
			if 'emerge' in options:
				opts = options['emerge']
		elif install_type == 'docker':
			cmd += 'docker pull'
			if 'docker' in options:
				opts = options['docker']
		elif install_type == 'brew':
			cmd += 'brew install'
			if 'brew' in options:
				opts = options['brew']
			else:
				opts += ' --force'
		else:
			# Not handled
			return False
		# Get mapped packages.
		package = package_map.map_packages(package, cfg['environment'][cfg['build']['current_environment_id']]['install_type'])
		# Let's be tolerant of failure eg due to network.
		# This is especially helpful with automated testing.
		if package.strip() != '':
			fails = 0
			while True:
				if pw != '':
					res = self.multisend('%s %s %s' % (cmd, opts, package), {'assword':pw}, expect=['Unable to fetch some archives',self.default_expect], timeout=timeout, check_exit=False, loglevel=loglevel)
				else:
					res = shutit_global.shutit.send('%s %s %s' % (cmd, opts, package), expect=['Unable to fetch some archives',self.default_expect], timeout=timeout, check_exit=check_exit, shutit_pexpect_child=self.pexpect_child, loglevel=loglevel, delaybeforesend=delaybeforesend)
				if res == 1:
					break
				else:
					fails += 1
				if fails >= 3:
					break
		else:
			# package not required
			pass
		shutit_global.shutit._handle_note_after(note=note)
		return True


	def get_memory(self,
	               delaybeforesend=0,
	               note=None):
		"""Returns memory available for use in k as an int"""
		cfg = shutit_global.shutit.cfg
		shutit_global.shutit._handle_note(note)
		if cfg['environment'][cfg['build']['current_environment_id']]['distro'] == 'osx':
			memavail = self.send_and_get_output("""vm_stat | grep ^Pages.free: | awk '{print $3}' | tr -d '.'""",timeout=3,echo=False, delaybeforesend=delaybeforesend)
			memavail = int(memavail)
			memavail *= 4
		else:
			memavail = self.send_and_get_output("""cat /proc/meminfo  | grep MemAvailable | awk '{print $2}'""",timeout=3,echo=False, delaybeforesend=delaybeforesend)
			if memavail == '':
				memavail = self.send_and_get_output("""free | grep buffers.cache | awk '{print $3}'""",timeout=3,echo=False, delaybeforesend=delaybeforesend)
			memavail = int(memavail)
		shutit_global.shutit._handle_note_after(note=note)
		return memavail


	def remove(self,
	           package,
	           options=None,
	           timeout=3600,
	           delaybeforesend=0,
	           note=None):
		"""Distro-independent remove function.
		Takes a package name and runs relevant remove function.

		@param package:  Package to remove, which is run through package_map.
		@param options:  Dict of options to pass to the remove command,
		                 mapped by install_type.
		@param timeout:  See send(). Default: 3600
		@param note:     See send()

		@return: True if all ok (i.e. the package was successfully removed),
		         False otherwise.
		@rtype: boolean
		"""
		cfg = shutit_global.shutit.cfg
		# If separated by spaces, remove separately
		shutit_global.shutit._handle_note(note)
		if options is None: options = {}
		install_type = cfg['environment'][cfg['build']['current_environment_id']]['install_type']
		whoiam = self.whoami()
		if whoiam != 'root' and install_type != 'brew':
			cmd = 'sudo '
			pw = self.get_env_pass(whoiam,'Please input your sudo password in case it is needed (for user: ' + whoiam + ')\nJust hit return if you do not want to submit a password.\n')
		else:
			cmd = ''
			pw = ''
		if install_type == 'src':
			# If this is a src build, we assume it's already installed.
			return True
		if install_type == 'apt':
			cmd += 'apt-get purge'
			opts = options['apt'] if 'apt' in options else '-qq -y'
		elif install_type == 'yum':
			cmd += 'yum erase'
			opts = options['yum'] if 'yum' in options else '-y'
		elif install_type == 'apk':
			cmd += 'apk del'
			if 'apk' in options:
				opts = options['apk']
		elif install_type == 'emerge':
			cmd += 'emerge -cav'
			if 'emerge' in options:
				opts = options['emerge']
		elif install_type == 'docker':
			cmd += 'docker rmi'
			if 'docker' in options:
				opts = options['docker']
		elif install_type == 'brew':
			cmd += 'brew uninstall'
			if 'brew' in options:
				opts = options['brew']
			else:
				opts += ' --force'
		else:
			# Not handled
			return False
		# Get mapped package.
		package = package_map.map_package(package, cfg['environment'][cfg['build']['current_environment_id']]['install_type'])
		if pw != '':
			self.multisend('%s %s %s' % (cmd, opts, package), {'assword:':pw}, timeout=timeout, exit_values=['0','100'])
		else:
			shutit_global.shutit.send('%s %s %s' % (cmd, opts, package), shutit_pexpect_child=self.pexpect_child, timeout=timeout, exit_values=['0','100'], delaybeforesend=delaybeforesend)
		shutit_global.shutit._handle_note_after(note=note)
		return True



	def send_and_match_output(self,
	                          send,
	                          matches,
	                          retry=3,
	                          strip=True,
	                          note=None,
	                          echo=False,
	                          delaybeforesend=0,
	                          loglevel=logging.DEBUG):
		"""Returns true if the output of the command matches any of the strings in
		the matches list of regexp strings. Handles matching on a per-line basis
		and does not cross lines.

		@param send:     See send()
		@param matches:  String - or list of strings - of regexp(s) to check
		@param retry:    Number of times to retry command (default 3)
		@param strip:    Whether to strip output (defaults to True)
		@param note:     See send()

		@type send:      string
		@type matches:   list
		@type retry:     integer
		@type strip:     boolean
		"""
		shutit_global.shutit._handle_note(note)
		shutit_global.shutit.log('Matching output from: "' + send + '" to one of these regexps:' + str(matches),level=logging.INFO)
		output = self.send_and_get_output(send, retry=retry, strip=strip, echo=echo, loglevel=loglevel, delaybeforesend=delaybeforesend)
		if type(matches) == str:
			matches = [matches]
		shutit_global.shutit._handle_note_after(note=note)
		for match in matches:
			if shutit_util.match_string(output, match) != None:
				shutit_global.shutit.log('Matched output, return True',level=logging.DEBUG)
				return True
		shutit_global.shutit.log('Failed to match output, return False',level=logging.DEBUG)
		return False



	def send_and_get_output(self,
	                        send,
	                        timeout=None,
	                        retry=3,
	                        strip=True,
	                        preserve_newline=False,
	                        note=None,
	                        record_command=False,
	                        echo=False,
	                        fail_on_empty_before=True,
	                        delaybeforesend=0,
	                        loglevel=logging.DEBUG):
		"""Returns the output of a command run. send() is called, and exit is not checked.

		@param send:     See send()
		@param retry:    Number of times to retry command (default 3)
		@param strip:    Whether to strip output (defaults to True). Strips whitespace
		                 and ansi terminal codes
		@param note:     See send()
		@param echo:     See send()

		@type retry:     integer
		@type strip:     boolean
		"""
		cfg = shutit_global.shutit.cfg
		shutit_global.shutit._handle_note(note, command=str(send))
		shutit_global.shutit.log('Retrieving output from command: ' + send,level=loglevel)
		# Don't check exit, as that will pollute the output. Also, it's quite likely the submitted command is intended to fail.
		shutit_global.shutit.send(shutit_util.get_send_command(send), shutit_pexpect_child=self.pexpect_child, check_exit=False, retry=retry, echo=echo, timeout=timeout, record_command=record_command, loglevel=loglevel, fail_on_empty_before=fail_on_empty_before, delaybeforesend=delaybeforesend)
		before = self.pexpect_child.before
		if preserve_newline and before[-1] == '\n':
			preserve_newline = True
		else:
			preserve_newline = False
		# Correct problem with first char in OSX.
		try:
			if cfg['environment'][cfg['build']['current_environment_id']]['distro'] == 'osx':
				before_list = before.split('\r\n')
				before_list = before_list[1:]
				before = string.join(before_list,'\r\n')
			else:
				before = before.strip(send)
		except Exception:
			before = before.strip(send)
		shutit_global.shutit._handle_note_after(note=note)
		if strip:
			ansi_escape = re.compile(r'\x1b[^m]*m')
			string_with_termcodes = before.strip()
			string_without_termcodes = ansi_escape.sub('', string_with_termcodes)
			#string_without_termcodes_stripped = string_without_termcodes.strip()
			# Strip out \rs to make it output the same as a typical CL. This could be optional.
			string_without_termcodes_stripped_no_cr = string_without_termcodes.replace('\r','')
			if False:
				for c in string_without_termcodes_stripped_no_cr:
					shutit_global.shutit.log((str(hex(ord(c))) + ' '),level=logging.DEBUG)
			if preserve_newline:
				return string_without_termcodes_stripped_no_cr + '\n'
			else:
				return string_without_termcodes_stripped_no_cr
		else:
			if False:
				for c in before:
					shutit_global.shutit.log((str(hex(ord(c))) + ' '),level=logging.DEBUG)
			return before


	def get_env_pass(self,user=None,msg=None,note=None):
		"""Gets a password from the user if one is not already recorded for this environment.

		@param user:    username we are getting password for
		@param msg:     message to put out there
		"""
		cfg = shutit_global.shutit.cfg
		shutit_global.shutit._handle_note(note)
		user = user or self.whoami()
		msg = msg or 'Please input the sudo password for user: ' + user
		# Test for the existence of the data structure.
		try:
			_=cfg['environment'][cfg['build']['current_environment_id']][user]
		except:
			cfg['environment'][cfg['build']['current_environment_id']][user] = {}
		try:
			_=cfg['environment'][cfg['build']['current_environment_id']][user]['password']
		except Exception:
			# Try and get input, if we are not interactive, this should fail.
			cfg['environment'][cfg['build']['current_environment_id']][user]['password'] = shutit_util.get_input(msg,ispass=True)
		shutit_global.shutit._handle_note_after(note=note)
		return cfg['environment'][cfg['build']['current_environment_id']][user]['password']


	def whoarewe(self,
	             note=None,
	             delaybeforesend=0,
	             loglevel=logging.DEBUG):
		"""Returns the current group.

		@param note:     See send()

		@return: the first group found
		@rtype: string
		"""
		shutit_global.shutit._handle_note(note)
		res = self.send_and_get_output(' id -n -g',echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend).strip()
		shutit_global.shutit._handle_note_after(note=note)
		return res




	# TODO: environment_id within this object
	def get_distro_info(self,
	                    environment_id,
	                    delaybeforesend=0,
	                    loglevel=logging.DEBUG):
		"""Get information about which distro we are using, placing it in the cfg['environment'][environment_id] as a side effect.

		Fails if distro could not be determined.
		Should be called with the container is started up, and uses as core info
		as possible.

		Note: if the install type is apt, it issues the following:
		    - apt-get update
		    - apt-get install -y -qq lsb-release

		"""
		cfg = shutit_global.shutit.cfg
		install_type   = ''
		distro         = ''
		distro_version = ''
		cfg['environment'][environment_id]['install_type']      = ''
		cfg['environment'][environment_id]['distro']            = ''
		cfg['environment'][environment_id]['distro_version']    = ''
		# A list of OS Family members
		# Suse      = SLES, SLED, OpenSuSE, Suse
		# Archlinux = Archlinux
		# Mandrake  = Mandriva, Mandrake
		# Solaris   = Solaris, Nexenta, OmniOS, OpenIndiana, SmartOS
		# AIX       = AIX
		# FreeBSD   = FreeBSD
		# HP-UK     = HPUX
		#    OSDIST_DICT = { '/etc/redhat-release': 'RedHat',
		#                    '/etc/vmware-release': 'VMwareESX',
		#                    '/etc/openwrt_release': 'OpenWrt',
		#                    '/etc/system-release': 'OtherLinux',
		#                    '/etc/release': 'Solaris',
		#                    '/etc/arch-release': 'Archlinux',
		#                    '/etc/SuSE-release': 'SuSE',
		#                    '/etc/gentoo-release': 'Gentoo',
		#                    '/etc/os-release': 'Debian' }
		#    # A list of dicts.  If there is a platform with more than one package manager, put the preferred one last.  If there is an ansible module, use that as the value for the 'name' key.
		#    PKG_MGRS = [
		#                 { 'path' : '/usr/bin/zypper',      'name' : 'zypper' },
		#                 { 'path' : '/usr/sbin/urpmi',      'name' : 'urpmi' },
		#                 { 'path' : '/usr/bin/pacman',      'name' : 'pacman' },
		#                 { 'path' : '/bin/opkg',            'name' : 'opkg' },
		#                 { 'path' : '/opt/local/bin/pkgin', 'name' : 'pkgin' },
		#                 { 'path' : '/opt/local/bin/port',  'name' : 'macports' },
		#                 { 'path' : '/usr/sbin/pkg',        'name' : 'pkgng' },
		#                 { 'path' : '/usr/sbin/swlist',     'name' : 'SD-UX' },
		#                 { 'path' : '/usr/sbin/pkgadd',     'name' : 'svr4pkg' },
		#                 { 'path' : '/usr/bin/pkg',         'name' : 'pkg' },
		#    ]
		if cfg['build']['distro_override'] != '':
			key = cfg['build']['distro_override']
			distro = cfg['build']['distro_override']
			install_type = package_map.INSTALL_TYPE_MAP[key]
			distro_version = ''
			if install_type == 'apt' and cfg['build']['delivery'] in ('docker','dockerfile'):
				if not self.command_available('lsb_release'):
					if not cfg['build']['apt_update_done']:
						cfg['build']['apt_update_done'] = True
						shutit_global.shutit.send('apt-get update && apt-get install -y -qq lsb-release',loglevel=loglevel,delaybeforesend=delaybeforesend)
				d = self.lsb_release()
				install_type   = d['install_type']
				distro         = d['distro']
				distro_version = d['distro_version']
			elif install_type == 'yum' and cfg['build']['delivery'] in ('docker', 'dockerfile'):
				if not cfg['build']['yum_update_done']:
					cfg['build']['yum_update_done'] = True
					shutit_global.shutit.send('yum update -y',exit_values=['0','1'],loglevel=logging.INFO,delaybeforesend=delaybeforesend)
				if self.file_exists('/etc/redhat-release'):
					output = self.send_and_get_output('cat /etc/redhat-release',echo=False, loglevel=loglevel,delaybeforesend=delaybeforesend)
					if re.match('^centos.*$', output.lower()) or re.match('^red hat.*$', output.lower()) or re.match('^fedora.*$', output.lower()) or True:
						self.send_and_match_output('yum install -y -t redhat-lsb epel-release','Complete!',loglevel=loglevel,delaybeforesend=delaybeforesend)
				else:
					if not self.command_available('lsb_release'):
						shutit_global.shutit.send('yum install -y lsb-release',loglevel=loglevel,delaybeforesend=delaybeforesend)
				install_type   = d['install_type']
				distro         = d['distro']
				distro_version = d['distro_version']
			elif install_type == 'apk' and cfg['build']['delivery'] in ('docker','dockerfile'):
				if not cfg['build']['apk_update_done']:
					cfg['build']['apk_update_done'] = True
					shutit_global.shutit.send('apk update',loglevel=logging.INFO,delaybeforesend=delaybeforesend)
				shutit_global.shutit.send('apk add bash',loglevel=loglevel,delaybeforesend=delaybeforesend)
				install_type   = 'apk'
				distro         = 'alpine'
				distro_version = '1.0'
			elif install_type == 'emerge' and cfg['build']['delivery'] in ('docker','dockerfile'):
				shutit_global.shutit.send('emerge --sync',loglevel=loglevel,delaybeforesend=delaybeforesend)
				install_type = 'emerge'
				distro = 'gentoo'
				distro_version = '1.0'
			elif install_type == 'docker' and cfg['build']['delivery'] in ('docker','dockerfile'):
				distro = 'coreos'
				distro_version = '1.0'
		elif cfg['environment'][environment_id]['setup'] and self.command_available('lsb_release'):
			d = self.lsb_release()
			install_type   = d['install_type']
			distro         = d['distro']
			distro_version = d['distro_version']
		else:
			# Don't check for existence of file to save a little time.
			issue_output = self.send_and_get_output(' cat /etc/issue',echo=False, loglevel=loglevel,delaybeforesend=delaybeforesend).lower()
			if not re.match('.*No such file.*',issue_output):
				for key in package_map.INSTALL_TYPE_MAP.keys():
					if issue_output.find(key) != -1:
						distro       = key
						install_type = package_map.INSTALL_TYPE_MAP[key]
						break
			elif self.file_exists('/cygdrive'):
				distro       = 'cygwin'
				install_type = 'apt-cyg'
			if install_type == '' or distro == '':
				if self.file_exists('/etc/os-release'):
					os_name = self.send_and_get_output(' cat /etc/os-release | grep ^NAME',echo=False, loglevel=loglevel,delaybeforesend=delaybeforesend).lower()
					if os_name.find('centos') != -1:
						distro       = 'centos'
						install_type = 'yum'
					elif os_name.find('red hat') != -1:
						distro       = 'red hat'
						install_type = 'yum'
					elif os_name.find('fedora') != -1:
						# TODO: distinguish with dnf - fedora 23+? search for dnf in here
						distro       = 'fedora'
						install_type = 'yum'
					elif os_name.find('gentoo') != -1:
						distro       = 'gentoo'
						install_type = 'emerge'
					elif os_name.find('coreos') != -1:
						distro       = 'coreos'
						install_type = 'docker'
				elif self.send_and_get_output("uname -a | awk '{print $1}'",echo=False, loglevel=loglevel,delaybeforesend=delaybeforesend) == 'Darwin':
					distro = 'osx'
					install_type = 'brew'
					if not self.command_available('brew'):
						shutit_global.shutit.fail('ShutiIt requires brew be installed. See http://brew.sh for details on installation.')
					for package in ('coreutils','findutils','gnu-tar','gnu-sed','gawk','gnutls','gnu-indent','gnu-getopt'):
						if self.send_and_get_output('brew list | grep -w ' + package,echo=False, loglevel=loglevel,delaybeforesend=delaybeforesend) == '':
							shutit_global.shutit.send('brew install ' + package,loglevel=loglevel,delaybeforesend=delaybeforesend)
				if install_type == '' or distro == '':
					shutit_global.shutit.fail('Could not determine Linux distro information. ' + 'Please inform ShutIt maintainers.', shutit_pexpect_child=self.pexpect_child)
			# The call to self.package_installed with lsb-release above
			# may fail if it doesn't know the install type, so
			# if we've determined that now
			if install_type == 'apt' and cfg['build']['delivery'] in ('docker','dockerfile'):
				if not self.command_available('lsb_release'):
					if not cfg['build']['apt_update_done']:
						cfg['build']['apt_update_done'] = True
						shutit_global.shutit.send('apt-get update && apt-get install -y -qq lsb-release',loglevel=loglevel,delaybeforesend=delaybeforesend)
					cfg['build']['apt_update_done'] = True
					shutit_global.shutit.send('apt-get install -y -qq lsb-release',loglevel=loglevel,delaybeforesend=delaybeforesend)
				d = self.lsb_release()
				install_type   = d['install_type']
				distro         = d['distro']
				distro_version = d['distro_version']
			elif install_type == 'yum' and cfg['build']['delivery'] in ('docker','dockerfile'):
				if self.file_exists('/etc/redhat-release'):
					output = shutit_global.shutit.send_and_get_output('cat /etc/redhat-release',echo=False, loglevel=loglevel,delaybeforesend=delaybeforesend)
					if re.match('^centos.*$', output.lower()) or re.match('^red hat.*$', output.lower()) or re.match('^fedora.*$', output.lower()) or True:
						self.send_and_match_output('yum install -y -t redhat-lsb epel-release','Complete!',loglevel=loglevel,delaybeforesend=delaybeforesend)
				else:
					if not self.command_available('lsb_release'):
						shutit_global.shutit.send('yum install -y lsb-release',loglevel=loglevel,delaybeforesend=delaybeforesend)
				d = self.lsb_release()
				install_type   = d['install_type']
				distro         = d['distro']
				distro_version = d['distro_version']
			elif install_type == 'apk' and cfg['build']['delivery'] in ('docker','dockerfile'):
				if not cfg['build']['apk_update_done']:
					cfg['build']['apk_update_done'] = True
					shutit_global.shutit.send('apk update',loglevel=logging.INFO,delaybeforesend=delaybeforesend)
				shutit_global.shutit.send('apk install bash',loglevel=loglevel,delaybeforesend=delaybeforesend)
				install_type   = 'apk'
				distro         = 'alpine'
				distro_version = '1.0'
			elif install_type == 'emerge' and cfg['build']['delivery'] in ('docker','dockerfile'):
				if not cfg['build']['emerge_update_done']:
					shutit_global.shutit.send('emerge --sync',loglevel=logging.INFO,delaybeforesend=delaybeforesend)
				install_type = 'emerge'
				distro = 'gentoo'
				distro_version = '1.0'
		# We should have the distro info now, let's assign to target config
		# if this is not a one-off.
		cfg['environment'][environment_id]['install_type']   = install_type
		cfg['environment'][environment_id]['distro']         = distro
		cfg['environment'][environment_id]['distro_version'] = distro_version



	def multisend(self,
	              send,
	              send_dict,
	              expect=None,
	              timeout=3600,
	              check_exit=None,
	              fail_on_empty_before=True,
	              record_command=True,
	              exit_values=None,
	              escape=False,
	              echo=None,
	              note=None,
	              delaybeforesend=0,
	              loglevel=logging.DEBUG):
		"""Multisend. Same as send, except it takes multiple sends and expects in a dict that are
		processed while waiting for the end "expect" argument supplied.

		@param send_dict:            dict of sends and expects, eg: {'interim prompt:','some input','other prompt','some other input'}
		@param expect:               String or list of strings of final expected output that returns from this function. See send()
		@param send:                 See send()
		@param timeout:              See send()
		@param check_exit:           See send()
		@param fail_on_empty_before: See send()
		@param record_command:       See send()
		@param exit_values:          See send()
		@param echo:                 See send()
		@param note:                 See send()
		"""
		expect = expect or self.default_expect
		shutit_global.shutit._handle_note(note)
		send_iteration = send
		expect_list = send_dict.keys()
		# Put breakout item(s) in last.
		n_breakout_items = 0
		if type(expect) == str:
			expect_list.append(expect)
			n_breakout_items = 1
		elif type(expect) == list:
			for item in expect:
				expect_list.append(item)
				n_breakout_items += 1
		while True:
			# If it's the last n items in the list, it's the breakout one.
			res = shutit_global.shutit.send(send_iteration, expect=expect_list, shutit_pexpect_child=self.pexpect_child, check_exit=check_exit, fail_on_empty_before=fail_on_empty_before, timeout=timeout, record_command=record_command, exit_values=exit_values, echo=echo, escape=escape, loglevel=loglevel, delaybeforesend=delaybeforesend)
			if res >= len(expect_list) - n_breakout_items:
				break
			else:
				send_iteration = send_dict[expect_list[res]]
		shutit_global.shutit._handle_note_after(note=note)
		return res


	def send_until(self,
	               send,
	               regexps,
	               not_there=False,
	               cadence=5,
	               retries=100,
	               echo=False,
	               note=None,
	               delaybeforesend=0,
	               loglevel=logging.INFO):
		"""Send string on a regular cadence until a string is either seen, or the timeout is triggered.

		@param send:                 See send()
		@param regexps:              List of regexps to wait for.
		@param not_there:            If True, wait until this a regexp is not seen in the output. If False
		                             wait until a regexp is seen in the output (default)
		@param echo:                 See send()
		@param note:                 See send()
		"""
		shutit_global.shutit._handle_note(note, command=send + ' until one of these seen: ' + str(regexps))
		shutit_global.shutit.log('Sending: "' + send + '" until one of these regexps seen: ' + str(regexps),level=loglevel)
		if type(regexps) == str:
			regexps = [regexps]
		if type(regexps) != list:
			shutit_global.shutit.fail('regexps should be list')
		while retries > 0:
			retries -= 1
			output = self.send_and_get_output(send, retry=1, strip=True,echo=echo, loglevel=loglevel, fail_on_empty_before=False, delaybeforesend=delaybeforesend)
			if not not_there:
				for regexp in regexps:
					if not shutit_util.check_regexp(regexp):
						shutit_global.shutit.fail('Illegal regexp found in send_until call: ' + regexp)
					if shutit_util.match_string(output, regexp):
						return True
			else:
				# Only return if _not_ seen in the output
				missing = False
				for regexp in regexps:
					if not shutit_util.check_regexp(regexp):
						shutit_global.shutit.fail('Illegal regexp found in send_until call: ' + regexp)
					if not shutit_util.match_string(output, regexp):
						missing = True
						break
				if missing:
					shutit_global.shutit._handle_note_after(note=note)
					return True
			time.sleep(cadence)
		shutit_global.shutit._handle_note_after(note=note)
		return False


	def change_text(self,
	                text,
	                fname,
	                pattern=None,
	                before=False,
	                force=False,
	                delete=False,
	                note=None,
	                replace=False,
	                line_oriented=True,
	                create=True,
	                delaybeforesend=0,
	                loglevel=logging.DEBUG):

		"""Change text in a file.

		Returns None if there was no match for the regexp, True if it was matched
		and replaced, and False if the file did not exist or there was some other
		problem.

		@param text:          Text to insert.
		@param fname:         Filename to insert text to
		@param pattern:       Regexp for a line to match and insert after/before/replace.
		                      If none, put at end of file.
		@param expect:        See send()
		@param shutit_pexpect_child:         See send()
		@param before:        Whether to place the text before or after the matched text.
		@param force:         Force the insertion even if the text is in the file.
		@param delete:        Delete text from file rather than insert
		@param replace:       Replace matched text with passed-in text. If nothing matches, then append.
		@param note:          See send()
		@param line_oriented: Consider the pattern on a per-line basis (default True).
		                      Can match any continuous section of the line, eg 'b.*d' will match the line: 'abcde'
		                      If not line_oriented, the regexp is considered on with the flags re.DOTALL, re.MULTILINE
		                      enabled
		"""
		shutit_global.shutit._handle_note(note)
		fexists = self.file_exists(fname)
		if not fexists:
			if create:
				shutit_global.shutit.send(' touch ' + fname,shutit_pexpect_child=self.pexpect_child, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
			else:
				shutit_global.shutit.fail(fname + ' does not exist and create=False')
		if replace:
			# If replace and no pattern FAIL
			if not pattern:
				shutit_global.shutit.fail('replace=True requires a pattern to be passed in')
			# If replace and delete FAIL
			if delete:
				shutit_global.shutit.fail('cannot pass replace=True and delete=True to insert_text')
		if self.command_available('base64'):
			ftext = self.send_and_get_output(' base64 ' + fname, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
			ftext = base64.b64decode(ftext)
		else:
			ftext = self.send_and_get_output('cat ' + fname, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
		# Replace the file text's ^M-newlines with simple newlines
		ftext = ftext.replace('\r\n','\n')
		# If we are not forcing and the text is already in the file, then don't insert.
		if delete:
			loc = ftext.find(text)
			if loc == -1:
				# No output - no match
				return None
			else:
				new_text = ftext[:loc] + ftext[loc+len(text)+1:]
		else:
			if pattern != None:
				if not line_oriented:
					if not shutit_util.check_regexp(pattern):
						shutit_global.shutit.fail('Illegal regexp found in change_text call: ' + pattern)
					# cf: http://stackoverflow.com/questions/9411041/matching-ranges-of-lines-in-python-like-sed-ranges
					sre_match = re.search(pattern,ftext,re.DOTALL|re.MULTILINE)
					if replace:
						if sre_match == None:
							cut_point = len(ftext)
							newtext1 = ftext[:cut_point]
							newtext2 = ftext[cut_point:]
						else:
							cut_point = sre_match.start()
							cut_point_after = sre_match.end()
							newtext1 = ftext[:cut_point]
							newtext2 = ftext[cut_point_after:]
					else:
						if sre_match == None:
							# No output - no match
							return None
						elif before:
							cut_point = sre_match.start()
							# If the text is already there and we're not forcing it, return None.
							if not force and ftext[cut_point-len(text):].find(text) > 0:
								return None
						else:
							cut_point = sre_match.end()
							# If the text is already there and we're not forcing it, return None.
							if not force and ftext[cut_point:].find(text) > 0:
								return None
						newtext1 = ftext[:cut_point]
						newtext2 = ftext[cut_point:]
				else:
					lines = ftext.split('\n')
					cut_point   = 0
					line_length = 0
					matched     = False
					if not shutit_util.check_regexp(pattern):
						shutit_global.shutit.fail('Illegal regexp found in change_text call: ' + pattern)
					for line in lines:
						#Help the user out to make this properly line-oriented
						pattern_before=''
						pattern_after=''
						if len(pattern) == 0 or pattern[0] != '^':
							pattern_before = '^.*'
						if len(pattern) == 0 or pattern[-1] != '$':
							pattern_after = '.*$'
						new_pattern = pattern_before+pattern+pattern_after
						match = re.search(new_pattern, line)
						line_length = len(line)
						if match != None:
							matched=True
							break
						# Update cut point to next line, including newline in original text
						cut_point += line_length+1
					if not replace and not matched:
						# No match, return none
						return None
					if replace and not matched:
						cut_point = len(ftext)
					elif not replace and not before:
						cut_point += line_length
					newtext1 = ftext[:cut_point]
					newtext2 = ftext[cut_point:]
					if replace and matched:
						newtext2 = ftext[cut_point+line_length:]
					elif not force:
						# If the text is already there and we're not forcing it, return None.
						if before and ftext[cut_point-len(text):].find(text) > 0:
							return None
						# If the text is already there and we're not forcing it, return None.
						if not before and ftext[cut_point:].find(text) > 0:
							return None
					if len(newtext1) > 0 and newtext1[-1] != '\n':
						newtext1 += '\n'
					if len(newtext2) > 0 and newtext2[0] != '\n':
						newtext2 = '\n' + newtext2
			else:
				# Append to file absent a pattern.
				cut_point = len(ftext)
				newtext1 = ftext[:cut_point]
				newtext2 = ftext[cut_point:]
			# If adding or replacing at the end of the file, then ensure we have a newline at the end
			if newtext2 == '' and len(text) > 0 and text[-1] != '\n':
				newtext2 = '\n'
			new_text = newtext1 + text + newtext2
		shutit_global.shutit.send_file(fname,new_text,truncate=True,loglevel=loglevel, delaybeforesend=delaybeforesend)
		shutit_global.shutit._handle_note_after(note=note)
		return True




	def remove_line_from_file(self,
							  line,
							  filename,
							  match_regexp=None,
							  literal=False,
	                          note=None,
	                          delaybeforesend=0,
	                          loglevel=logging.DEBUG):
		"""Removes line from file, if it exists.
		Must be exactly the line passed in to match.
		Returns True if there were no problems, False if there were.
	
		@param line:          Line to remove.
		@param filename       Filename to remove it from.
		@param match_regexp:  If supplied, a regexp to look for in the file
		                      instead of the line itself,
		                      handy if the line has awkward characters in it.
		@param literal:       If true, then simply grep for the exact string without
		                      bash interpretation. (Default: False)
		@param note:          See send()

		@type line:           string
		@type filename:       string
		@type match_regexp:   string
		@type literal:        boolean

		@return:              True if the line was matched and deleted, False otherwise.
		@rtype:               boolean
		"""
		shutit_global.shutit._handle_note(note)
		# assume we're going to add it
		tmp_filename = '/tmp/' + shutit_util.random_id()
		if self.file_exists(filename):
			if literal:
				if match_regexp == None:
					#            v the space is intentional, to avoid polluting bash history.
					shutit_global.shutit.send(""" grep -v '^""" + line + """$' """ + filename + ' > ' + tmp_filename, shutit_pexpect_child=self.pexpect_child, exit_values=['0', '1'], echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
				else:
					if not shutit_util.check_regexp(match_regexp):
						shutit_global.shutit.fail('Illegal regexp found in remove_line_from_file call: ' + match_regexp)
					#            v the space is intentional, to avoid polluting bash history.
					shutit_global.shutit.send(""" grep -v '^""" + match_regexp + """$' """ + filename + ' > ' + tmp_filename, shutit_pexpect_child=self.pexpect_child, exit_values=['0', '1'], echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
			else:
				if match_regexp == None:
					#          v the space is intentional, to avoid polluting bash history.
					shutit_global.shutit.send(' grep -v "^' + line + '$" ' + filename + ' > ' + tmp_filename, shutit_pexpect_child=self.pexpect_child, exit_values=['0', '1'], echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
				else:
					if not shutit_util.check_regexp(match_regexp):
						shutit_global.shutit.fail('Illegal regexp found in remove_line_from_file call: ' + match_regexp)
					#          v the space is intentional, to avoid polluting bash history.
					shutit_global.shutit.send(' grep -v "^' + match_regexp + '$" ' + filename + ' > ' + tmp_filename, shutit_pexpect_child=self.pexpect_child, exit_values=['0', '1'], echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
			shutit_global.shutit.send(' cat ' + tmp_filename + ' > ' + filename, shutit_pexpect_child=self.pexpect_child, check_exit=False, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
			shutit_global.shutit.send(' rm -f ' + tmp_filename, shutit_pexpect_child=self.pexpect_child, exit_values=['0', '1'], echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
		shutit_global.shutit._handle_note_after(note=note)
		return True


	#TODO: create environment object
	#TODO: review items in cfg and see if they make more sense in the pexpect object
	#TODO: replace 'target' in cfg
