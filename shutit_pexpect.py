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
import package_map
import re
import base64
import sys
import textwrap
try:
	from md5 import md5
except ImportError:
	from hashlib import md5
from shutit_module import ShutItFailException


PY3 = (sys.version_info[0] >= 3)


class ShutItPexpectSession(object):

	def __init__(self,
	             pexpect_session_id,
				 command,
	             args=[],
				 timeout=300,
	             maxread=2000,
	             searchwindowsize=None,
	             logfile=None,
	             env=None,
	             ignore_sighup=False,
	             echo=True,
	             preexec_fn=None,
	             encoding=None,
	             codec_errors='strict',
	             dimensions=None,
	             delaybeforesend=0.05):
		"""spawn a child, and manage the delaybefore send setting to 0
		"""
		if PY3:
			encoding = 'utf-8'
		shutit = shutit_global.shutit
		self.check_exit          = True
		self.default_expect      = [shutit.expect_prompts['base_prompt']]
		self.pexpect_session_id  = pexpect_session_id
		self.login_stack         = []
		self.current_environment = None
		self.pexpect_child       = self._spawn_child(command=command,
		                                             args=args,
		                                             timeout=timeout,
		                                             maxread=maxread,
		                                             searchwindowsize=searchwindowsize,
		                                             logfile=logfile,
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
					env=None,
					ignore_sighup=False,
					echo=True,
					preexec_fn=None,
					encoding=None,
					codec_errors='strict',
					dimensions=None,
					delaybeforesend=0.05):
		"""spawn a child, and manage the delaybefore send setting to 0
		"""
		shutit = shutit_global.shutit
		pexpect_child = pexpect.spawn(command,
		                              args=args,
		                              timeout=timeout,
		                              maxread=maxread,
		                              searchwindowsize=searchwindowsize,
		                              logfile=logfile,
		                              env=env,
		                              ignore_sighup=ignore_sighup,
		                              echo=echo,
		                              preexec_fn=preexec_fn,
		                              encoding=encoding,
		                              codec_errors=codec_errors,
		                              dimensions=dimensions)
		pexpect_child.delaybeforesend=delaybeforesend
		shutit.log('sessions before: ' + str(shutit.shutit_pexpect_sessions),level=logging.DEBUG)
		shutit.shutit_pexpect_sessions.update({self.pexpect_session_id:self})
		shutit.log('sessions after: ' + str(shutit.shutit_pexpect_sessions),level=logging.DEBUG)
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
		shutit = shutit_global.shutit
		r_id = shutit_util.random_id()
		if prompt_prefix == None:
			prompt_prefix = r_id
		# Be helpful.
		if ' ' in user:
			shutit.fail('user has space in it - did you mean: login(command="' + user + '")?')
		if shutit.build['delivery'] == 'bash' and command == 'su -':
			# We want to retain the current working directory
			command = 'su'
		# If this is a su-type command, add the user, else assume user is in the command.
		if command == 'su -' or command == 'su' or command == 'login':
			send = command + ' ' + user
		else:
			send = command
		if expect == None:
			login_expect = shutit.expect_prompts['base_prompt']
		else:
			login_expect = expect
		# We don't fail on empty before as many login programs mess with the output.
		# In this special case of login we expect either the prompt, or 'user@' as this has been seen to work.
		general_expect = [login_expect]
		# Add in a match if we see user+ and then the login matches. Be careful not to match against 'user+@...password:'
		general_expect = general_expect + [user+'@.*'+'[@#$]']
		# If not an ssh login, then we can match against user + @sign because it won't clash with 'user@adasdas password:'
		if not command.find('ssh') == 0:
			general_expect = general_expect + [user+'@']
			general_expect = general_expect + ['.*[@#$]']
		if user == 'bash' and command == 'su -':
			shutit.log('WARNING! user is bash - if you see problems below, did you mean: login(command="' + user + '")?',level=loglevel.WARNING)
		shutit._handle_note(note,command=command + '\n\n[as user: "' + user + '"]',training_input=send)
		# r'[^t] login:' - be sure not to match 'last login:'
		#if send == 'bash':
		echo=False
		self.multisend(send,{'ontinue connecting':'yes','assword':password,r'[^t] login:':password},expect=general_expect,check_exit=False,timeout=timeout,fail_on_empty_before=False,escape=escape,echo=echo,loglevel=loglevel)
		if prompt_prefix != None:
			self.setup_prompt(r_id,prefix=prompt_prefix)
		else:
			self.setup_prompt(r_id)
		if go_home:
			self.send('cd',check_exit=False, echo=False, loglevel=loglevel)
		self.login_stack_append(r_id)
		shutit._handle_note_after(note=note,training_input=send)
		# Try and stop user being 'clever'
		if shutit.build['testing']:
			shutit.send(' alias exit=/bin/true',echo=False,record_command=False)
			shutit.send(' alias logout=/bin/true',echo=False,record_command=False)
			shutit.send(' alias kill=/bin/true',echo=False,record_command=False)
			shutit.send(' alias alias=/bin/true',echo=False,record_command=False)
		return True



	def logout(self,
			   expect=None,
			   command='exit',
			   note=None,
			   timeout=5,
			   loglevel=logging.DEBUG):
		"""Logs the user out. Assumes that login has been called.
		If login has never been called, throw an error.

			@param expect:  See send()
			@param command: Command to run to log out (default=exit)
			@param note:    See send()
		"""
		shutit = shutit_global.shutit
		shutit._handle_note(note,training_input=command)
		if shutit.build['testing']:
			shutit.send(' unalias exit',echo=False,record_command=False)
			shutit.send(' unalias logout',echo=False,record_command=False)
			shutit.send(' unalias kill',echo=False,record_command=False)
			shutit.send(' unalias alias',echo=False,record_command=False)
		if len(self.login_stack):
			_ = self.login_stack.pop()
			if len(self.login_stack):
				old_prompt_name	 = self.login_stack[-1]
				self.default_expect = shutit.expect_prompts[old_prompt_name]
			else:
				# If none are on the stack, we assume we're going to the root prompt
				# set up in shutit_setup.py
				shutit.set_default_shutit_pexpect_session_expect()
		else:
			shutit.fail('Logout called without corresponding login', throw_exception=False)
		# No point in checking exit here, the exit code will be
		# from the previous command from the logged in session
		self.send(command, expect=expect, check_exit=False, fail_on_empty_before=False, timeout=timeout,echo=False, loglevel=loglevel)
		shutit._handle_note_after(note=note)


	def login_stack_append(self, r_id):
		self.login_stack.append(r_id)
		return True


	def setup_prompt(self,
	                 prompt_name,
	                 prefix='default',
	                 loglevel=logging.DEBUG):
		"""Use this when you've opened a new shell to set the PS1 to something
		sane. By default, it sets up the default expect so you don't have to
		worry about it and can just call shutit.send('a command').
		
		If you want simple login and logout, please use login() and logout()
		within this module.
		
		Typically it would be used in this boilerplate pattern::
		
		    shutit.send('su - auser', expect=shutit.expect_prompts['base_prompt'], check_exit=False)
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
		shutit = shutit_global.shutit
		local_prompt = prefix + '#' + shutit_util.random_id() + '> '
		shutit.expect_prompts[prompt_name] = local_prompt
		# Set up the PS1 value.
		# Unset the PROMPT_COMMAND as this can cause nasty surprises in the output.
		# Set the cols value, as unpleasant escapes are put in the output if the
		# input is > n chars wide.
		# checkwinsize is required for similar reasons.
		# The newline in the expect list is a hack. On my work laptop this line hangs
		# and times out very frequently. This workaround seems to work, but I
		# haven't figured out why yet - imiell.
		self.send((" export SHUTIT_BACKUP_PS1_%s=$PS1 && PS1='%s' && unset PROMPT_COMMAND && stty cols " + str(shutit.build['stty_cols'])) % (prompt_name, local_prompt), expect=['\r\n' + shutit.expect_prompts[prompt_name]], fail_on_empty_before=False, timeout=5, echo=False, loglevel=loglevel)
		shutit.log('Resetting default expect to: ' + shutit.expect_prompts[prompt_name],level=logging.DEBUG)
		self.default_expect = shutit.expect_prompts[prompt_name]
		# These two lines are required to make the terminal sane. They are best endeavours,
		# they might fail (eg if we are not in bash) so we keep them separate and do not check whether it succeeded.
		self.send(' shopt -s checkwinsize', check_exit=False, echo=False, loglevel=loglevel)
		self.send(' stty sane',             check_exit=False, echo=False, loglevel=loglevel)
		# Set up history the way shutit likes it.
		self.send(' export HISTCONTROL=$HISTCONTROL:ignoredups:ignorespace', echo=False, loglevel=loglevel)
		# Ensure environment is set up OK.
		_ = self.init_pexpect_session_environment(prefix)
		return True


	def revert_prompt(self,
	                  old_prompt_name,
	                  new_expect=None):
		"""Reverts the prompt to the previous value (passed-in).
		
		It should be fairly rare to need this. Most of the time you would just
		exit a subshell rather than resetting the prompt.
		
		    - old_prompt_name -
		    - new_expect      -
		    - child           - See send()
		"""
		shutit = shutit_global.shutit
		expect = new_expect or self.default_expect
		#           v the space is intentional, to avoid polluting bash history.
		self.send((' PS1="${SHUTIT_BACKUP_PS1_%s}" && unset SHUTIT_BACKUP_PS1_%s') % (old_prompt_name, old_prompt_name), expect=expect, check_exit=False, fail_on_empty_before=False, echo=False, loglevel=logging.DEBUG)
		if not new_expect:
			shutit.log('Resetting default expect to default',level=logging.DEBUG)
			shutit.set_default_shutit_pexpect_session_expect()
		_ = self.init_pexpect_session_environment(old_prompt_name)


	def pexpect_send(self, string):
		self.pexpect_child.send(string)
		return True


	def sendline(self, string):
		self.pexpect_send(string+'\n')
		return True


	def expect(self,
			   expect,
	           searchwindowsize=None,
	           delaybeforesend=None,
	           maxread=None,
			   timeout=None):
		"""Handle child expects, with EOF and TIMEOUT handled
		"""
		if type(expect) == str:
			expect = [expect]
		if searchwindowsize != None:
			old_searchwindowsize = self.pexpect_child.searchwindowsize
			self.pexpect_child.searchwindowsize = searchwindowsize
		if maxread != None:
			old_maxread = self.pexpect_child.maxread
			self.pexpect_child.maxread = maxread
		if delaybeforesend != None:
			old_delaybeforesend = self.pexpect_child.delaybeforesend
			self.pexpect_child.delaybeforesend = delaybeforesend
		res = self.pexpect_child.expect(expect + [pexpect.TIMEOUT] + [pexpect.EOF], timeout=timeout)
		if searchwindowsize != None:
			self.pexpect_child.searchwindowsize = old_searchwindowsize
		if maxread != None:
			self.pexpect_child.maxread = old_maxread
		if delaybeforesend != None:
			self.pexpect_child.maxread = old_delaybeforesend
		return res


	def replace_container(self, new_target_image_name):
		"""Replaces a container. Assumes we are in Docker context
		"""
		shutit = shutit_global.shutit
		shutit.log('Replacing container, please wait...',level=logging.INFO)
		shutit.log(shutit.print_session_state(),level=logging.DEBUG)

		# Destroy existing container.
		conn_module = None
		for mod in shutit.conn_modules:
			if mod.module_id == shutit.build['conn_module']:
				conn_module = mod
				break
		if conn_module is None:
			shutit.fail('''Couldn't find conn_module ''' + shutit.build['conn_module'])
		container_id = shutit.target['container_id']
		conn_module.destroy_container('host_child', 'target_child', container_id)
		
		# Start up a new container.
		shutit.target['docker_image'] = new_target_image_name
		target_child = conn_module.start_container(self.pexpect_session_id)
		conn_module.setup_target_child(target_child)
		shutit.log('Container replaced',level=logging.INFO)
		shutit.log(shutit.print_session_state(),level=logging.DEBUG)
		# New session - log in. This makes the assumption that we are nested
		# the same level in in terms of shells (root shell + 1 new login shell).
		target_child = shutit.get_shutit_pexpect_session_from_id('target_child')
		target_child.login(command='bash --noprofile --norc')
		return True


	def whoami(self,
	           note=None,
	           loglevel=logging.DEBUG):
		"""Returns the current user by executing "whoami".

		@param note:     See send()

		@return: the output of "whoami"
		@rtype: string
		"""
		shutit = shutit_global.shutit
		shutit._handle_note(note)
		res = self.send_and_get_output(' whoami',echo=False, loglevel=loglevel).strip()
		shutit._handle_note_after(note=note)
		return res


#	def setup_environment(self,
#	                      prefix,
#	                      loglevel=logging.DEBUG):
#		"""If we are in a new environment then set up a new data structure.
#		A new environment is a new machine environment, whether that's
#		over ssh, docker, whatever.
#		If we are not in a new environment ensure the env_id is correct.
#		Returns the environment id every time.
#		"""
#		# Set this to be the default session.
#		shutit = shutit_global.shutit
#		shutit.set_default_shutit_pexpect_session(self)
#		cfg = shutit.cfg
#		environment_id_dir = shutit.build['shutit_state_dir'] + '/environment_id'
#		if self.file_exists(environment_id_dir,directory=True):
#			files = self.ls(environment_id_dir)
#			if len(files) != 1 or type(files) != list:
#				if len(files) == 2 and (files[0] == 'ORIGIN_ENV' or files[1] == 'ORIGIN_ENV'):
#					for f in files:
#						if f != 'ORIGIN_ENV':
#							environment_id = f
#							shutit.build['current_environment_id'] = environment_id
#							# Workaround for CygWin terminal issues. If the envid isn't in the cfg item
#							# Then crudely assume it is. This will drop through and then assume we are in the origin env.
#							try:
#								_=shutit.environment[shutit.build['current_environment_id']]
#							except Exception:
#								shutit.build['current_environment_id'] = 'ORIGIN_ENV'
#							break
#				else:
#					# See comment above re: cygwin.
#					if self.file_exists('/cygdrive'):
#						shutit.build['current_environment_id'] = 'ORIGIN_ENV'
#					else:
#						shutit.fail('Wrong number of files in environment_id_dir: ' + environment_id_dir)
#			else:
#				if self.file_exists('/cygdrive'):
#					environment_id = 'ORIGIN_ENV'
#				else:
#					environment_id = files[0]
#			if shutit.build['current_environment_id'] != environment_id:
#				# Clean out any trace of this new environment, and return the already-existing one.
#				self.send(' rm -rf ' + environment_id_dir + '/environment_id/' + environment_id, echo=False, loglevel=loglevel)
#				return shutit.build['current_environment_id']
#			if not environment_id == 'ORIGIN_ENV':
#				return environment_id
#		# Origin environment is a special case.
#		if prefix == 'ORIGIN_ENV':
#			environment_id = prefix
#		else:
#			environment_id = shutit_util.random_id()
#		shutit.build['current_environment_id']                             = environment_id
#		shutit.environment[environment_id] = {}
#		# Directory to revert to when delivering in bash and reversion to directory required.
#		shutit.environment[environment_id]['module_root_dir']              = '/'
#		shutit.environment[environment_id]['modules_installed']            = [] # has been installed (in this build)
#		shutit.environment[environment_id]['modules_not_installed']        = [] # modules _known_ not to be installed
#		shutit.environment[environment_id]['modules_ready']                = [] # has been checked for readiness and is ready (in this build)
#		# Installed file info
#		shutit.environment[environment_id]['modules_recorded']             = []
#		shutit.environment[environment_id]['modules_recorded_cache_valid'] = False
#		# Exempt the ORIGIN_ENV from getting distro info
#		if prefix != 'ORIGIN_ENV':
#			self.get_distro_info(environment_id)
#		fname = environment_id_dir + '/' + environment_id
#		#self.send(' mkdir -p ' + environment_id_dir + ' && chmod -R 777 ' + shutit.build['shutit_state_dir_base'] + ' && touch ' + fname, echo=False, loglevel=loglevel)
#		return environment_id


	def create_command_file(self, expect, send):
		"""Internal function. Do not use.

		Takes a long command, and puts it in an executable file ready to run. Returns the filename.
		"""
		shutit = shutit_global.shutit
		random_id = shutit_util.random_id()
		fname = shutit.build['shutit_state_dir_base'] + '/tmp_' + random_id
		working_str = send
		# truncate -s must be used as --size is not supported everywhere (eg busybox)
		self.sendline(' truncate -s 0 '+ fname)
		self.pexpect_child.expect(expect)
		size = shutit.build['stty_cols'] - 25
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
		shutit = shutit_global.shutit
		expect = expect or self.default_expect
		if not self.check_exit:
			shutit.log('check_exit configured off, returning', level=logging.DEBUG)
			return True
		if exit_values is None:
			exit_values = ['0']
		if type(exit_values) == int:
			exit_values = [str(exit_values)]
		# Don't use send here (will mess up last_output)!
		# Space before "echo" here is sic - we don't need this to show up in bash history
		self.sendline(' echo EXIT_CODE:$?')
		while True:
			# Sometimes pexpect gets confused at this point, so we expect again until all appears ok.
			shutit.log('Expecting: ' + str(expect),level=logging.DEBUG)
			self.expect(expect,timeout=5)
			res = shutit_util.match_string(str(self.pexpect_child.before), '^EXIT_CODE:([0-9][0-9]?[0-9]?)$')
			if res == None:
				# Try before without anchor - sometimes needed when logging into obscure shells
				shutit.log('Un-clean login (1), trying: ' + str(self.pexpect_child.before), level=logging.DEBUG)
				res = shutit_util.match_string(str(self.pexpect_child.before), '.*EXIT_CODE:([0-9][0-9]?[0-9]?)$')
			if res == None:
				# Try after - for some reason needed after login
				shutit.log('Un-clean login (2), trying: ' + str(self.pexpect_child.after), level=logging.DEBUG)
				res = shutit_util.match_string(str(self.pexpect_child.after), '^EXIT_CODE:([0-9][0-9]?[0-9]?)$')
			if res == None:
				# Try after without anchor - sometimes needed when logging into obscure 
				shutit.log('Un-clean login (3), trying: ' + str(self.pexpect_child.after), level=logging.DEBUG)
				res = shutit_util.match_string(str(self.pexpect_child.after), '^.*EXIT_CODE:([0-9][0-9]?[0-9]?)$')
			if res != None:
				break
		if res not in exit_values or res == None:
			if res == None:
				res = str(res)
			shutit.log('shutit_pexpect_child.after: ' + str(self.pexpect_child.after), level=logging.DEBUG)
			shutit.log('Exit value from command: ' + str(send) + ' was:' + res, level=logging.DEBUG)
			msg = ('\nWARNING: command:\n' + send + '\nreturned unaccepted exit code: ' + res + '\nIf this is expected, pass in check_exit=False or an exit_values array into the send function call.')
			shutit.build['report'] += msg
			if retbool:
				return False
			elif shutit.build['interactive'] >= 1:
				# This is a failure, so we pass in level=0
				shutit.pause_point(msg + '\n\nInteractive, so not retrying.\nPause point on exit_code != 0 (' + res + '). CTRL-C to quit', shutit_pexpect_child=self.pexpect_child, level=0)
			elif retry == 1:
				shutit.fail('Exit value from command\n' + send + '\nwas:\n' + res, throw_exception=False)
			else:
				return False
		return True



	def pause_point(self,
	                msg='SHUTIT PAUSE POINT',
	                print_input=True,
	                resize=True,
	                colour='32',
	                default_msg=None,
	                wait=-1):
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
		shutit = shutit_global.shutit
		if print_input:
			if resize:
				# It is possible we do not have distro set yet, so wrap in try/catch
				try:
					if self.current_environment.distro != 'osx':
						fixterm_filename = '/tmp/shutit_fixterm'
						fixterm_filename_stty = fixterm_filename + '_stty'
						if not self.in_screen():
							if not self.file_exists(fixterm_filename):
								shutit.log('Fixing up your terminal, please wait...',level=logging.INFO)
								self.send_file(fixterm_filename,shutit_assets.get_fixterm(), loglevel=logging.DEBUG)
								self.send(' chmod 777 ' + fixterm_filename, echo=False,loglevel=logging.DEBUG)
							if not self.file_exists(fixterm_filename + '_stty'):
								self.send(' stty >  ' + fixterm_filename_stty, echo=False,loglevel=logging.DEBUG)
								self.sendline(' ' + fixterm_filename)
							# do not re-run if the output of stty matches the current one
							# This causes problems in video mode (?), so commenting out.
							#elif self.send_and_get_output(' diff <(stty) ' + fixterm_filename_stty) != '':
							#	self.sendline(' ' + fixterm_filename)
							else:
								self.sendline('')
				except:
					pass
			if default_msg == None:
				if not shutit.build['video'] and not shutit.build['training'] and not shutit.build['testing'] and not shutit.build['walkthrough']:
					pp_msg = '\r\nYou now have a standard shell. Hit CTRL and then ] at the same time to continue ShutIt run.'
					if shutit.build['delivery'] == 'docker':
						pp_msg += '\r\nHit CTRL and u to save the state to a docker image'
					shutit.log('\r\n' + 10*'=' + shutit_util.colourise(colour,msg) + 10*'='+'\r\n' + shutit_util.colourise(colour,pp_msg),transient=True)
				else:
					shutit.log('\r\n' + (shutit_util.colourise(colour, msg)),transient=True)
			else:
				shutit.log(shutit_util.colourise(colour, msg) + '\r\n' + default_msg + '\r\n',transient=True)
			oldlog = self.pexpect_child.logfile_send
			self.pexpect_child.logfile_send = None
			if wait < 0:
				try:
					self.pexpect_child.interact(input_filter=self._pause_input_filter)
					self.handle_pause_point_signals()
				except Exception as e:
					shutit.fail('Terminating ShutIt.\n' + str(e))
			else:
				time.sleep(wait)
			self.pexpect_child.logfile_send = oldlog
		else:
			pass
		shutit.build['ctrlc_stop'] = False
		return True


	def _pause_input_filter(self, input_string):
		
		shutit = shutit_global.shutit
		"""Input filter for pause point to catch special keystrokes"""
		# Can get errors with eg up/down chars
		if len(input_string) == 1:
			# Picked CTRL-u as the rarest one accepted by terminals.
			if ord(input_string) == 21 and shutit.build['delivery'] == 'docker':
				shutit.log('CTRL and u caught, forcing a tag at least',level=logging.INFO)
				shutit.do_repository_work('tagged_by_shutit', password=shutit.host['password'], docker_executable=shutit.host['docker_executable'], force=True)
				shutit.log('Commit and tag done. Hit CTRL and ] to continue with build. Hit return for a prompt.',level=logging.INFO)
			# CTRL-d
			elif ord(input_string) == 4:
				# Testing mode simply ignores the CTRL-D
				if not shutit.build['testing']:
					shutit.shutit_signal['ID'] = 4
					if shutit_util.get_input('CTRL-D caught, are you sure you want to quit this ShutIt run?\n\r=> ',default='n',boolean=True):
						shutit.fail('CTRL-D caught, quitting')
					if shutit_util.get_input('Do you want to pass through the CTRL-D to the ShutIt session?\n\r=> ',default='n',boolean=True):
						return '\x04'
					# Return nothing
				return ''
			# CTRL-h
			elif ord(input_string) == 8:
				shutit.shutit_signal['ID'] = 8
				# Return the escape from pexpect char
				return '\x1d'
			# CTRL-g
			elif ord(input_string) == 7:
				shutit.shutit_signal['ID'] = 7
				# Return the escape from pexpect char
				return '\x1d'
			# CTRL-s
			elif ord(input_string) == 19:
				shutit.shutit_signal['ID'] = 19
				# Return the escape from pexpect char
				return '\x1d'
			# CTRL-]
			# Foreign keyboard?: http://superuser.com/questions/398/how-to-send-the-escape-character-on-os-x-terminal/427#427
			elif ord(input_string) == 29:
				shutit.shutit_signal['ID'] = 29
				# Return the escape from pexpect char
				return '\x1d'
		return input_string


	def handle_pause_point_signals(self):
		shutit = shutit_global.shutit
		if shutit.shutit_signal['ID'] == 29:
			# clear the signal
			shutit.shutit_signal['ID'] = 0
			shutit.log('\r\nCTRL-] caught, continuing with run...',level=logging.INFO,transient=True)
		return True


	def file_exists(self,
	                filename,
	                directory=False,
	                note=None,
	                loglevel=logging.DEBUG):
		"""Return True if file exists on the target host, else False

		@param filename:   Filename to determine the existence of.
		@param directory:  Indicate that the file is a directory.
		@param note:       See send()

		@type filename:    string
		@type directory:   boolean

		@rtype: boolean
		"""
		shutit = shutit_global.shutit
		shutit._handle_note(note, 'Looking for filename in current environment: ' + filename)
		test_type = '-d' if directory is True else '-e' if directory is None else '-a'
		#       v the space is intentional, to avoid polluting bash history.
		test = ' test %s %s' % (test_type, filename)
		output = self.send_and_get_output(test + ' && echo FILEXIST-""FILFIN || echo FILNEXIST-""FILFIN', record_command=False, echo=False, loglevel=loglevel)
		res = shutit_util.match_string(output, '^(FILEXIST|FILNEXIST)-FILFIN$')
		ret = False
		if res == 'FILEXIST':
			ret = True
		elif res == 'FILNEXIST':
			pass
		else:
			# Change to log?
			shutit.log(repr('before>>>>:%s<<<< after:>>>>%s<<<<' % (self.pexpect_child.before, self.pexpect_child.after)),transient=True)
			shutit.fail('Did not see FIL(N)?EXIST in output:\n' + output)
		shutit._handle_note_after(note=note)
		return ret


	def chdir(self,
	          path,
	          timeout=3600,
	          note=None,
	          loglevel=logging.DEBUG):
		"""How to change directory will depend on whether we are in delivery mode bash or docker.

		@param path:          Path to send file to.
		@param timeout:       Timeout on response
		@param note:          See send()
		"""
		shutit = shutit_global.shutit
		shutit._handle_note(note, 'Changing to path: ' + path)
		shutit.log('Changing directory to path: "' + path + '"', level=logging.DEBUG)
		if shutit.build['delivery'] in ('bash','dockerfile'):
			self.send(' cd ' + path, timeout=timeout, echo=False,loglevel=loglevel)
		elif shutit.build['delivery'] in ('docker','ssh'):
			os.chdir(path)
		else:
			shutit.fail('chdir not supported for delivery method: ' + shutit.build['delivery'])
		shutit._handle_note_after(note=note)
		return True



	def get_file_perms(self,
	                   filename,
	                   note=None,
	                   loglevel=logging.DEBUG):
		"""Returns the permissions of the file on the target as an octal
		string triplet.

		@param filename:  Filename to get permissions of.
		@param note:      See send()

		@type filename:   string

		@rtype:           string
		"""
		shutit = shutit_global.shutit
		shutit._handle_note(note)
		cmd = 'stat -c %a ' + filename
		self.send(' ' + cmd, check_exit=False, echo=False, loglevel=loglevel)
		res = shutit_util.match_string(self.pexpect_child.before, '([0-9][0-9][0-9])')
		shutit._handle_note_after(note=note)
		return res


	def add_to_bashrc(self,
	                  line,
	                  match_regexp=None,
	                  note=None,
	                  loglevel=logging.DEBUG):
		"""Takes care of adding a line to everyone's bashrc
		(/etc/bash.bashrc).

		@param line:          Line to add.
		@param match_regexp:  See add_line_to_file()
		@param note:          See send()

		@return:              See add_line_to_file()
		"""
		shutit = shutit_global.shutit
		shutit._handle_note(note)
		if not shutit_util.check_regexp(match_regexp):
			shutit.fail('Illegal regexp found in add_to_bashrc call: ' + match_regexp)
		if self.whoami() == 'root':
			shutit.add_line_to_file(line, '/root/.bashrc', match_regexp=match_regexp, loglevel=loglevel)
		else:
			shutit.add_line_to_file(line, '${HOME}/.bashrc', match_regexp=match_regexp, loglevel=loglevel)
		shutit.add_line_to_file(line, '/etc/bash.bashrc', match_regexp=match_regexp, loglevel=loglevel)
		return True



	def is_user_id_available(self,
	                         user_id,
	                         note=None,
	                         loglevel=logging.DEBUG):
		"""Determine whether the specified user_id available.

		@param user_id:  User id to be checked.
		@param note:     See send()

		@type user_id:   integer

		@rtype:          boolean
		@return:         True is the specified user id is not used yet, False if it's already been assigned to a user.
		"""
		shutit = shutit_global.shutit
		shutit._handle_note(note)
		# v the space is intentional, to avoid polluting bash history.
		self.send(' cut -d: -f3 /etc/paswd | grep -w ^' + user_id + '$ | wc -l', expect=self.default_expect, echo=False, loglevel=loglevel)
		shutit._handle_note_after(note=note)
		if shutit_util.match_string(self.pexpect_child.before, '^([0-9]+)$') == '1':
			return False
		else:
			return True



	def set_password(self,
	                 password,
	                 user='',
	                 note=None):
		"""Sets the password for the current user or passed-in user.

		As a side effect, installs the "password" package.

		@param user:        username to set the password for. Defaults to '' (i.e. current user)
		@param password:    password to set for the user
		@param note:        See send()
		"""
		shutit = shutit_global.shutit
		shutit._handle_note(note)
		self.install('passwd')
		if self.current_environment.install_type == 'apt':
			self.send('passwd ' + user, expect='Enter new', check_exit=False)
			self.send(password, expect='Retype new', check_exit=False, echo=False)
			self.send(password, expect=self.default_expect, echo=False)
		elif self.current_environment.install_type == 'yum':
			self.send('passwd ' + user, expect='ew password', check_exit=False)
			self.send(password, expect='ew password', check_exit=False, echo=False)
			self.send(password, expect=self.default_expect, echo=False)
		else:
			self.send('passwd ' + user, expect='Enter new', check_exit=False)
			self.send(password, expect='Retype new', check_exit=False, echo=False)
			self.send(password, expect=self.default_expect, echo=False)
		shutit._handle_note_after(note=note)
		return True



	def lsb_release(self,
	                loglevel=logging.DEBUG):
		"""Get distro information from lsb_release.
		"""
		#          v the space is intentional, to avoid polluting bash history.
		self.send(' lsb_release -a',check_exit=False, echo=False, loglevel=loglevel)
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
	            command='curl -L',
	            timeout=3600,
	            fail_on_empty_before=True,
	            record_command=True,
	            exit_values=None,
	            retry=3,
	            note=None,
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
		shutit = shutit_global.shutit
		shutit._handle_note(note)
		if len(locations) == 0 or type(locations) != list:
			raise ShutItFailException('Locations should be a list containing base of the url.')
		retry_orig = retry
		if not self.command_available(command):
			self.install('curl')
			if not self.command_available('curl'):
				self.install('wget')
				command = 'wget -qO- '
				if not self.command_available('wget'):
					shutit.fail('Could not install curl or wget, inform maintainers.')
		for location in locations:
			retry = retry_orig
			if location[-1] == '/':
				location = location[0:-1]
			while retry >= 0:
				send = command + ' ' + location + '/' + filename + ' > ' + filename
				self.send(send,check_exit=False,expect=self.default_expect,timeout=timeout,fail_on_empty_before=fail_on_empty_before,record_command=record_command,echo=False, loglevel=loglevel)
				if retry == 0:
					self.check_last_exit_values(send, expect=self.default_expect, exit_values=exit_values, retbool=False)
				elif not self.check_last_exit_values(send, expect=self.default_expect, exit_values=exit_values, retbool=True):
					shutit.log('Sending: ' + send + ' failed, retrying', level=logging.DEBUG)
					retry -= 1
					continue
				# If we get here, all is ok.
				shutit._handle_note_after(note=note)
				return True
		# If we get here, it didn't work
		return False



	def user_exists(self,
	                user,
	                note=None,
 	                loglevel=logging.DEBUG):
		"""Returns true if the specified username exists.
		
		@param user:   username to check for
		@param note:   See send()

		@type user:    string

		@rtype:        boolean
		"""
		shutit = shutit_global.shutit
		shutit._handle_note(note)
		exists = False
		if user == '':
			return exists
		#v the space is intentional, to avoid polluting bash history.
		ret = self.send(' id %s && echo E""XIST || echo N""XIST' % user, expect=['NXIST', 'EXIST'], echo=False, loglevel=loglevel)
		if ret:
			exists = True
		# sync with the prompt
		self.expect(self.default_expect)
		shutit._handle_note_after(note=note)
		return exists


	def package_installed(self,
	                      package,
	                      note=None,
	                      loglevel=logging.DEBUG):
		"""Returns True if we can be sure the package is installed.

		@param package:   Package as a string, eg 'wget'.
		@param note:      See send()

		@rtype:           boolean
		"""
		shutit = shutit_global.shutit
		shutit._handle_note(note)
		if self.current_environment.install_type == 'apt':
			#            v the space is intentional, to avoid polluting bash history.
			self.send(""" dpkg -l | awk '{print $2}' | grep "^""" + package + """$" | wc -l""", expect=self.default_expect, check_exit=False, echo=False, loglevel=loglevel)
		elif self.current_environment.install_type == 'yum':
			#            v the space is intentional, to avoid polluting bash history.
			self.send(""" yum list installed | awk '{print $1}' | grep "^""" + package + """$" | wc -l""", expect=self.default_expect, check_exit=False, echo=False, loglevel=loglevel)
		else:
			return False
		if shutit_util.match_string(self.pexpect_child.before, '^([0-9]+)$') != '0':
			return True
		else:
			return False



	def command_available(self,
	                      command,
	                      note=None,
	                      loglevel=logging.DEBUG):
		shutit = shutit_global.shutit
		shutit._handle_note(note)
		output = self.send_and_get_output(' command -V ' + command + ' > /dev/null', echo=False, loglevel=loglevel).strip()
		if output != '':
			return False
		else:
			return True



	def is_shutit_installed(self,
	                        module_id,
	                        note=None,
	                        loglevel=logging.DEBUG):
		"""Helper proc to determine whether shutit has installed already here by placing a file in the db.
	
		@param module_id: Identifying string of shutit module
		@param note:      See send()
		"""
		# If it's already in cache, then return True.
		# By default the cache is invalidated.
		shutit = shutit_global.shutit
		shutit._handle_note(note)
		if not self.current_environment.modules_recorded_cache_valid:
			if self.file_exists(shutit.build['build_db_dir'] + '/module_record',directory=True):
				# Bit of a hack here to get round the long command showing up as the first line of the output.
				cmd = 'find ' + shutit.build['build_db_dir'] + r"""/module_record/ -name built | sed 's@^.""" + shutit.build['build_db_dir'] + r"""/module_record.\([^/]*\).built@\1@' > """ + shutit.build['build_db_dir'] + '/' + shutit.build['build_id']
				self.send(' ' + cmd, echo=False, loglevel=loglevel)
				built = self.send_and_get_output('cat ' + shutit.build['build_db_dir'] + '/' + shutit.build['build_id'], echo=False, loglevel=loglevel).strip()
				self.send(' rm -rf ' + shutit.build['build_db_dir'] + '/' + shutit.build['build_id'], echo=False, loglevel=loglevel)
				built_list = built.split('\r\n')
				self.current_environment.modules_recorded = built_list
			# Either there was no directory (so the cache is valid), or we've built the cache, so mark as good.
			self.current_environment.modules_recorded_cache_valid = True
		# Modules recorded cache will be valid at this point, so check the pre-recorded modules and the in-this-run installed cache.
		shutit._handle_note_after(note=note)
		if module_id in self.current_environment.modules_recorded or module_id in self.current_environment.modules_installed:
			return True
		else:
			return False


	def ls(self,
	       directory,
	       note=None,
	       loglevel=logging.DEBUG):
		"""Helper proc to list files in a directory

		@param directory:   directory to list.  If the directory doesn't exist, shutit.fail() is called (i.e.  the build fails.)
		@param note:        See send()

		@type directory:    string

		@rtype:             list of strings
		"""
		shutit = shutit_global.shutit
		# should this blow up?
		shutit._handle_note(note)
		if not self.file_exists(directory,directory=True):
			shutit.fail('ls: directory\n\n' + directory + '\n\ndoes not exist', throw_exception=False)
		files = self.send_and_get_output(' ls ' + directory,echo=False, loglevel=loglevel, fail_on_empty_before=False)
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
		shutit._handle_note_after(note=note)
		return files


	def install(self,
	            package,
	            options=None,
	            timeout=3600,
	            force=False,
	            check_exit=True,
	            reinstall=False,
	            note=None,
	            loglevel=logging.INFO):
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
		shutit = shutit_global.shutit
		# If separated by spaces, install separately
		if package.find(' ') != -1:
			ok = True
			for p in package.split(' '):
				if not self.install(p,options,timeout,force,check_exit,reinstall,note):
					ok = False
			return ok
		# Some packages get mapped to the empty string. If so, bail out with 'success' here.
		if note != None:
			shutit._handle_note('Installing package: ' + package + '\n' + note)
		shutit.log('Installing package: ' + package,level=loglevel)
		if options is None: options = {}
		install_type = self.current_environment.install_type
		if install_type == 'src':
			# If this is a src build, we assume it's already installed.
			return True
		opts = ''
		whoiam = self.whoami()
		if whoiam != 'root' and install_type != 'brew':
			if not self.command_available('sudo'):
				shutit.pause_point('Please install sudo and then continue with CTRL-]',shutit_pexpect_child=self.pexpect_child)
			cmd = 'sudo '
			pw = self.get_env_pass(whoiam,'Please input your sudo password in case it is needed (for user: ' + whoiam + ')\nJust hit return if you do not want to submit a password.\n')
		else:
			cmd = ''
			pw = ''
		if install_type == 'apt':
			if not shutit.get_current_shutit_pexpect_session_environment().build['apt_update_done'] and self.whoami() == 'root':
				self.send('apt-get update',loglevel=logging.INFO)
				shutit.get_current_shutit_pexpect_session_environment().build['apt_update_done'] = True
			cmd += 'apt-get install'
			if 'apt' in options:
				opts = options['apt']
			else:
				opts = '-y'
				if not shutit.build['loglevel'] <= logging.DEBUG:
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
		elif install_type == 'pacman':
			cmd += 'pacman -Syy'
			if 'pacman' in options:
				opts = options['pacman']
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
		package = package_map.map_packages(package, self.current_environment.install_type)
		# Let's be tolerant of failure eg due to network.
		# This is especially helpful with automated testing.
		if package.strip() != '':
			fails = 0
			while True:
				if pw != '':
					res = self.multisend('%s %s %s' % (cmd, opts, package), {'assword':pw}, expect=['Unable to fetch some archives',self.default_expect], timeout=timeout, check_exit=False, loglevel=loglevel, echo=False)
				else:
					res = self.send('%s %s %s' % (cmd, opts, package), expect=['Unable to fetch some archives',self.default_expect], timeout=timeout, check_exit=check_exit, loglevel=loglevel)
				if res == 1:
					break
				else:
					fails += 1
				if fails >= 3:
					break
		else:
			# package not required
			pass
		shutit._handle_note_after(note=note)
		return True


	def get_memory(self, note=None):
		"""Returns memory available for use in k as an int"""
		shutit = shutit_global.shutit
		shutit._handle_note(note)
		if self.current_environment.distro == 'osx':
			memavail = self.send_and_get_output("""vm_stat | grep ^Pages.free: | awk '{print $3}' | tr -d '.'""",timeout=3,echo=False)
			memavail = int(memavail)
			memavail *= 4
		else:
			memavail = self.send_and_get_output("""cat /proc/meminfo  | grep MemAvailable | awk '{print $2}'""",timeout=3,echo=False)
			if memavail == '':
				memavail = self.send_and_get_output("""free | grep buffers.cache | awk '{print $3}'""",timeout=3,echo=False)
			memavail = int(memavail)
		shutit._handle_note_after(note=note)
		return memavail


	def remove(self,
	           package,
	           options=None,
	           timeout=3600,
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
		# If separated by spaces, remove separately
		shutit = shutit_global.shutit
		if note != None:
			shutit._handle_note('Removing package: ' + package + '\n' + note)
		if options is None: options = {}
		install_type = self.current_environment.install_type
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
		elif install_type == 'pacman':
			cmd += 'pacman -R'
			if 'pacman' in options:
				opts = options['pacman']
		elif install_type == 'apk':
			cmd += 'apk del'
			opts = options['apt'] if 'apt' in options else '-q'
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
		package = package_map.map_package(package, self.current_environment.install_type)
		if pw != '':
			self.multisend('%s %s %s' % (cmd, opts, package), {'assword:':pw}, timeout=timeout, exit_values=['0','100'], echo=False)
		else:
			self.send('%s %s %s' % (cmd, opts, package), timeout=timeout, exit_values=['0','100'])
		shutit._handle_note_after(note=note)
		return True



	def send_and_match_output(self,
	                          send,
	                          matches,
	                          retry=3,
	                          strip=True,
	                          note=None,
	                          echo=False,
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
		shutit = shutit_global.shutit
		shutit._handle_note(note)
		shutit.log('Matching output from: "' + send + '" to one of these regexps:' + str(matches),level=logging.INFO)
		output = self.send_and_get_output(send, retry=retry, strip=strip, echo=echo, loglevel=loglevel)
		if type(matches) == str:
			matches = [matches]
		shutit._handle_note_after(note=note)
		for match in matches:
			if shutit_util.match_string(output, match) != None:
				shutit.log('Matched output, return True',level=logging.DEBUG)
				return True
		shutit.log('Failed to match output, return False',level=logging.DEBUG)
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
		shutit = shutit_global.shutit
		shutit._handle_note(note, command=str(send))
		shutit.log('Retrieving output from command: ' + send,level=loglevel)
		# Don't check exit, as that will pollute the output. Also, it's quite likely the submitted command is intended to fail.
		self.send(shutit_util.get_send_command(send), check_exit=False, retry=retry, echo=echo, timeout=timeout, record_command=record_command, loglevel=loglevel, fail_on_empty_before=fail_on_empty_before)
		before = self.pexpect_child.before
		if preserve_newline and before[-1] == '\n':
			preserve_newline = True
		else:
			preserve_newline = False
		before = before.strip(send)
		shutit._handle_note_after(note=note)
		if strip:
			# cf: http://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
			ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
			string_with_termcodes = before.strip()
			string_without_termcodes = ansi_escape.sub('', string_with_termcodes)
			
			#string_without_termcodes_stripped = string_without_termcodes.strip()
			# Strip out \rs to make it output the same as a typical CL. This could be optional.
			string_without_termcodes_stripped_no_cr = string_without_termcodes.replace('\r','')
			if False:
				for c in string_without_termcodes_stripped_no_cr:
					shutit.log((str(hex(ord(c))) + ' '),level=logging.DEBUG)
			if preserve_newline:
				return string_without_termcodes_stripped_no_cr + '\n'
			else:
				return string_without_termcodes_stripped_no_cr
		else:
			if False:
				for c in before:
					shutit.log((str(hex(ord(c))) + ' '),level=logging.DEBUG)
			return before


	def get_env_pass(self,user=None,msg=None,note=None):
		"""Gets a password from the user if one is not already recorded for this environment.

		@param user:    username we are getting password for
		@param msg:     message to put out there
		"""
		shutit = shutit_global.shutit
		shutit._handle_note(note)
		user = user or self.whoami()
		msg = msg or 'Please input the sudo password for user: ' + user
		if user not in self.current_environment.users.keys():
			self.current_environment.users.update({user:None})
		if not self.current_environment.users[user]:
			self.current_environment.users[user] = shutit_util.get_input(msg,ispass=True)
		return self.current_environment.users[user]


	def whoarewe(self,
	             note=None,
	             loglevel=logging.DEBUG):
		"""Returns the current group.

		@param note:     See send()

		@return: the first group found
		@rtype: string
		"""
		shutit = shutit_global.shutit
		shutit._handle_note(note)
		res = self.send_and_get_output(' id -n -g',echo=False, loglevel=loglevel).strip()
		shutit._handle_note_after(note=note)
		return res




	def get_distro_info(self, loglevel=logging.DEBUG):
		"""Get information about which distro we are using, placing it in the environment object.

		Fails if distro could not be determined.
		Should be called with the container is started up, and uses as core info
		as possible.

		Note: if the install type is apt, it issues the following:
		    - apt-get update
		    - apt-get install -y -qq lsb-release

		"""
		shutit = shutit_global.shutit
		install_type   = ''
		distro         = ''
		distro_version = ''
		if shutit.build['distro_override'] != '':
			key = shutit.build['distro_override']
			distro = shutit.build['distro_override']
			install_type = package_map.INSTALL_TYPE_MAP[key]
			distro_version = ''
			if install_type == 'apt' and shutit.build['delivery'] in ('docker','dockerfile'):
				if not self.command_available('lsb_release'):
					if not shutit.get_current_shutit_pexpect_session_environment().build['apt_update_done'] and self.whoami() == 'root':
						shutit.get_current_shutit_pexpect_session_environment.build['apt_update_done'] = True
						self.send('apt-get update && apt-get install -y -qq lsb-release',loglevel=loglevel)
				d = self.lsb_release()
				install_type   = d['install_type']
				distro         = d['distro']
				distro_version = d['distro_version']
			elif install_type == 'yum' and shutit.build['delivery'] in ('docker', 'dockerfile'):
				if self.file_exists('/etc/redhat-release'):
					output = self.send_and_get_output('cat /etc/redhat-release',echo=False, loglevel=loglevel)
					if re.match('^centos.*$', output.lower()) or re.match('^red hat.*$', output.lower()) or re.match('^fedora.*$', output.lower()) or True:
						self.send_and_match_output('yum install -y -t redhat-lsb epel-release','Complete!',loglevel=loglevel)
				else:
					if not self.command_available('lsb_release'):
						self.send('yum install -y lsb-release',loglevel=loglevel)
				install_type   = d['install_type']
				distro         = d['distro']
				distro_version = d['distro_version']
			elif install_type == 'apk' and shutit.build['delivery'] in ('docker','dockerfile'):
				if not shutit.get_current_shutit_pexpect_session_environment().build['apk_update_done'] and self.whoami() == 'root':
					self.send('apk -q update',loglevel=logging.INFO)
					shutit.get_current_shutit_pexpect_session_environment().build['apk_update_done'] = True
				self.send('apk -q add bash',loglevel=loglevel)
				install_type   = 'apk'
				distro         = 'alpine'
				distro_version = '1.0'
			elif install_type == 'pacman' and shutit.build['delivery'] in ('docker','dockerfile') and self.whoami() == 'root':
				if not shutit.get_current_shutit_pexpect_session_environment().build['pacman_update_done']:
					shutit.get_current_shutit_pexpect_session_environment().build['pacman_update_done'] = True
					self.send('pacman -Syy',loglevel=logging.INFO)
				install_type   = d['install_type']
				distro         = d['distro']
				distro_version = '1.0'
			elif install_type == 'emerge' and shutit.build['delivery'] in ('docker','dockerfile'):
				if not shutit.get_current_shutit_pexpect_session_environment().build['emerge_update_done'] and self.whoami() == 'root':
					# Takes bloody ages!
					#self.send('emerge --sync',loglevel=loglevel,timeout=9999)
					pass
				install_type = 'emerge'
				distro = 'gentoo'
				distro_version = '1.0'
			elif install_type == 'docker' and shutit.build['delivery'] in ('docker','dockerfile'):
				distro = 'coreos'
				distro_version = '1.0'
		elif self.command_available('lsb_release'):
			d = self.lsb_release()
			install_type   = d['install_type']
			distro         = d['distro']
			distro_version = d['distro_version']
		else:
			issue_output = self.send_and_get_output(' cat /etc/issue',echo=False, loglevel=loglevel).lower()
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
					os_name = self.send_and_get_output(' cat /etc/os-release | grep ^NAME',echo=False, loglevel=loglevel).lower()
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
				elif self.send_and_get_output("uname -a | awk '{print $1}'",echo=False, loglevel=loglevel) == 'Darwin':
					distro = 'osx'
					install_type = 'brew'
					if not self.command_available('brew'):
						shutit.fail('ShutiIt requires brew be installed. See http://brew.sh for details on installation.')
					if not self.file_exists('/tmp/shutit_brew_list'):
						self.send('brew list > .shutit_brew_list',echo=False)
					for package in ('coreutils','findutils','gnu-tar','gnu-sed','gawk','gnutls','gnu-indent','gnu-getopt'):
						if self.send_and_get_output('cat .shutit_brew_list | grep -w ' + package,echo=False, loglevel=loglevel) == '':
							self.send('brew install ' + package,loglevel=loglevel)
					self.send('rm -f .shutit_brew_list',echo=False)
				if install_type == '' or distro == '':
					shutit.fail('Could not determine Linux distro information. ' + 'Please inform ShutIt maintainers at https://github.com/ianmiell/shutit', shutit_pexpect_child=self.pexpect_child)
			# The call to self.package_installed with lsb-release above
			# may fail if it doesn't know the install type, so
			# if we've determined that now
			if install_type == 'apt' and shutit.build['delivery'] in ('docker','dockerfile'):
				if not self.command_available('lsb_release'):
					if not shutit.get_current_shutit_pexpect_session_environment().build['apt_update_done'] and self.whoami() == 'root':
						shutit.get_current_shutit_pexpect_session_environment().build['apt_update_done'] = True
						self.send('apt-get update && apt-get install -y -qq lsb-release',loglevel=loglevel)
					self.send('apt-get install -y -qq lsb-release',loglevel=loglevel)
				d = self.lsb_release()
				install_type   = d['install_type']
				distro         = d['distro']
				distro_version = d['distro_version']
			elif install_type == 'yum' and shutit.build['delivery'] in ('docker','dockerfile'):
				if self.file_exists('/etc/redhat-release'):
					output = self.send_and_get_output('cat /etc/redhat-release',echo=False, loglevel=loglevel)
					if re.match('^centos.*$', output.lower()) or re.match('^red hat.*$', output.lower()) or re.match('^fedora.*$', output.lower()) or True:
						self.send_and_match_output('yum install -y -t redhat-lsb epel-release','Complete!',loglevel=loglevel)
				else:
					if not self.command_available('lsb_release'):
						self.send('yum install -y lsb-release',loglevel=loglevel)
				d = self.lsb_release()
				install_type   = d['install_type']
				distro         = d['distro']
				distro_version = d['distro_version']
			elif install_type == 'apk' and shutit.build['delivery'] in ('docker','dockerfile'):
				if not shutit.get_current_shutit_pexpect_session_environment().build['apk_update_done'] and self.whoami() == 'root':
					self.send('apk -q update',loglevel=logging.INFO)
					shutit.get_current_shutit_pexpect_session_environment().build['apk_update_done'] = True
				self.send('apk -q add bash',loglevel=loglevel)
				install_type   = 'apk'
				distro         = 'alpine'
				distro_version = '1.0'
			elif install_type == 'emerge' and shutit.build['delivery'] in ('docker','dockerfile'):
				if not shutit.get_current_shutit_pexpect_session_environment().build['emerge_update_done'] and self.whoami() == 'root':
					# Takes bloody ages!
					#self.send('emerge --sync',loglevel=logging.INFO)
					pass
				install_type = 'emerge'
				distro = 'gentoo'
				distro_version = '1.0'
		# We should have the distro info now, let's assign to target config
		# if this is not a one-off.
		self.current_environment.install_type   = install_type
		self.current_environment.distro         = distro
		self.current_environment.distro_version = distro_version
		return True



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
		shutit = shutit_global.shutit
		shutit._handle_note(note)
		send_iteration = send
		expect_list = list(send_dict)
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
			res = self.send(send_iteration, expect=expect_list, check_exit=check_exit, fail_on_empty_before=fail_on_empty_before, timeout=timeout, record_command=record_command, exit_values=exit_values, echo=echo, escape=escape, loglevel=loglevel)
			if res >= len(expect_list) - n_breakout_items:
				break
			else:
				send_iteration = send_dict[expect_list[res]]
		shutit._handle_note_after(note=note)
		return res


	def send_and_require(self,
	                     send,
	                     regexps,
	                     not_there=False,
	                     echo=None,
	                     note=None,
	                     loglevel=logging.INFO):
		"""Send string and require the item in the output.
		See send_until
		"""
		shutit = shutit_global.shutit
		return self.send_until(send, regexps, not_there=not_there, cadence=0, retries=1, echo=echo, note=note, loglevel=loglevel)


	def send_until(self,
	               send,
	               regexps,
	               not_there=False,
	               cadence=5,
	               retries=100,
	               echo=None,
	               note=None,
	               loglevel=logging.INFO):
		"""Send string on a regular cadence until a string is either seen, or the timeout is triggered.

		@param send:                 See send()
		@param regexps:              List of regexps to wait for.
		@param not_there:            If True, wait until this a regexp is not seen in the output. If False
		                             wait until a regexp is seen in the output (default)
		@param echo:                 See send()
		@param note:                 See send()
		"""
		shutit = shutit_global.shutit
		shutit._handle_note(note, command=send + ' until one of these seen: ' + str(regexps))
		shutit.log('Sending: "' + send + '" until one of these regexps seen: ' + str(regexps),level=loglevel)
		if type(regexps) == str:
			regexps = [regexps]
		if type(regexps) != list:
			shutit.fail('regexps should be list')
		while retries > 0:
			retries -= 1
			output = self.send_and_get_output(send, retry=1, strip=True,echo=echo, loglevel=loglevel, fail_on_empty_before=False)
			if not not_there:
				for regexp in regexps:
					if not shutit_util.check_regexp(regexp):
						shutit.fail('Illegal regexp found in send_until call: ' + regexp)
					if shutit_util.match_string(output, regexp):
						return True
			else:
				# Only return if _not_ seen in the output
				missing = False
				for regexp in regexps:
					if not shutit_util.check_regexp(regexp):
						shutit.fail('Illegal regexp found in send_until call: ' + regexp)
					if not shutit_util.match_string(output, regexp):
						missing = True
						break
				if missing:
					shutit._handle_note_after(note=note)
					return True
			time.sleep(cadence)
		shutit._handle_note_after(note=note)
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
	                loglevel=logging.DEBUG):

		"""Change text in a file.

		Returns None if there was no match for the regexp, True if it was matched
		and replaced, and False if the file did not exist or there was some other
		problem.

		@param text:          Text to insert.
		@param fname:         Filename to insert text to
		@param pattern:       Regexp for a line to match and insert after/before/replace.
		                      If none, put at end of file.
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
		import pdb
		#pdb.set_trace()
		shutit = shutit_global.shutit
		shutit._handle_note(note)
		fexists = self.file_exists(fname)
		if not fexists:
			if create:
				self.send(' touch ' + fname, echo=False, loglevel=loglevel)
			else:
				shutit.fail(fname + ' does not exist and create=False')
		if replace:
			# If replace and no pattern FAIL
			if not pattern:
				shutit.fail('replace=True requires a pattern to be passed in')
			# If replace and delete FAIL
			if delete:
				shutit.fail('cannot pass replace=True and delete=True to insert_text')
		# ftext is the original file's text. If base64 is available, use it to
		# encode the text
		if self.command_available('base64'):
			if PY3:
				ftext = bytes(self.send_and_get_output(' base64 ' + fname, echo=False, loglevel=loglevel),'utf-8')
			else:
				ftext = self.send_and_get_output(' base64 ' + fname, echo=False, loglevel=loglevel)
			ftext = base64.b64decode(ftext)
		else:
			# Replace the file text's ^M-newlines with simple newlines
			if PY3:
				ftext = bytes(self.send_and_get_output('cat ' + fname, echo=False, loglevel=loglevel),'utf-8')
				ftext = ftext.replace(bytes('\r\n', 'utf-8'),bytes('\n', 'utf-8'))
			else:
				ftext = self.send_and_get_output('cat ' + fname, echo=False, loglevel=loglevel)
				ftext = ftext.replace('\r\n','\n')
		# Delete the text
		if delete:
			if PY3:
				loc = ftext.find(bytes(text,'utf-8'))
			else:
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
						shutit.fail('Illegal regexp found in change_text call: ' + pattern)
					# cf: http://stackoverflow.com/questions/9411041/matching-ranges-of-lines-in-python-like-sed-ranges
					if PY3:
						sre_match = re.search(bytes(pattern,'utf-8'),ftext,re.DOTALL|re.MULTILINE)
					else:
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
							if PY3:
								if not force and ftext[cut_point-len(text):].find(bytes(text,'utf-8')) > 0:
									return None
							else:
								if not force and ftext[cut_point-len(text):].find(text) > 0:
									return None
						else:
							cut_point = sre_match.end()
							# If the text is already there and we're not forcing it, return None.
							if PY3:
								if not force and ftext[cut_point:].find(bytes(text,'utf-8')) > 0:
									return None
							else:
								if not force and ftext[cut_point:].find(text) > 0:
									return None
						newtext1 = ftext[:cut_point]
						newtext2 = ftext[cut_point:]
				else:
					if PY3:
						lines = ftext.split(bytes('\n','utf-8'))
					else:
						lines = ftext.split('\n')
					cut_point   = 0
					line_length = 0
					matched     = False
					if not shutit_util.check_regexp(pattern):
						shutit.fail('Illegal regexp found in change_text call: ' + pattern)
					for line in lines:
						#Help the user out to make this properly line-oriented
						pattern_before=''
						pattern_after=''
						if len(pattern) == 0 or pattern[0] != '^':
							pattern_before = '^.*'
						if len(pattern) == 0 or pattern[-1] != '$':
							pattern_after = '.*$'
						new_pattern = pattern_before+pattern+pattern_after
						if PY3:
							match = re.search(bytes(new_pattern,'utf-8'), line)
						else:
							match = re.search(new_pattern,line)
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
					# newtext1 is everything up to the cutpoint
					newtext1 = ftext[:cut_point]
					# newtext2 is everything after the cutpoint
					newtext2 = ftext[cut_point:]
					# if replacing and we matched the output in a line, then set newtext2 to be everything from cutpoint's line end
					if replace and matched:
						newtext2 = ftext[cut_point+line_length:]
					elif not force:
						# If the text is already there and we're not forcing it, return None.
						if PY3:
							if before and ftext[cut_point-len(text):].find(bytes(text,'utf-8')) > 0:
								return None
							if not before and ftext[cut_point:].find(bytes(text,'utf-8')) > 0:
								return None
						else:
							if before and ftext[cut_point-len(text):].find(text) > 0:
								return None
							if not before and ftext[cut_point:].find(text) > 0:
								return None
					# Add a newline to newtext1 if it is not already there
					if PY3:
						if len(newtext1) > 0 and bytes(newtext1.decode('utf-8')[-1],'utf-8') != bytes('\n','utf-8'):
							newtext1 += bytes('\n','utf-8')
					else:
						if len(newtext1) > 0 and newtext1[-1] != '\n':
							newtext1 += '\n'
					# Add a newline to newtext2 if it is not already there
					if PY3:
						if len(newtext2) > 0 and bytes(newtext2.decode('utf-8')[0],'utf-8') != bytes('\n','utf-8'):
							newtext2 = bytes('\n','utf-8') + newtext2
					else:
						if len(newtext2) > 0 and newtext2[0] != '\n':
							newtext2 = '\n' + newtext2
			else:
				# Append to file absent a pattern.
				cut_point = len(ftext)
				newtext1 = ftext[:cut_point]
				newtext2 = ftext[cut_point:]
			# If adding or replacing at the end of the file, then ensure we have a newline at the end
			if PY3:
				if newtext2 == b'' and len(text) > 0 and bytes(text[-1],'utf-8') != bytes('\n','utf-8'):
					newtext2 = bytes('\n','utf-8')
			else:
				if newtext2 == '' and len(text) > 0 and text[-1] != '\n':
					newtext2 = '\n'
			if PY3:
				new_text = newtext1 + bytes(text,'utf-8') + newtext2
			else:
				new_text = newtext1 + text + newtext2
		self.send_file(fname,new_text,truncate=True,loglevel=loglevel)
		shutit._handle_note_after(note=note)
		return True




	def remove_line_from_file(self,
							  line,
							  filename,
							  match_regexp=None,
							  literal=False,
	                          note=None,
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
		shutit = shutit_global.shutit
		shutit._handle_note(note)
		# assume we're going to add it
		tmp_filename = '/tmp/' + shutit_util.random_id()
		if self.file_exists(filename):
			if literal:
				if match_regexp == None:
					#            v the space is intentional, to avoid polluting bash history.
					self.send(""" grep -v '^""" + line + """$' """ + filename + ' > ' + tmp_filename, exit_values=['0', '1'], echo=False, loglevel=loglevel)
				else:
					if not shutit_util.check_regexp(match_regexp):
						shutit.fail('Illegal regexp found in remove_line_from_file call: ' + match_regexp)
					#            v the space is intentional, to avoid polluting bash history.
					self.send(""" grep -v '^""" + match_regexp + """$' """ + filename + ' > ' + tmp_filename, exit_values=['0', '1'], echo=False, loglevel=loglevel)
			else:
				if match_regexp == None:
					#          v the space is intentional, to avoid polluting bash history.
					self.send(' grep -v "^' + line + '$" ' + filename + ' > ' + tmp_filename, exit_values=['0', '1'], echo=False, loglevel=loglevel)
				else:
					if not shutit_util.check_regexp(match_regexp):
						shutit.fail('Illegal regexp found in remove_line_from_file call: ' + match_regexp)
					#          v the space is intentional, to avoid polluting bash history.
					self.send(' grep -v "^' + match_regexp + '$" ' + filename + ' > ' + tmp_filename, exit_values=['0', '1'], echo=False, loglevel=loglevel)
			self.send(' cat ' + tmp_filename + ' > ' + filename, check_exit=False, echo=False, loglevel=loglevel)
			self.send(' rm -f ' + tmp_filename, exit_values=['0', '1'], echo=False, loglevel=loglevel)
		shutit._handle_note_after(note=note)
		return True



	def send(self,
	         send,
	         expect=None,
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
	         follow_on_commands={},
		     searchwindowsize=None,
		     maxread=None,
		     loglevel=logging.INFO):
		"""Send string as a shell command, and wait until the expected output
		is seen (either a string or any from a list of strings) before
		returning. The expected string will default to the currently-set
		default expected string (see get_default_shutit_pexpect_session_expect)

		Returns the pexpect return value (ie which expected string in the list
		matched)

		@param send:                 String to send, ie the command being
		                             issued. If set to None, we consume up to
		                             the expect string, which is useful if we
		                             just matched output that came before a
		                             standard command that returns to the
		                             prompt.
		@param expect:               String that we expect to see in the output.
		                             Usually a prompt. Defaults to currently-set
		                             expect string (see
		                             set_default_shutit_pexpect_session_expect)
		@param timeout:              Timeout on response
		@param check_exit:           Whether to check the shell exit code of the
		                             passed-in command.  If the exit value was
		                             non-zero an error is thrown.
		                             (default=None, which takes the
		                             currently-configured check_exit value)
		                             See also fail_on_empty_before.
		@param fail_on_empty_before: If debug is set, fail on empty match output
		                             string (default=True) If this is set to
		                             False, then we don't check the exit value
		                              of the command.
		@param record_command:       Whether to record the command for output at
		                             end. As a safety measure, if the command
		                             matches any 'password's then we don't
		                             record it.
		@param exit_values:          Array of acceptable exit values as strings
		@param echo:                 Whether to suppress any logging output from
		                             pexpect to the terminal or not.  We don't
		                             record the command if this is set to False
		                             unless record_command is explicitly passed
		                             in as True.
		@param escape:               Whether to escape the characters in a
		                             bash-friendly way, ie $'\\Uxxxxxx'
		@param retry:                Number of times to retry the command if the
		                             first attempt doesn't work. Useful if going
		                             to the network
		@param note:                 If a note is passed in, and we are in
		                             walkthrough mode, pause with the note
		                             printed
		@param assume_gnu:           Assume the gnu version of commands, which
		                             are not in OSx by default (for example)
		@param follow_on_commands:   A dict containing further stings to send
		                             based on the output of the last command.
		@return:                     The pexpect return value (ie which expected
		                             string in the list matched)
		@rtype:                      string
		"""
		shutit = shutit_global.shutit
		cfg = shutit.cfg
		if type(expect) == dict:
			return self.multisend(send=send,send_dict=expect,expect=shutit.get_default_shutit_pexpect_session_expect(),timeout=timeout,check_exit=check_exit,fail_on_empty_before=fail_on_empty_before,record_command=record_command,exit_values=exit_values,echo=echo,note=note,loglevel=loglevel)
		expect = expect or self.default_expect
		shutit.log('Sending in session: ' + self.pexpect_session_id,level=logging.DEBUG)
		shutit._handle_note(note, command=str(send), training_input=str(send))
		if timeout == None:
			timeout = 3600
	
		# Should we echo the output?	
		if shutit.build['loglevel'] <= logging.DEBUG:
			# Yes if it's in debug
			echo = True
		if echo == None and shutit.build['walkthrough']:
			# Yes if it's in walkthrough and was not explicitly passed in
			echo = True
		if echo == None:
			# No if it was not explicitly passed in
			echo = False

		# Handle OSX to get the GNU version of the command
		if assume_gnu:
			send = shutit_util.get_send_command(send)
			
		# If check_exit is not passed in
		# - if the expect matches the default, use the default check exit
		# - otherwise, default to doing the check
		if check_exit == None:
			# If we are in video mode, ignore exit value
			if shutit.build['video'] or shutit.build['training'] or shutit.build['walkthrough'] or shutit.build['testing']:
				check_exit = False
			elif expect == shutit.get_default_shutit_pexpect_session_expect():
				check_exit = shutit.get_default_shutit_pexpect_session_check_exit()
			else:
				# If expect given doesn't match the defaults and no argument
				# was passed in (ie check_exit was passed in as None), set
				# check_exit to true iff it matches a prompt.
				expect_matches_prompt = False
				for prompt in shutit.expect_prompts:
					if prompt == expect:
						expect_matches_prompt = True
				if not expect_matches_prompt:
					check_exit = False
				else:
					check_exit = True
		ok_to_record = False
		if not echo and record_command == None:
			record_command = False
		if record_command == None or record_command:
			ok_to_record = True
			for i in cfg.keys():
				if isinstance(cfg[i], dict):
					for j in cfg[i].keys():
						if ((j == 'password' or j == 'passphrase') and cfg[i][j] == send):
							shutit.build['shutit_command_history'].append ('#redacted command, password')
							ok_to_record = False
							break
					if not ok_to_record:
						break
			if ok_to_record:
				shutit.build['shutit_command_history'].append(send)
		if send != None:
			if not echo:
				shutit.log('Sending: ' + send,level=loglevel)
			shutit.log('================================================================================',level=logging.DEBUG)
			shutit.log('Sending>>>' + send + '<<<',level=logging.DEBUG)
			shutit.log('Expecting>>>' + str(expect) + '<<<',level=logging.DEBUG)
		while retry > 0:
			if escape:
				escaped_str = "eval $'"
				_count = 7
				for char in send:
					if char in string.ascii_letters:
						escaped_str += char
						_count += 1
					else:
						escaped_str += shutit_util.get_wide_hex(char)
						_count += 4
					if _count > shutit.build['stty_cols'] - 50:
						escaped_str += r"""'\
$'"""
						_count = 0
				escaped_str += "'"
				shutit.log('This string was sent safely: ' + send, level=logging.DEBUG)
			# Don't echo if echo passed in as False
			if not echo:
				oldlog = self.pexpect_child.logfile_send
				self.pexpect_child.logfile_send = None
				if escape:
					# 'None' escaped_str's are possible from multisends with nothing to send.
					if escaped_str != None:
						if len(escaped_str) + 25 > shutit.build['stty_cols']:
							fname = self.create_command_file(expect,escaped_str)
							res = self.send(' ' + fname,expect=expect,timeout=timeout,check_exit=check_exit,fail_on_empty_before=False,record_command=False,exit_values=exit_values,echo=False,escape=False,retry=retry,loglevel=loglevel,follow_on_commands=follow_on_commands)
							self.sendline(' rm -f ' + fname)
							self.expect(expect, searchwindowsize=searchwindowsize, maxread=maxread)
							return res
						else:
							self.sendline(escaped_str)
							expect_res = shutit._expect_allow_interrupt(self.pexpect_child, expect, timeout)
					else:
						expect_res = shutit._expect_allow_interrupt(self.pexpect_child, expect, timeout)
				else:
					if send != None:
						if len(send) + 25 > shutit.build['stty_cols']:
							fname = self.create_command_file(expect,send)
							res = self.send(' ' + fname,expect=expect,timeout=timeout,check_exit=check_exit,fail_on_empty_before=False,record_command=False,exit_values=exit_values,echo=False,escape=False,retry=retry,loglevel=loglevel,follow_on_commands=follow_on_commands)
							self.sendline(' rm -f ' + fname)
							self.expect(expect, searchwindowsize=searchwindowsize, maxread=maxread)
							return res
						else:
							self.sendline(send)
							expect_res = shutit._expect_allow_interrupt(self.pexpect_child, expect, timeout)
					else:
						expect_res = shutit._expect_allow_interrupt(self.pexpect_child, expect, timeout)
				self.pexpect_child.logfile_send = oldlog
			else:
				if escape:
					if escaped_str != None:
						if len(escaped_str) + 25 > shutit.build['stty_cols']:
							fname = self.create_command_file(expect,escaped_str)
							res = self.send(' ' + fname,expect=expect,timeout=timeout,check_exit=check_exit,fail_on_empty_before=False,record_command=False,exit_values=exit_values,echo=False,escape=False,retry=retry,loglevel=loglevel,follow_on_commands=follow_on_commands)
							self.sendline(' rm -f ' + fname)
							self.expect(expect, searchwindowsize=searchwindowsize, maxread=maxread)
							return res
						else:
							self.sendline(escaped_str)
							expect_res = shutit._expect_allow_interrupt(self.pexpect_child, expect, timeout)
					else:
						expect_res = shutit._expect_allow_interrupt(self.pexpect_child, expect, timeout)
				else:
					if send != None:
						if len(send) + 25 > shutit.build['stty_cols']:
							fname = self.create_command_file(expect,send)
							res = self.send(' ' + fname,expect=expect,timeout=timeout,check_exit=check_exit,fail_on_empty_before=False,record_command=False,exit_values=exit_values,echo=False,escape=False,retry=retry,loglevel=loglevel,follow_on_commands=follow_on_commands)
							self.sendline(' rm -f ' + fname)
							self.expect(expect,searchwindowsize=searchwindowsize, maxread=maxread)
							return res
						else:
							if echo:
								shutit.divert_output(sys.stdout)
							self.sendline(send)
							expect_res = shutit._expect_allow_interrupt(self.pexpect_child, expect, timeout)
							if echo:
								shutit.divert_output(None)
					else:
						expect_res = shutit._expect_allow_interrupt(self.pexpect_child, expect, timeout)
			# Handles 'cannot concatenate 'str' and 'type' objects' errors
			try:
				logged_output = ''.join((self.pexpect_child.before + self.pexpect_child.after).split('\n'))
				logged_output = logged_output.replace(send,'',1)
				logged_output = logged_output.replace('\r','')
				logged_output = logged_output[:30] + ' [...]'
				if echo:
					shutit.log('Output (squashed): ' + logged_output,level=logging.DEBUG)
				else:
					shutit.log('Output (squashed): ' + logged_output,level=loglevel)
				shutit.log('shutit_pexpect_child.buffer(hex)>>>\n' + str(self.pexpect_child.buffer).encode('hex') + '\n<<<',level=logging.DEBUG)
				shutit.log('shutit_pexpect_child.buffer>>>\n' + str(self.pexpect_child.buffer) + '\n<<<',level=logging.DEBUG)
				shutit.log('shutit_pexpect_child.before (hex)>>>\n' + self.pexpect_child.before.encode('hex') + '\n<<<',level=logging.DEBUG)
				shutit.log('shutit_pexpect_child.before>>>\n' + self.pexpect_child.before + '\n<<<',level=logging.DEBUG)
				shutit.log('shutit_pexpect_child.after (hex)>>>\n' + self.pexpect_child.after.encode('hex') + '\n<<<',level=logging.DEBUG)
				shutit.log('shutit_pexpect_child.after>>>\n' + self.pexpect_child.after + '\n<<<',level=logging.DEBUG)
			except:
				pass
			if fail_on_empty_before:
				if self.pexpect_child.before.strip() == '':
					shutit.fail('before empty after sending: ' + str(send) + '\n\nThis is expected after some commands that take a password.\nIf so, add fail_on_empty_before=False to the send call.\n\nIf that is not the problem, did you send an empty string to a prompt by mistake?', shutit_pexpect_child=self.pexpect_child)
			elif not fail_on_empty_before:
				# Don't check exit if fail_on_empty_before is False
				shutit.log('' + self.pexpect_child.before + '<<<', level=logging.DEBUG)
				check_exit = False
				for prompt in shutit.expect_prompts:
					if prompt == expect:
						# Reset prompt
						self.setup_prompt('reset_tmp_prompt')
						self.pexpect_child.revert_prompt('reset_tmp_prompt', expect)
			# Last output - remove the first line, as it is the previous command.
			shutit.build['last_output'] = '\n'.join(self.pexpect_child.before.split('\n')[1:])
			if check_exit:
				# store the output
				if not self.check_last_exit_values(send, expect=expect, exit_values=exit_values, retry=retry):
					shutit.log('Sending: ' + send + ' : failed, retrying', level=logging.DEBUG)
					retry -= 1
					assert(retry > 0)
					continue
			break
		# check self.pexpect_child.before for matches for follow-on commands
		for match in follow_on_commands:
			send = follow_on_commands[match]
			if shutit_util.match_string(shutit.build['last_output'],match):
				# send (with no follow-on commands)
				self.send(send,expect=expect,timeout=timeout,check_exit=check_exit,fail_on_empty_before=False,record_command=record_command,exit_values=exit_values,echo=echo,escape=escape,retry=retry,loglevel=loglevel)
		if shutit.build['step_through']:
			self.pause_point('pause point: stepping through')
		if shutit.build['ctrlc_stop']:
			shutit.build['ctrlc_stop'] = False
			self.pause_point('pause point: interrupted by CTRL-c')
		shutit._handle_note_after(note=note, training_input=str(send))
		return expect_res
	# alias send to send_and_expect
	send_and_expect = send



	def send_file(self,
	              path,
	              contents,
	              truncate=False,
	              note=None,
	              user=None,
	              group=None,
	              loglevel=logging.INFO):
		"""Sends the passed-in string as a file to the passed-in path on the
		target.

		@param path:        Target location of file on target.
		@param contents:    Contents of file as a string.
		@param note:        See send()
		@param user:        Set ownership to this user (defaults to whoami)
		@param group:       Set group to this user (defaults to first group in groups)

		@type path:         string
		@type contents:     string
		"""
		shutit = shutit_global.shutit
		shutit._handle_note(note, 'Sending contents to path: ' + path)
		# make more efficient by only looking at first 10000 chars, stop when we get to 30 chars rather than reading whole file.
		if PY3:
			split_contents = ''.join((str(contents[:10000]).split()))
		else:
			split_contents = ''.join((contents[:10000].split()))
		strings_from_file = re.findall("[^\x00-\x1F\x7F-\xFF]", split_contents)
		shutit.log('Sending file contents beginning: "' + ''.join(strings_from_file)[:30] + ' [...]" to file: ' + path, level=loglevel)
		if user == None:
			user = self.whoami()
		if group == None:
			group = self.whoarewe()
		if self.current_environment.environment_id == 'ORIGIN_ENV':
			# If we're on the root env (ie the same one that python is running on, then use python.
			f = open(path,'w')
			if truncate:
				f.truncate(0)
			if type(contents) == str:
				f.write(contents)
			elif type(contents) == bytes:
				f.write(contents.decode('utf-8'))
			f.close()
		elif shutit.build['delivery'] in ('bash','dockerfile'):
			if truncate and self.file_exists(path):
				self.send(' rm -f ' + path, echo=False,loglevel=loglevel)
			random_id = shutit_util.random_id()
			# set the searchwindowsize to a low number to speed up processing of large output
			b64contents = base64.b64encode(contents)
			if len(b64contents) > 100000:
				shutit.log('File is larger than ~100K - this may take some time',level=logging.WARNING)
			self.send(' ' + shutit_util.get_command('head') + ' -c -1 > ' + path + "." + random_id + " << 'END_" + random_id + """'\n""" + b64contents + '''\nEND_''' + random_id, echo=False,loglevel=loglevel, timeout=99999)
			self.send(' cat ' + path + '.' + random_id + ' | base64 -d > ' + path, echo=False,loglevel=loglevel)
		else:
			host_child = shutit.get_shutit_pexpect_session_from_id('host_child').pexpect_child
			path = path.replace(' ', '\ ')
			# get host session
			tmpfile = shutit.build['shutit_state_dir_base'] + 'tmp_' + shutit_util.random_id()
			f = open(tmpfile,'w')
			f.truncate(0)
			if type(contents) == str:
				f.write(contents)
			elif type(contents) == bytes:
				f.write(contents.decode('utf-8'))
			else:
				shutit.fail('type: ' + type(contents) + ' not handled')
			f.close()
			# Create file so it has appropriate permissions
			self.send(' touch ' + path, echo=False,loglevel=loglevel)
			# If path is not absolute, add $HOME to it.
			if path[0] != '/':
				shutit.send(' cat ' + tmpfile + ' | ' + shutit.host['docker_executable'] + ' exec -i ' + shutit.target['container_id'] + " bash -c 'cat > $HOME/" + path + "'", shutit_pexpect_child=host_child, expect=shutit.expect_prompts['origin_prompt'], echo=False,loglevel=loglevel)
			else:
				shutit.send(' cat ' + tmpfile + ' | ' + shutit.host['docker_executable'] + ' exec -i ' + shutit.target['container_id'] + " bash -c 'cat > " + path + "'", shutit_pexpect_child=host_child, expect=shutit.expect_prompts['origin_prompt'], echo=False,loglevel=loglevel)
			self.send(' chown ' + user + ' ' + path + ' && chgrp ' + group + ' ' + path, echo=False,loglevel=loglevel)
			os.remove(tmpfile)
		shutit._handle_note_after(note=note)
		return True


	def run_script(self,
	               script,
	               in_shell=True,
	               note=None,
	               loglevel=logging.DEBUG):
		"""Run the passed-in string as a script on the target's command line.

		@param script:   String representing the script. It will be de-indented
						 and stripped before being run.
		@param in_shell: Indicate whether we are in a shell or not. (Default: True)
		@param note:     See send()

		@type script:    string
		@type in_shell:  boolean
		"""
		shutit = shutit_global.shutit
		shutit._handle_note(note, 'Script: ' + str(script))
		shutit.log('Running script beginning: "' + ''.join(script.split())[:30] + ' [...]', level=logging.INFO)
		# Trim any whitespace lines from start and end of script, then dedent
		lines = script.split('\n')
		while len(lines) > 0 and re.match('^[ \t]*$', lines[0]):
			lines = lines[1:]
		while len(lines) > 0 and re.match('^[ \t]*$', lines[-1]):
			lines = lines[:-1]
		if len(lines) == 0:
			return True
		script = '\n'.join(lines)
		script = textwrap.dedent(script)
		# Send the script and run it in the manner specified
		if shutit.build['delivery'] in ('docker','dockerfile') and in_shell:
			script = ('set -o xtrace \n\n' + script + '\n\nset +o xtrace')
		self.send(' mkdir -p ' + shutit.build['shutit_state_dir'] + '/scripts && chmod 777 ' + shutit.build['shutit_state_dir'] + '/scripts', echo=False,loglevel=loglevel)
		self.send_file(shutit.build['shutit_state_dir'] + '/scripts/shutit_script.sh', script, loglevel=loglevel)
		self.send(' chmod +x ' + shutit.build['shutit_state_dir'] + '/scripts/shutit_script.sh', echo=False,loglevel=loglevel)
		shutit.build['shutit_command_history'].append('    ' + script.replace('\n', '\n    '))
		if in_shell:
			ret = self.send(' . ' + shutit.build['shutit_state_dir'] + '/scripts/shutit_script.sh && rm -f ' + shutit.build['shutit_state_dir'] + '/scripts/shutit_script.sh && rm -f ' + shutit.build['shutit_state_dir'] + '/scripts/shutit_script.sh', echo=False,loglevel=loglevel)
		else:
			ret = self.send(' ' + shutit.build['shutit_state_dir'] + '/scripts/shutit_script.sh && rm -f ' + shutit.build['shutit_state_dir'] + '/scripts/shutit_script.sh', echo=False,loglevel=loglevel)
		shutit._handle_note_after(note=note)
		return ret


	def _challenge_done(self,
	                    result=None,
	                    congratulations=None,
	                    follow_on_context={},
	                    pause=1,
	                    skipped=False):
		shutit = shutit_global.shutit
		if result == 'ok':
			if congratulations:
				shutit.log('\n\n' + shutit_util.colourise('32',congratulations) + '\n',transient=True)
			time.sleep(pause)
			shutit.build['ctrlc_passthrough'] = False
			if follow_on_context != {}:
				if follow_on_context.get('context') == 'docker':
					container_name = follow_on_context.get('ok_container_name')
					if not container_name:
						shutit.log('No reset context available, carrying on.',level=logging.INFO)
					elif skipped:
						# We need to ensure the correct state.
						self.replace_container(container_name)
						shutit.log('State restored.',level=logging.INFO)
					else:
						shutit.log(shutit_util.colourise('31','Continuing, remember you can restore to a known state with CTRL-g.'),transient=True)
				else:
					shutit.fail('Follow-on context not handled on pass')
			return True
		elif result in ('failed'):
			shutit.build['ctrlc_passthrough'] = False
			time.sleep(1)
			return
		elif result == 'exited':
			shutit.build['ctrlc_passthrough'] = False
			return
		elif result in ('reset'):
			if follow_on_context != {}:
				if follow_on_context.get('context') == 'docker':
					container_name = follow_on_context.get('reset_container_name')
					if not container_name:
						shutit.log('No reset context available, carrying on.',level=logging.DEBUG)
					else:
						self.replace_container(container_name)
						shutit.log('State restored.',level=logging.INFO)
				else:
					shutit.fail('Follow-on context not handled on reset')
			return True
		else:
			shutit.fail('result: ' + result + ' not handled')
		shutit.fail('_challenge_done should not get here')
		return True



	def challenge(self,
                  task_desc,
                  expect=None,
                  hints=[],
                  congratulations='OK',
                  failed='FAILED',
	              expect_type='exact',
	              challenge_type='command',
	              timeout=None,
	              check_exit=None,
	              fail_on_empty_before=True,
	              record_command=True,
	              exit_values=None,
	              echo=True,
	              escape=False,
	              pause=1,
	              loglevel=logging.DEBUG,
	              follow_on_context={},
	              difficulty=1.0,
	              new_stage=True):
		"""Set the user a task to complete, success being determined by matching the output.

		Either pass in regexp(s) desired from the output as a string or a list, or an md5sum of the output wanted.

		@param follow_on_context     On success, move to this context. A dict of information about that context.
		                             context              = the type of context, eg docker, bash
		                             ok_container_name    = if passed, send user to this container
		                             reset_container_name = if resetting, send user to this container
		@param challenge_type        Behaviour of challenge made to user
		                             command = check for output of single command
		                             golf    = user gets a pause point, and when leaving, command follow_on_context['check_command'] is run to check the output
		"""
		shutit = shutit_global.shutit
		#print shutit.build['testing_object']
		if new_stage and shutit.build['testing_object']:
			shutit.build['testing_object'].new_stage(difficulty)
		# don't catch CTRL-C, pass it through.
		shutit.build['ctrlc_passthrough'] = True
		preserve_newline                  = False
		skipped                           = False
		if expect_type == 'regexp':
			if type(expect) == str:
				expect = [expect]
			if type(expect) != list:
				shutit.fail('expect_regexps should be list')
		elif expect_type == 'md5sum':
			preserve_newline = True
			pass
		elif expect_type == 'exact':
			pass
		else:
			shutit.fail('Must pass either expect_regexps or md5sum in')
		if len(hints):
			shutit.build['pause_point_hints'] = hints
		else:
			shutit.build['pause_point_hints'] = []
		if challenge_type == 'command':
			help_text = shutit_util.colourise('32','''\nType 'help' or 'h' to get a hint, 'exit' to skip, 'shutitreset' to reset state.''')
			ok = False
			while not ok:
				shutit.log(shutit_util.colourise('32','''\nChallenge!'''),transient=True)
				if len(hints):
					shutit.log(shutit_util.colourise('32',help_text),transient=True)
				time.sleep(pause)
				# TODO: bash path completion
				send = shutit_util.get_input(task_desc + ' => ',colour='31')
				if not send or send.strip() == '':
					continue
				if send in ('help','h'):
					if len(hints):
						shutit.log(help_text,transient=True)
						shutit.log(shutit_util.colourise('32',hints.pop()),transient=True)
					else:
						shutit.log(help_text,transient=True)
						shutit.log(shutit_util.colourise('32','No hints left, sorry! CTRL-g to reset state, CTRL-s to skip this step, CTRL-] to submit for checking'),transient=True)
					time.sleep(pause)
					continue
				if send == 'shutitreset':
					self._challenge_done(result='reset',follow_on_context=follow_on_context)
					continue
				if send == 'shutitquit':
					self._challenge_done(result='reset',follow_on_context=follow_on_context)
					shutit_util.handle_exit(exit_code=1)
				if send == 'exit':
					self._challenge_done(result='exited',follow_on_context=follow_on_context)
					shutit.build['pause_point_hints'] = []
					return True
				output = self.send_and_get_output(timeout=timeout,retry=1,record_command=record_command,echo=echo, loglevel=loglevel, fail_on_empty_before=False, preserve_newline=preserve_newline)
				md5sum_output = md5(output).hexdigest()
				shutit.log('output: ' + output + ' is md5sum: ' + md5sum_output,level=logging.DEBUG)
				if expect_type == 'md5sum':
					output = md5sum_output
					if output == expect:
						ok = True
				elif expect_type == 'exact':
					if output == expect:
						ok = True
				elif expect_type == 'regexp':
					for regexp in expect:
						if shutit_util.match_string(output,regexp):
							ok = True
							break
				if not ok and failed:
					shutit.log('\n\n' + shutit_util.colourise('32','failed') + '\n',transient=True)
					self._challenge_done(result='failed')
					continue
		elif challenge_type == 'golf':
			# pause, and when done, it checks your working based on check_command.
			ok = False
			# hints
			if len(hints):
				task_desc_new = task_desc + '\r\n\r\nHit CTRL-h for help, CTRL-g to reset state, CTRL-s to skip, CTRL-] to submit for checking'
			else:
				task_desc_new = '\r\n' + task_desc
			while not ok:
				if shutit.build['testing_object']:
					shutit.build['testing_object'].start_timer()
				self.pause_point(shutit_util.colourise('31',task_desc_new),colour='31')
				if shutit.shutit_signal['ID'] == 8:
					if shutit.build['testing_object']:
						shutit.build['testing_object'].add_hint()
					if len(shutit.build['pause_point_hints']):
						shutit.log(shutit_util.colourise('31','\r\n========= HINT ==========\r\n\r\n' + shutit.build['pause_point_hints'].pop(0)),transient=True)
					else:
						shutit.log(shutit_util.colourise('31','\r\n\r\n' + 'No hints available!'),transient=True)
					time.sleep(1)
					# clear the signal
					shutit.shutit_signal['ID'] = 0
					continue
				elif shutit.shutit_signal['ID'] == 7:
					if shutit.build['testing_object']:
						shutit.build['testing_object'].add_reset()
					shutit.log(shutit_util.colourise('31','\r\n========= RESETTING STATE ==========\r\n\r\n'),transient=True)
					self._challenge_done(result='reset', follow_on_context=follow_on_context)
					# clear the signal
					shutit.shutit_signal['ID'] = 0
					# Get the new target child, which is the new 'self'
					target_child = shutit.get_shutit_pexpect_session_from_id('target_child')
					return target_child.challenge(
						task_desc=task_desc,
						expect=expect,
						hints=hints,
						congratulations=congratulations,
						failed=failed,
						expect_type=expect_type,
						challenge_type=challenge_type,
						timeout=timeout,
						check_exit=check_exit,
						fail_on_empty_before=fail_on_empty_before,
						record_command=record_command,
						exit_values=exit_values,
						echo=echo,
						escape=escape,
						pause=pause,
						loglevel=loglevel,
						follow_on_context=follow_on_context,
						new_stage=False
					)
				elif shutit.shutit_signal['ID'] == 19:
					if shutit.build['testing_object']:
						shutit.build['testing_object'].add_skip()
						shutit.build['testing_object'].end_timer()
					# Clear the signal.
					shutit.shutit_signal['ID'] = 0
					# Skip test.
					shutit.log('Test skipped',level=logging.INFO)
					skipped=True
					return True
				shutit.log('State submitted, checking your work...',level=logging.INFO)
				check_command = follow_on_context.get('check_command')
				output = self.send_and_get_output(check_command,timeout=timeout,retry=1,record_command=record_command,echo=False, loglevel=loglevel, fail_on_empty_before=False, preserve_newline=preserve_newline)
				shutit.log('output: ' + output,level=logging.DEBUG)
				md5sum_output = md5(output).hexdigest()
				if expect_type == 'md5sum':
					shutit.log('output: ' + output + ' is md5sum: ' + md5sum_output,level=logging.DEBUG)
					output = md5sum_output
					if output == expect:
						ok = True
				elif expect_type == 'exact':
					if output == expect:
						ok = True
				elif expect_type == 'regexp':
					for regexp in expect:
						if shutit_util.match_string(output,regexp):
							ok = True
							break
				if not ok and failed:
					if shutit.build['testing_object']:
						shutit.build['testing_object'].add_fail()
						shutit.build['testing_object'].end_timer()
					shutit.log('\n\n' + shutit_util.colourise('31','Failed! CTRL-g to reset state, CTRL-h for a hint, CTRL-] to submit for checking') + '\n',transient=True)
					self._challenge_done(result='failed')
					continue
		else:
			shutit.fail('Challenge type: ' + challenge_type + ' not supported')
		self._challenge_done(result='ok',follow_on_context=follow_on_context,congratulations=congratulations,skipped=skipped)
		if shutit.build['testing_object']:
			shutit.build['testing_object'].add_ok()
			shutit.build['testing_object'].end_timer()
		# Tidy up hints
		shutit.build['pause_point_hints'] = []
		return True


	def init_pexpect_session_environment(self, prefix):
		shutit = shutit_global.shutit
		environment_id_dir = shutit.build['shutit_state_dir'] + '/environment_id'
		if self.file_exists(environment_id_dir,directory=True):
			files = self.ls(environment_id_dir)
			if len(files) != 1 or type(files) != list:
				if len(files) == 2 and (files[0] == 'ORIGIN_ENV' or files[1] == 'ORIGIN_ENV'):
					for f in files:
						if f != 'ORIGIN_ENV':
							environment_id = f
							# Look up this environment id
							environment = shutit.get_shutit_pexpect_session_environment(environment_id)
							if environment:
								# Set that object to the _current_ environment in the PexpectSession
								# OBJECT TO _CURRENT_ ENVIRONMENT IN SHUTIT PEXPECT session OBJECT AND RETURN that object.
								self.current_environment = environment
							else:
								shutit.fail('Should not get here: environment reached but with unique build_id that matches, but object not in existence')
							# TODO: check against CygWin
							## Workaround for CygWin terminal issues. If the envid isn't in the cfg item
							## Then crudely assume it is. This will drop through and then assume we are in the origin env.
							#try:
							#	_=shutit.environment[shutit.build['current_environment_id']]
							#except Exception:
							#	shutit.build['current_environment_id'] = 'ORIGIN_ENV'
							#break
				else:
					## See comment above re: cygwin.
					#if self.file_exists('/cygdrive'):
					#	self.current_environment_id = shutit.get_shutit_pexpect_session_environment('ORIGIN_ENV')
					#else:
					#	shutit.fail('Wrong number of files in environment_id_dir: ' + environment_id_dir)
					shutit.fail('Wrong number of files in environment_id_dir: ' + environment_id_dir)
			else:
				# TODO: check against CygWin
				#if self.file_exists('/cygdrive'):
				#	environment_id = 'ORIGIN_ENV'
				#else:
				environment_id = files[0]
				environment = shutit.get_shutit_pexpect_session_environment(environment_id)
				if environment:
					# Set that object to the _current_ environment in the PexpectSession
					# OBJECT TO _CURRENT_ ENVIRONMENT IN SHUTIT PEXPECT session OBJECT AND RETURN that object.
					self.current_environment = environment
				else:
					shutit.fail('Should not get here: environment reached but with unique build_id that matches, but object not in existence, ' + environment_id)
			# as far as I can tell, this should never happen?
			#if shutit.build['current_environment_id'] != environment_id:
			#	# Clean out any trace of this new environment, and return the already-existing one.
			#	self.send(' rm -rf ' + environment_id_dir + '/environment_id/' + environment_id, echo=False, loglevel=loglevel)
			#	return shutit.build['current_environment_id']
			#if not environment_id == 'ORIGIN_ENV':
			#	return shutit.get_shutit_pexpect_session_environment('ORIGIN_ENV')
			self.current_environment = environment
			return shutit.get_shutit_pexpect_session_environment(environment_id)
		new_environment = ShutItPexpectSessionEnvironment(prefix)
		# If not, create new env object, set it to current.
		self.current_environment = new_environment
		shutit.add_shutit_pexpect_session_environment(new_environment)
		# TODO: make smarter wrt ORIGIN_ENV and cacheing
		self.get_distro_info()
		self.send(' mkdir -p ' + environment_id_dir + ' && chmod -R 777 ' + shutit.build['shutit_state_dir_base'] + ' && touch ' + environment_id_dir + '/' + new_environment.environment_id, echo=False, loglevel=logging.DEBUG)
		return new_environment

 
	def in_screen(self, loglevel=logging.INFO):
		shutit = shutit_global.shutit
		if self.send_and_get_output(' echo $TMUX', record_command=False, echo=False, loglevel=loglevel) != '':
			return True
		elif self.send_and_get_output(' echo $TERM', record_command=False, echo=False, loglevel=loglevel) == 'screen':
			return True
		return False

class ShutItPexpectSessionEnvironment(object):


	def __init__(self,
	             prefix):
		"""Represents a new 'environment' in ShutIt, which corresponds to a host or any
		machine-like location (eg docker container, ssh'd to host, or even a chroot jail
		with a /tmp folder that has not been touched by shutit.
		"""
		if prefix == 'ORIGIN_ENV':
			self.environment_id = prefix
		else:
			self.environment_id = shutit_util.random_id()
		self.module_root_dir              = '/'
		self.modules_installed            = [] # has been installed in this build
		self.modules_not_installed        = [] # modules _known_ not to be installed
		self.modules_ready                = [] # has been checked for readiness and is ready (in this build)
		self.modules_recorded             = []
		self.modules_recorded_cache_valid = False
		self.install_type                 = ''
		self.distro                       = ''
		self.distro_version               = ''
		self.users                        = dict()
		self.build                        = {}
		self.build['apt_update_done']     = False
		self.build['emerge_update_done']  = False
		self.build['apk_update_done']     = False
	

