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

ShutItGlobal
|
 - set(ShutItPexpectSessionEnvironment) - environments can exist in multiple sessions (eg root one)
   |
    -ShutItLoginStack
     |
      - ShutItLoginStackItem[]
        |
         - ShutItBackgroundCommand[]


ShutIt
|
 - current_pexpect_session
|
 - dict(ShutItPexpectSessions)
   |
    - each ShutItPexpectSession contains a current ShutItPexpectSessionEnvironment object

"""

try:
	from md5 import md5
except ImportError: # pragma: no cover
	from hashlib import md5
import logging
import string
import time
import os
import re
import base64
import sys
import textwrap
import binascii
import pexpect
import shutit_util
import shutit_global
import package_map
import shutit_class
from shutit_login_stack import ShutItLoginStack
from shutit_sendspec import ShutItSendSpec
from shutit_module import ShutItFailException
from shutit_pexpect_session_environment import ShutItPexpectSessionEnvironment
from shutit_background import ShutItBackgroundCommand


PY3 = (sys.version_info[0] >= 3)


class ShutItPexpectSession(object):

	def __init__(self,
	             shutit,
	             pexpect_session_id,
	             command,
	             args=None,
	             timeout=300,
	             maxread=2000,
	             searchwindowsize=None,
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
		if PY3: # pragma: no cover
			encoding = 'utf-8'
		assert isinstance(shutit, shutit_class.ShutIt)
		self.shutit                    = shutit
		self.check_exit                = True
		self.default_expect            = [shutit_global.shutit_global_object.base_prompt]
		self.pexpect_session_id        = pexpect_session_id
		self.login_stack               = ShutItLoginStack()
		self.current_environment       = None
		args = args or []
		self.pexpect_child       = self._spawn_child(command=command,
		                                             args=args,
		                                             timeout=timeout,
		                                             maxread=maxread,
		                                             searchwindowsize=searchwindowsize,
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
	                 args=None,
	                 timeout=30,
	                 maxread=2000,
	                 searchwindowsize=None,
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
		shutit = self.shutit
		args = args or []
		pexpect_child = pexpect.spawn(command,
		                              args=args,
		                              timeout=timeout,
		                              maxread=maxread,
		                              searchwindowsize=searchwindowsize,
		                              env=env,
		                              ignore_sighup=ignore_sighup,
		                              echo=echo,
		                              preexec_fn=preexec_fn,
		                              encoding=encoding,
		                              codec_errors=codec_errors,
		                              dimensions=dimensions)
		# Set the winsize to the theoretical maximum to reduce risk of trouble from terminal line wraps.
		# Other things have been attempted, eg tput rmam/smam without success.
		pexpect_child.setwinsize(shutit_global.shutit_global_object.pexpect_window_size[0],shutit_global.shutit_global_object.pexpect_window_size[1])
		pexpect_child.delaybeforesend=delaybeforesend
		shutit_global.shutit_global_object.log('sessions before: ' + str(shutit.shutit_pexpect_sessions),level=logging.DEBUG)
		shutit.shutit_pexpect_sessions.update({self.pexpect_session_id:self})
		shutit_global.shutit_global_object.log('sessions after: ' + str(shutit.shutit_pexpect_sessions),level=logging.DEBUG)
		return pexpect_child


	def sendline(self, sendspec):
		"""Sends line, handling background and newline directives.

		True means: 'all handled here ok'
		False means: you'll need to 'expect' the right thing from here.
		"""
		assert not sendspec.started
		#shutit_global.shutit_global_object.log('sendline: ' + str(sendspec),level=logging.DEBUG)
		try:
			# Check there are no background commands running that have block_other_commands set iff
			# this sendspec says
			if self._check_blocked(sendspec) and sendspec.ignore_background != True:
				shutit_global.shutit_global_object.log('sendline: blocked',level=logging.DEBUG)
				return False
			# If this is marked as in the background, create a background object and run in the background.
			if sendspec.run_in_background:
				shutit_global.shutit_global_object.log('sendline: run_in_background',level=logging.DEBUG)
				# If this is marked as in the background, create a background object and run in the background after newlines sorted.
				shutit_background_command_object = self.login_stack.get_current_login_item().append_background_send(sendspec)
				# Makes no sense to check exit for a background command.
				sendspec.check_exit = False
			if sendspec.nonewline != True:
				sendspec.send += '\n'
				# sendspec has newline added now, so no need to keep marker
				sendspec.nonewline = True
			if sendspec.run_in_background:
				shutit_background_command_object.run_background_command()
				return True
			else:
				shutit_global.shutit_global_object.log('sendline: actually sending: ' + sendspec.send,level=logging.DEBUG)
				self.pexpect_child.send(sendspec.send)
				return False
		except OSError:
			self.shutit.fail('Caught failure to send, assuming user has exited from pause point.')


	# Multisends must go through send() in shutit global
	def _check_blocked(self, sendspec):
		if sendspec.ignore_background:
			shutit_global.shutit_global_object.log('_check_blocked: background is ignored',level=logging.DEBUG)
			return False
		elif self.login_stack.get_current_login_item():
			if self.login_stack.get_current_login_item().find_sendspec(sendspec):
				shutit_global.shutit_global_object.log('_check_blocked: sendspec object already in there, so GTFO.',level=logging.INFO)
				return True
			if self.login_stack.get_current_login_item().has_blocking_background_send():
				if sendspec.run_in_background:
					# If we honour background tasks, and we are running in background, queue it up.
					shutit_global.shutit_global_object.log('_check_blocked: a blocking background send is running, so queue this up.',level=logging.INFO)
					self.login_stack.get_current_login_item().append_background_send(sendspec)
				elif not sendspec.run_in_background:
					shutit_global.shutit_global_object.log('_check_blocked: a blocking background send is running, so queue this up and wait.',level=logging.INFO)
					# If we honour background tasts and we are running in foreground, wait.
					#print('adding')
					#sendspec.run_in_background = True
					self.login_stack.get_current_login_item().append_background_send(sendspec)
					##print(self.login_stack)
					self.wait(sendspec=sendspec)
					## Now add this to the background sends.
					## And wait until done.
					self.wait()
				else:
					# Should be logically impossible.
					assert False
					shutit_global.shutit_global_object.log('Not yet handled?',level=logging.INFO)
					shutit_global.shutit_global_object.log(str(sendspec),level=logging.INFO)
				return True
			else:
				shutit_global.shutit_global_object.log('_check_blocked: no blocking background send',level=logging.DEBUG)
		else:
			shutit_global.shutit_global_object.log('_check_blocked: no current login item',level=logging.DEBUG)
		return False


	def wait(self, cadence=2, sendspec=None):
		"""Does not return until all background commands are completed.
		"""
		shutit_global.shutit_global_object.log('In wait.',level=logging.DEBUG)
		if sendspec:
			cadence = sendspec.wait_cadence
		shutit_global.shutit_global_object.log('Login stack is:\n' + str(self.login_stack),level=logging.DEBUG)
		while True:
			# go through each background child checking whether they've finished
			res, res_str, background_object = self.login_stack.get_current_login_item().check_background_commands_complete()
			if res:
				# When all have completed, break return the background command objects.
				break
			elif res_str in ('S','N'):
				# Do nothing, this is an unstarted or running task.
				pass
			elif res_str == 'F':
				assert background_object is not None
				assert isinstance(background_object, ShutItBackgroundCommand)
				shutit_global.shutit_global_object.log('Failure in: ' + str(self.login_stack),level=logging.DEBUG)
				self.pause_point('Background task: ' + background_object.sendspec.original_send + ' :failed.')
				return False
			else:
				self.shutit.fail('Un-handled exit code: ' + res_str) # pragma: no cover
			time.sleep(cadence)
		shutit_global.shutit_global_object.log('Wait complete.',level=logging.DEBUG)
		return True


	def login(self, sendspec):
		"""Logs the user in with the passed-in password and command.
		Tracks the login. If used, used logout to log out again.
		Assumes you are root when logging in, so no password required.
		If not, override the default command for multi-level logins.
		If passwords are required, see setup_prompt() and revert_prompt()

		@type param:           see shutit_sendspec.ShutItSendSpec
		@type sendspec:        shutit_sendspec.ShutItSendSpec
		"""
		user          = sendspec.user
		command       = sendspec.send
		prompt_prefix = sendspec.prompt_prefix
		# We don't get the default expect here, as it's either passed in, or a base default regexp.
		if isinstance(sendspec.password,str):
			shutit_global.shutit_global_object.secret_words_set.add(sendspec.password)
		r_id = shutit_util.random_id()
		if prompt_prefix is None:
			prompt_prefix = r_id
		# Be helpful - if this looks like a command that requires a user, then suggest user provides one.
		if user is None:
			user = self.whoami()
			if 'bash' not in command:
				shutit_global.shutit_global_object.log('No user supplied to login function, so retrieving who I am (' + user + '). You may want to override.',level=logging.WARNING)
		if ' ' in user:
			self.shutit.fail('user has space in it - did you mean: login(command="' + user + '")?') # pragma: no cover
		if self.shutit.build['delivery'] == 'bash' and command == 'su -':
			# We want to retain the current working directory
			command = 'su'
		# If this is a su-type command, add the user, else assume user is in the command.
		if command == 'su -' or command == 'su' or command == 'login':
			send = command + ' ' + user
		else:
			send = command
		login_expect = sendspec.expect or shutit_global.shutit_global_object.base_prompt
		# We don't fail on empty before as many login programs mess with the output.
		# In this special case of login we expect either the prompt, or 'user@' as this has been seen to work.
		general_expect = [login_expect]
		# Add in a match if we see user+ and then the login matches. Be careful not to match against 'user+@...password:'
		general_expect = general_expect + [user+'@.*'+'[#$]']
		# If not an ssh login, then we can match against user + @sign because it won't clash with 'user@adasdas password:'
		if (sendspec.is_ssh != None and sendspec.is_ssh) or command.find('ssh ') != -1:
			shutit_global.shutit_global_object.log('Assumed to be an ssh command, is_ssh: ' + str(sendspec.is_ssh) + ', command: ' + command,level=logging.DEBUG)
			# If user@ already there, remove it, as it can conflict with password lines in ssh calls.
			if user+'@' in general_expect:
				general_expect.remove(user+'@')
			general_expect.append('.*[#$]')
			send_dict={'ontinue connecting':['yes',False], 'assword:':[sendspec.password,True], r'[^t] login:':[sendspec.password,True]}
		else:
			send_dict={'ontinue connecting':['yes',False], 'assword:':[sendspec.password,True], r'[^t] login:':[sendspec.password,True], user+'@':[sendspec.password,True]}
		if user == 'bash' and command == 'su -':
			shutit_global.shutit_global_object.log('WARNING! user is bash - if you see problems below, did you mean: login(command="' + user + '")?',level=logging.WARNING)
		self.shutit.handle_note(sendspec.note,command=command + '\n\n[as user: "' + user + '"]',training_input=send)
		# r'[^t] login:' - be sure not to match 'last login:'
		echo = self.shutit.get_echo_override(sendspec.echo)
		shutit_global.shutit_global_object.log('Logging in to new ShutIt environment.' + user,level=logging.DEBUG)
		shutit_global.shutit_global_object.log('Logging in with command: ' + send + ' as user: ' + user,level=logging.DEBUG)
		shutit_global.shutit_global_object.log('Login stack before login: ' + str(self.login_stack),level=logging.DEBUG)
		res = self.multisend(ShutItSendSpec(self,
		                                    send=send,
		                                    send_dict=send_dict,
		                                    expect=general_expect,
		                                    check_exit=False,
		                                    timeout=sendspec.timeout,
		                                    fail_on_empty_before=False,
		                                    escape=sendspec.escape,
		                                    echo=echo,
		                                    remove_on_match=True,
		                                    nonewline=sendspec.nonewline,
		                                    loglevel=sendspec.loglevel))
		if res == -1:
			# Should not get here as login should not be blocked.
			assert False
		# Check exit 'by hand' here to not effect/assume setup prompt.
		if not self.get_exit_value():
			if sendspec.fail_on_fail: # pragma: no cover
				self.shutit.fail('Login failure!')
			else:
				return False
		# Setup prompt
		if prompt_prefix != None:
			self.setup_prompt(r_id,prefix=prompt_prefix)
		else:
			self.setup_prompt(r_id)
		self.login_stack.append(r_id)
		shutit_global.shutit_global_object.log('Login stack after login: ' + str(self.login_stack),level=logging.DEBUG)
		if sendspec.go_home:
			self.send(ShutItSendSpec(self,
			                         send='cd',
			                         check_exit=False,
			                         echo=False,
		                             ignore_background=True,
			                         loglevel=sendspec.loglevel))
		self.shutit.handle_note_after(note=sendspec.note,training_input=send)
		return True


	def logout(self, sendspec):
		"""Logs the user out. Assumes that login has been called.
		If login has never been called, throw an error.

			@param command: Command to run to log out (default=exit)
			@param note:    See send()
		"""
		# Block until background tasks complete.
		self.wait()
		shutit = self.shutit
		shutit.handle_note(sendspec.note,training_input=sendspec.send)
		if self.login_stack.length() > 0:
			_ = self.login_stack.pop()
			if self.login_stack.length() > 0:
				old_prompt_name	 = self.login_stack.get_current_login_id()
				self.default_expect = shutit.expect_prompts[old_prompt_name]
			else:
				# If none are on the stack, we assume we're going to the root prompt
				# set up in shutit_setup.py
				shutit.set_default_shutit_pexpect_session_expect()
		else:
			shutit.fail('Logout called without corresponding login', throw_exception=False) # pragma: no cover
		# No point in checking exit here, the exit code will be
		# from the previous command from the logged in session
		echo = shutit.get_echo_override(sendspec.echo)
		output = self.send_and_get_output(sendspec.send,
		                                  fail_on_empty_before=False,
		                                  timeout=sendspec.timeout,
		                                  echo=echo,
		                                  loglevel=sendspec.loglevel,
			                              nonewline=sendspec.nonewline)
		shutit.handle_note_after(note=sendspec.note)
		return output



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

		    shutit.send('su - auser', expect=shutit_global.shutit_global_object.base_prompt, check_exit=False)
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
		shutit = self.shutit
		local_prompt = prefix + ':' + shutit_util.random_id() + '# '
		shutit.expect_prompts[prompt_name] = local_prompt
		# Set up the PS1 value.
		# Unset the PROMPT_COMMAND as this can cause nasty surprises in the output.
		# Set the cols value, as unpleasant escapes are put in the output if the
		# input is > n chars wide.
		# checkwinsize is required for similar reasons.
		# The newline in the expect list is a hack. On my work laptop this line hangs
		# and times out very frequently. This workaround seems to work, but I
		# haven't figured out why yet - imiell.

		# Split the local prompt into two parts and separate with quotes to protect against the expect matching the command rather than the output.
		shutit_global.shutit_global_object.log('Setting up prompt.', level=logging.DEBUG)
		self.send(ShutItSendSpec(self,
		                         send=""" export SHUTIT_BACKUP_PS1_""" + prompt_name + """=$PS1 && PS1='""" + local_prompt[:2] + "''" + local_prompt[2:] + """' && unset PROMPT_COMMAND""",
		                         expect=['\r\n' + shutit.expect_prompts[prompt_name]],
		                         fail_on_empty_before=False,
		                         echo=False,
		                         loglevel=loglevel,
		                         ignore_background=True))
		shutit_global.shutit_global_object.log('Resetting default expect to: ' + shutit.expect_prompts[prompt_name],level=loglevel)
		self.default_expect = shutit.expect_prompts[prompt_name]
		hostname = shutit.send_and_get_output("""if [[ $(echo $SHELL) == '/bin/bash' ]]; then echo $HOSTNAME; elif [[ $(command hostname 2> /dev/null) != '' ]]; then hostname -s; fi""", echo=False)
		local_prompt_with_hostname = hostname + ':' + local_prompt
		shutit.expect_prompts[prompt_name] = local_prompt_with_hostname
		self.default_expect = shutit.expect_prompts[prompt_name]

		# Split the local prompt into two parts and separate with quotes to protect against the expect matching the command rather than the output.
		self.send(ShutItSendSpec(self,
		                         send=""" PS1='""" + shutit.expect_prompts[prompt_name][:2] + "''" + shutit.expect_prompts[prompt_name][2:] + """'""",
		                         echo=False,
		                         loglevel=loglevel,
		                         ignore_background=True))

		# Set up history the way shutit likes it.
		self.send(ShutItSendSpec(self,
		                         send=' command export HISTCONTROL=$HISTCONTROL:ignoredups:ignorespace',
		                         echo=False,
		                         loglevel=loglevel,
		                         ignore_background=True))
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
		shutit = self.shutit
		expect = new_expect or self.default_expect
		#           v the space is intentional, to avoid polluting bash history.
		self.send(ShutItSendSpec(self,
		                         send=(' PS1="${SHUTIT_BACKUP_PS1_%s}" && unset SHUTIT_BACKUP_PS1_%s') % (old_prompt_name, old_prompt_name),
		                         expect=expect,
		                         check_exit=False,
		                         fail_on_empty_before=False,
		                         echo=False,
		                         loglevel=logging.DEBUG,
		                         ignore_background=True))
		if not new_expect:
			shutit_global.shutit_global_object.log('Resetting default expect to default',level=logging.DEBUG)
			shutit.set_default_shutit_pexpect_session_expect()
		_ = self.init_pexpect_session_environment(old_prompt_name)




	def expect(self,
	           expect,
	           searchwindowsize=None,
	           maxread=None,
	           timeout=None):
		"""Handle child expects, with EOF and TIMEOUT handled
		"""
		if isinstance(expect, str):
			expect = [expect]
		if searchwindowsize != None:
			old_searchwindowsize = self.pexpect_child.searchwindowsize
			self.pexpect_child.searchwindowsize = searchwindowsize
		if maxread != None:
			old_maxread = self.pexpect_child.maxread
			self.pexpect_child.maxread = maxread
		res = self.pexpect_child.expect(expect + [pexpect.TIMEOUT] + [pexpect.EOF], timeout=timeout)
		if searchwindowsize != None:
			self.pexpect_child.searchwindowsize = old_searchwindowsize
		if maxread != None:
			self.pexpect_child.maxread = old_maxread
		return res


	def replace_container(self, new_target_image_name, go_home=None):
		"""Replaces a container. Assumes we are in Docker context.
		"""
		shutit = self.shutit
		shutit_global.shutit_global_object.log('Replacing container with ' + new_target_image_name + ', please wait...',level=logging.INFO)
		shutit_global.shutit_global_object.log(shutit.print_session_state(),level=logging.DEBUG)

		# Destroy existing container.
		conn_module = None
		for mod in shutit.conn_modules:
			if mod.module_id == shutit.build['conn_module']:
				conn_module = mod
				break
		if conn_module is None:
			shutit.fail('''Couldn't find conn_module ''' + shutit.build['conn_module']) # pragma: no cover
		container_id = shutit.target['container_id']
		conn_module.destroy_container(shutit, 'host_child', 'target_child', container_id)

		# Start up a new container.
		shutit.target['docker_image'] = new_target_image_name
		target_child = conn_module.start_container(shutit, self.pexpect_session_id)
		conn_module.setup_target_child(shutit, target_child)
		shutit_global.shutit_global_object.log('Container replaced',level=logging.INFO)
		shutit_global.shutit_global_object.log(shutit.print_session_state(),level=logging.DEBUG)
		# New session - log in. This makes the assumption that we are nested
		# the same level in in terms of shells (root shell + 1 new login shell).
		target_child = shutit.get_shutit_pexpect_session_from_id('target_child')
		if go_home != None:
			target_child.login(ShutItSendSpec(self,
			                                  send='bash --noprofile --norc',
			                                  echo=False,
			                                  go_home=go_home))
		else:
			target_child.login(ShutItSendSpec(self,
			                                  send='bash --noprofile --norc',
			                                  echo=False))
		return True


	def whoami(self,
	           note=None,
	           loglevel=logging.DEBUG):
		"""Returns the current user by executing "whoami".

		@param note:     See send()

		@return: the output of "whoami"
		@rtype: string
		"""
		shutit = self.shutit
		shutit.handle_note(note)
		res = self.send_and_get_output(' command whoami',
		                               echo=False,
		                               loglevel=loglevel).strip()
		if res == '':
			res = self.send_and_get_output(' command id -u -n',
			                               echo=False,
			                               loglevel=loglevel).strip()
		shutit.handle_note_after(note=note)
		return res



	def check_last_exit_values(self,
	                           send,
	                           expect=None,
	                           exit_values=None,
	                           retry=0,
	                           retbool=False):
		"""Internal function to check the exit value of the shell. Do not use.
		"""
		shutit = self.shutit
		expect = expect or self.default_expect
		if not self.check_exit:
			shutit_global.shutit_global_object.log('check_exit configured off, returning', level=logging.DEBUG)
			return True
		if exit_values is None:
			exit_values = ['0']
		if isinstance(exit_values, int):
			exit_values = [str(exit_values)]
		# Don't use send here (will mess up last_output)!
		# Space before "echo" here is sic - we don't need this to show up in bash history
		assert not self.sendline(ShutItSendSpec(self,
		                                        send=' echo EXIT_CODE:$?',
		                                        ignore_background=True))
		shutit_global.shutit_global_object.log('Expecting: ' + str(expect),level=logging.DEBUG)
		self.expect(expect,timeout=60)
		res = shutit.match_string(str(self.pexpect_child.before), '^EXIT_CODE:([0-9][0-9]?[0-9]?)$')
		if res not in exit_values or res is None: # pragma: no cover
			res_str = res or str(res)
			shutit_global.shutit_global_object.log('shutit_pexpect_child.after: ' + str(self.pexpect_child.after), level=logging.DEBUG)
			shutit_global.shutit_global_object.log('Exit value from command: ' + str(send) + ' was:' + res_str, level=logging.DEBUG)
			msg = ('\nWARNING: command:\n' + send + '\nreturned unaccepted exit code: ' + res_str + '\nIf this is expected, pass in check_exit=False or an exit_values array into the send function call.')
			shutit.build['report'] += msg
			if retbool:
				return False
			elif shutit_global.shutit_global_object.interactive >= 1:
				# This is a failure, so we pass in level=0
				shutit.pause_point(msg + '\n\nInteractive, so not retrying.\nPause point on exit_code != 0 (' + res_str + '). CTRL-C to quit', shutit_pexpect_child=self.pexpect_child, level=0)
			elif retry == 1:
				shutit.fail('Exit value from command\n' + send + '\nwas:\n' + res_str, throw_exception=False) # pragma: no cover
			else:
				return False
		return True



	def pause_point(self,
	                msg='SHUTIT PAUSE POINT',
	                print_input=True,
	                resize=True,
	                colour='32',
	                default_msg=None,
	                interact=False,
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
		@param interact:     Interact without mediation, and set up environment.
		@param wait:         Wait a few seconds rather than for input (for video mode)

		@type msg:           string
		@type print_input:   boolean
		@type resize:        boolean
		@type wait:          decimal

		@return:             True if pause point handled ok, else false
		"""
		shutit = self.shutit
		# Try and stop user being 'clever' if we are in an exam and not in debug
		if shutit.build['exam'] and shutit_global.shutit_global_object.loglevel not in ('DEBUG',):
			self.send(ShutItSendSpec(self,
			                         send=' command alias exit=/bin/true && command alias logout=/bin/true && command alias kill=/bin/true && command alias alias=/bin/true',
			                         echo=False,
			                         record_command=False,
			                         ignore_background=True))
		if print_input:
			# Do not resize if we are in video mode (ie wait > 0)
			if resize and wait < 0:
				# It is possible we do not have distro set yet, so wrap in try/catch
				try:
					assert not self.sendline(ShutItSendSpec(self,
					                                        send='',
					                                        ignore_background=True))
				except Exception:
					pass
			if default_msg is None:
				if not shutit.build['video'] and not shutit.build['training'] and not shutit.build['exam'] and not shutit.build['walkthrough'] and shutit_global.shutit_global_object.loglevel not in ('DEBUG',):
					pp_msg = '\r\nYou now have a standard shell.'
					if not interact:
						pp_msg += '\r\nHit CTRL and then ] at the same time to continue ShutIt run, CTRL-q to quit.'
					if shutit.build['delivery'] == 'docker':
						pp_msg += '\r\nHit CTRL and u to save the state to a docker image'
					shutit_global.shutit_global_object.log(shutit_util.colourise(colour,'\r\n' + 80*'=' + '\r\n' + msg + '\r\n' + 80*'='+'\r\n' + pp_msg),transient=True,level=logging.CRITICAL)
				else:
					shutit_global.shutit_global_object.log('\r\n' + (shutit_util.colourise(colour, msg)),transient=True,level=logging.critical)
			else:
				shutit_global.shutit_global_object.log(shutit_util.colourise(colour, msg) + '\r\n' + default_msg + '\r\n',transient=True,level=logging.CRITICAL)
			oldlog = self.pexpect_child.logfile_send
			self.pexpect_child.logfile_send = None
			if wait > 0:
				time.sleep(wait)
			else:
				# Re-set the window size to match the original window.
				# TODO: sigwinch. Line assumes no change.
				self.pexpect_child.setwinsize(shutit_global.shutit_global_object.root_window_size[0],shutit_global.shutit_global_object.root_window_size[1])
				# TODO: handle exams better?
				self.pexpect_child.expect('.*')
				if not shutit.build['exam'] and shutit_global.shutit_global_object.loglevel not in ('DEBUG',):
					# Give them a 'normal' shell.
					assert not self.sendline(ShutItSendSpec(self,
					                                        send=' bash',
					                                        ignore_background=True))
					self.pexpect_child.expect('.*')
				if interact:
					self.pexpect_child.interact()
				try:
					self.pexpect_child.interact(input_filter=self._pause_input_filter)
					self.handle_pause_point_signals()
				except Exception as e:
					shutit.fail('Terminating ShutIt within pause point.\r\n' + str(e)) # pragma: no cover
				if not shutit.build['exam'] and shutit_global.shutit_global_object.loglevel not in ('DEBUG',):
					assert not self.send(ShutItSendSpec(self,
					                                    send=' exit',
					                                    ignore_background=True))
			self.pexpect_child.logfile_send = oldlog
		else:
			pass
		shutit.build['ctrlc_stop'] = False
		return True


	def handle_pause_point_signals(self):
		shutit = self.shutit
		if shutit_global.shutit_global_object.signal_id == 29:
			# clear the signal
			shutit_global.shutit_global_object.signal_id = 0
			shutit_global.shutit_global_object.log('\r\nCTRL-] caught, continuing with run...',level=logging.INFO,transient=True)
		elif isinstance(shutit_global.shutit_global_object.signal_id, int) and shutit_global.shutit_global_object.signal_id not in (0,4,7,8,17,19):
			shutit_global.shutit_global_object.log('\r\nLeaving interact without CTRL-] and shutit_signal is not recognised, shutit_signal value: ' + str(shutit_global.shutit_global_object.signal_id),level=logging.CRITICAL,transient=True)
		elif shutit_global.shutit_global_object.signal_id == 0:
			shutit_global.shutit_global_object.log('\r\nLeaving interact without CTRL-], assuming exit.',level=logging.CRITICAL,transient=True)
			shutit_global.shutit_global_object.handle_exit(exit_code=1)
		if shutit.build['exam'] and shutit_global.shutit_global_object.loglevel not in ('DEBUG',):
			self.send(ShutItSendSpec(self,
			                         send=' unalias exit && unalias logout && unalias kill && unalias alias',
			                         echo=False,
			                         record_command=False,
			                         ignore_background=True))
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
		shutit = self.shutit
		shutit.handle_note(note, 'Looking for filename in current environment: ' + filename)
		test_type = '-d' if directory is True else '-e' if directory is None else '-a'
		#       v the space is intentional, to avoid polluting bash history.
		test = ' test %s %s' % (test_type, filename)
		output = self.send_and_get_output(test + ' && echo FILEXIST-""FILFIN || echo FILNEXIST-""FILFIN',
		                                  record_command=False,
		                                  echo=False,
		                                  loglevel=loglevel)
		res = shutit.match_string(output, '^(FILEXIST|FILNEXIST)-FILFIN$')
		ret = False
		if res == 'FILEXIST':
			ret = True
		elif res == 'FILNEXIST':
			pass
		else: # pragma: no cover
			# Change to log?
			shutit_global.shutit_global_object.log(repr('before>>>>:%s<<<< after:>>>>%s<<<<' % (self.pexpect_child.before, self.pexpect_child.after)),transient=True)
			shutit.fail('Did not see FIL(N)?EXIST in output:\n' + output)
		shutit.handle_note_after(note=note)
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
		shutit = self.shutit
		shutit.handle_note(note, 'Changing to path: ' + path)
		shutit_global.shutit_global_object.log('Changing directory to path: "' + path + '"', level=logging.DEBUG)
		if shutit.build['delivery'] in ('bash','dockerfile'):
			self.send(ShutItSendSpec(self,
			                         send=' command cd ' + path,
			                         timeout=timeout,
			                         echo=False,
			                         loglevel=loglevel))
		elif shutit.build['delivery'] in ('docker',):
			os.chdir(path)
		else:
			shutit.fail('chdir not supported for delivery method: ' + str(shutit.build['delivery'])) # pragma: no cover
		shutit.handle_note_after(note=note)
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
		shutit = self.shutit
		shutit.handle_note(note)
		cmd = ' command stat -c %a ' + filename
		self.send(ShutItSendSpec(self,
		                         send=' ' + cmd,
		                         check_exit=False,
		                         echo=False,
		                         loglevel=loglevel,
		                         ignore_background=True))
		res = shutit.match_string(self.pexpect_child.before, '([0-9][0-9][0-9])')
		shutit.handle_note_after(note=note)
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
		shutit = self.shutit
		shutit.handle_note(note)
		if not shutit_util.check_regexp(match_regexp):
			shutit.fail('Illegal regexp found in add_to_bashrc call: ' + match_regexp) # pragma: no cover
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
		shutit = self.shutit
		shutit.handle_note(note)
		# v the space is intentional, to avoid polluting bash history.
		self.send(ShutItSendSpec(self,
		                         send=' command cut -d: -f3 /etc/paswd | grep -w ^' + user_id + '$ | wc -l',
		                         expect=self.default_expect,
		                         echo=False,
		                         loglevel=loglevel,
		                         ignore_background=True))
		shutit.handle_note_after(note=note)
		if shutit.match_string(self.pexpect_child.before, '^([0-9]+)$') == '1':
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
		shutit = self.shutit
		shutit.handle_note(note)
		if isinstance(password, str):
			shutit_global.shutit_global_object.secret_words_set.add(password)
		self.install('passwd')
		if self.current_environment.install_type == 'apt':
			self.send(ShutItSendSpec(self,
			                         send='passwd ' + user,
			                         expect='Enter new',
			                         check_exit=False,
			                         ignore_background=True))
			self.send(ShutItSendSpec(self,
			                         send=password,
			                         expect='Retype new',
			                         check_exit=False,
			                         echo=False,
			                         ignore_background=True
			                         ))
			self.send(ShutItSendSpec(self,
			                         send=password,
			                         expect=self.default_expect,
			                         echo=False,
			                         ignore_background=True,
			                         ))
		elif self.current_environment.install_type == 'yum':
			self.send(ShutItSendSpec(self,
			                         send='passwd ' + user,
			                         expect='ew password',
			                         check_exit=False,
			                         ignore_background=True))
			self.send(ShutItSendSpec(self,
			                         send=password,
			                         expect='ew password',
			                         check_exit=False,
			                         echo=False,
			                         ignore_background=True))
			self.send(ShutItSendSpec(self,
			                         send=password,
			                         expect=self.default_expect,
			                         echo=False,
			                         ignore_background=True))
		else:
			self.send(ShutItSendSpec(self,
			                         send='passwd ' + user,
			                         expect='Enter new',
			                         check_exit=False,
			                         ignore_background=True))
			self.send(ShutItSendSpec(self,
			                         send=password,
			                         expect='Retype new',
			                         check_exit=False,
			                         echo=False,
			                         ignore_background=True))
			self.send(ShutItSendSpec(self,
			                         send=password,
			                         expect=self.default_expect,
			                         echo=False,
			                         ignore_background=True))
		shutit.handle_note_after(note=note)
		return True



	def lsb_release(self,
	                loglevel=logging.DEBUG):
		"""Get distro information from lsb_release.
		"""
		#          v the space is intentional, to avoid polluting bash history.
		shutit = self.shutit
		d = {}
		self.send(ShutItSendSpec(self,
		                         send=' command lsb_release -a',
		                         check_exit=False,
		                         echo=False,
		                         loglevel=loglevel,
		                         ignore_background=True))
		res = shutit.match_string(self.pexpect_child.before, r'^Distributor[\s]*ID:[\s]*(.*)$')
		if isinstance(res, str):
			dist_string = res
			d['distro']       = dist_string.lower().strip()
			d['install_type'] = (package_map.INSTALL_TYPE_MAP[dist_string.lower()])
		else:
			return d
		res = shutit.match_string(self.pexpect_child.before, r'^Release:[\s*](.*)$')
		if isinstance(res, str):
			version_string = res
			d['distro_version'] = version_string
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
		shutit = self.shutit
		shutit.handle_note(note)
		if len(locations) == 0 or not isinstance(locations, list):
			raise ShutItFailException('Locations should be a list containing base of the url.')
		retry_orig = retry
		if not self.command_available(command):
			self.install('curl')
			if not self.command_available('curl'):
				self.install('wget')
				command = 'wget -qO- '
				if not self.command_available('wget'):
					shutit.fail('Could not install curl or wget, inform maintainers.') # pragma: no cover
		for location in locations:
			retry = retry_orig
			if location[-1] == '/':
				location = location[0:-1]
			while retry >= 0:
				send = command + ' ' + location + '/' + filename + ' > ' + filename
				self.send(ShutItSendSpec(self,
				                         send=send,
				                         check_exit=False,
				                         expect=self.default_expect,
				                         timeout=timeout,
				                         fail_on_empty_before=fail_on_empty_before,
				                         record_command=record_command,
				                         echo=False,
				                         loglevel=loglevel,
				                         ignore_background=True))
				if retry == 0:
					self.check_last_exit_values(send,
					                            expect=self.default_expect,
					                            exit_values=exit_values,
					                            retbool=False)
				elif not self.check_last_exit_values(send,
				                                     expect=self.default_expect,
				                                     exit_values=exit_values,
				                                     retbool=True):
					shutit_global.shutit_global_object.log('Sending: ' + send + ' failed, retrying', level=logging.DEBUG)
					retry -= 1
					continue
				# If we get here, all is ok.
				shutit.handle_note_after(note=note)
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
		shutit = self.shutit
		shutit.handle_note(note)
		exists = False
		if user == '':
			return exists
		#                v the space is intentional, to avoid polluting bash history.
		# The quotes before XIST are deliberate, to prevent the command from matching the expect.
		ret = self.send(ShutItSendSpec(self,
		                               send=' command id %s && echo E""XIST || echo N""XIST' % user,
		                               expect=['NXIST', 'EXIST'],
		                               echo=False,
		                               loglevel=loglevel,
		                               ignore_background=True))
		if ret:
			exists = True
		# sync with the prompt
		self.expect(self.default_expect)
		shutit.handle_note_after(note=note)
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
		shutit = self.shutit
		shutit.handle_note(note)
		# THIS DOES NOT WORK - WHY? TODO
		if self.current_environment.install_type == 'apt':
			#            v the space is intentional, to avoid polluting bash history.
			return self.send_and_get_output(' dpkg -s ' + package + """ | grep '^Status: install ok installed' | wc -l""",loglevel=loglevel) == '1'
		elif self.current_environment.install_type == 'yum':
			# TODO: check whether it's already installed?. see yum notes  yum list installed "$@" >/dev/null 2>&1
			self.send(ShutItSendSpec(self,
			                         send=' yum list installed ' + package + ' > /dev/null 2>&1',
			                         check_exit=False,
			                         loglevel=loglevel,
			                         ignore_background=True))
			return self.check_last_exit_values('install TODO change this',retbool=True)
		else:
			return False



	def command_available(self,
	                      command,
	                      note=None,
	                      loglevel=logging.DEBUG):
		shutit = self.shutit
		shutit.handle_note(note)
		output = self.send_and_get_output(' command -V ' + command + ' > /dev/null',
		                                  echo=False,
		                                  loglevel=loglevel,
		                                  check_sudo=False).strip()
		return output == ''


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
		shutit = self.shutit
		shutit.handle_note(note)
		if not self.current_environment.modules_recorded_cache_valid:
			if self.file_exists(shutit_global.shutit_global_object.shutit_state_dir_build_db_dir + '/module_record',directory=True):
				# Bit of a hack here to get round the long command showing up as the first line of the output.
				tmpid = shutit_util.random_id()
				cmd = 'find ' + shutit_global.shutit_global_object.shutit_state_dir_build_db_dir + r"""/module_record/ -name built | sed 's@^.""" + shutit_global.shutit_global_object.shutit_state_dir_build_db_dir + r"""/module_record.\([^/]*\).built@\1@' > """ + shutit_global.shutit_global_object.shutit_state_dir_build_db_dir + '/' + tmpid
				self.send(ShutItSendSpec(self,
				                         send=' ' + cmd,
				                         echo=False,
				                         loglevel=loglevel,
				                         ignore_background=True))
				built = self.send_and_get_output(' command cat ' + shutit_global.shutit_global_object.shutit_state_dir_build_db_dir + '/' + tmpid,
				                                 echo=False,
				                                 loglevel=loglevel).strip()
				self.send(ShutItSendSpec(self,
				                         send=' command rm -rf ' + shutit_global.shutit_global_object.shutit_state_dir_build_db_dir + '/' + tmpid,
				                         echo=False,
				                         loglevel=loglevel,
				                         ignore_background=True))
				built_list = built.split('\r\n')
				self.current_environment.modules_recorded = built_list
			# Either there was no directory (so the cache is valid), or we've built the cache, so mark as good.
			self.current_environment.modules_recorded_cache_valid = True
		# Modules recorded cache will be valid at this point, so check the pre-recorded modules and the in-this-run installed cache.
		shutit.handle_note_after(note=note)
		return module_id in self.current_environment.modules_recorded or module_id in self.current_environment.modules_installed


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
		shutit = self.shutit
		# should this blow up?
		shutit.handle_note(note)
		if not self.file_exists(directory,directory=True):
			shutit.fail('ls: directory\n\n' + directory + '\n\ndoes not exist', throw_exception=False) # pragma: no cover
		files = self.send_and_get_output(' command ls ' + directory,
		                                 echo=False,
		                                 loglevel=loglevel,
		                                 fail_on_empty_before=False)
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
		shutit.handle_note_after(note=note)
		return files


	def install(self,
	            package,
	            options=None,
	            timeout=3600,
	            force=False,
	            check_exit=True,
	            reinstall=False,
	            run_in_background=False,
	            ignore_background=False,
	            block_other_commands=True,
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
		shutit = self.shutit
		# If separated by spaces, install separately
		if package.find(' ') != -1:
			ok = True
			for p in package.split(' '):
				if not self.install(p,options,timeout,force,check_exit,reinstall,note):
					ok = False
			return ok
		# Some packages get mapped to the empty string. If so, bail out with 'success' here.
		if note != None:
			shutit.handle_note('Installing package: ' + package + '\n' + note)
		shutit_global.shutit_global_object.log('Installing package: ' + package,level=loglevel)
		if options is None: options = {}
		install_type = self.current_environment.install_type
		if install_type == 'src':
			# If this is a src build, we assume it's already installed.
			return True
		opts = ''
		cmd = ''
		if self.package_installed(package):
			shutit_global.shutit_global_object.log(package + ' already installed.',level=loglevel)
			return True
		if install_type == 'apt':
			if not shutit.get_current_shutit_pexpect_session_environment().build['apt_update_done'] and self.whoami() == 'root':
				self.send(ShutItSendSpec(self,
				                         send='apt-get update -y',
				                         loglevel=logging.INFO,
				                         run_in_background=False,
				                         ignore_background=False,
				                         block_other_commands=True))
				shutit.get_current_shutit_pexpect_session_environment().build['apt_update_done'] = True
			cmd += 'DEBIAN_FRONTEND=noninteractive apt-get install'
			if 'apt' in options:
				opts = options['apt']
			else:
				opts = '-y'
				if shutit_global.shutit_global_object.loglevel > logging.DEBUG:
					opts += ' -qq'
				if force:
					opts += ' --force-yes'
				if reinstall:
					opts += ' --reinstall'
		elif install_type == 'yum':
			# TODO: check whether it's already installed?. see yum notes  yum list installed "$@" >/dev/null 2>&1
			cmd += 'yum install'
			if 'yum' in options:
				opts = options['yum']
			else:
				if shutit_global.shutit_global_object.loglevel > logging.DEBUG:
					opts += ' -q'
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
		# This is especially helpful with automated exam.
		# Also can help when packages are interdependent, eg 'epel-release asciinema',
		# which requires that epel-release is fully installed before asciinema can be.
		if package.strip() != '':
			fails = 0
			while True:
				pw = self.get_sudo_pass_if_needed(shutit, ignore_brew=True)
				if pw != '':
					cmd = 'sudo ' + cmd
					res = self.multisend(ShutItSendSpec(self,
					                                    send='%s %s %s' % (cmd, opts, package),
					                                    send_dict={'assword':[pw,True]},
					                                    expect=['Unable to fetch some archives',self.default_expect],
					                                    timeout=timeout,
					                                    check_exit=False,
					                                    loglevel=loglevel,
					                                    echo=False,
					                                    secret=True))
					if res == -1:
						## Should not happen
						#assert False
						break
					shutit_global.shutit_global_object.log('Result of install attempt was: ' + str(res),level=logging.DEBUG)
				else:
					res = self.send(ShutItSendSpec(self,
					                               send='%s %s %s' % (cmd, opts, package),
					                               expect=['Unable to fetch some archives',self.default_expect],
					                               timeout=timeout,
					                               check_exit=False,
					                               loglevel=loglevel,
					                               ignore_background=ignore_background,
					                               run_in_background=run_in_background,
				                                   block_other_commands=block_other_commands))
					if res == -1:
						## Should not happen
						#assert False
						break
					shutit_global.shutit_global_object.log('Result of install attempt was: ' + str(res),level=logging.DEBUG)
				# Does not work!
				if res == 1:
					break
				else:
					fails += 1
					if fails >= 3:
						shutit.pause_point('Failed to install ' + package)
						return False
		else:
			# package not required
			shutit_global.shutit_global_object.log('Package not required.',level=logging.DEBUG)

		shutit_global.shutit_global_object.log('Package is installed.',level=logging.DEBUG)
		# Sometimes we see installs (eg yum) reset the terminal to a state
		# ShutIt does not like.
		self.reset_terminal()
		shutit.handle_note_after(note=note)
		return True


	def reset_terminal(self, expect=None):
		"""Resets the terminal to as good a state as we can try.
		Tries to ensure that we have 'expect'ed the last prompt seen.
		"""
		shutit_global.shutit_global_object.log('Resetting terminal begin.',level=logging.DEBUG)
		exp_string = 'SHUTIT_TERMINAL_RESET'
		assert not self.sendline(ShutItSendSpec(self,
		                                        send=' echo ' + exp_string,
		                                        ignore_background=True))
		self.expect(exp_string)
		expect = expect or self.default_expect
		self.expect(expect)
		shutit_global.shutit_global_object.log('Resetting terminal done.',level=logging.DEBUG)


	def get_memory(self, note=None):
		"""Returns memory available for use in k as an int"""
		shutit = self.shutit
		shutit.handle_note(note)
		if self.current_environment.distro == 'osx':
			memavail = self.send_and_get_output("""command vm_stat | grep ^Pages.free: | awk '{print $3}' | tr -d '.'""",
			                                    timeout=3,
			                                    echo=False)
			memavail = int(memavail)
			memavail *= 4
		else:
			memavail = self.send_and_get_output("""command cat /proc/meminfo  | grep MemAvailable | awk '{print $2}'""",
			                                    timeout=3,
			                                    echo=False)
			if memavail == '':
				memavail = self.send_and_get_output("""command free | grep buffers.cache | awk '{print $3}'""",
				                                    timeout=3,
				                                    echo=False)
			memavail = int(memavail)
		shutit.handle_note_after(note=note)
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
		shutit = self.shutit
		if note != None:
			shutit.handle_note('Removing package: ' + package + '\n' + note)
		if options is None: options = {}
		install_type = self.current_environment.install_type
		cmd = ''
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
		pw = self.get_sudo_pass_if_needed(shutit, ignore_brew=True)
		if pw != '':
			cmd = 'sudo ' + cmd
			res = self.multisend(ShutItSendSpec(self,
			                                    send='%s %s %s' % (cmd, opts, package),
			                                    send_dict={'assword:':[pw,True]},
			                                    timeout=timeout,
			                                    exit_values=['0','100'],
			                                    echo=False,
			                                    secret=True))
			if res == -1:
				# Should not happen
				assert False
		else:
			self.send(ShutItSendSpec(self,
			                         send='%s %s %s' % (cmd, opts, package),
			                         timeout=timeout,
			                         exit_values=['0','100'],
			                         ignore_background=False,
			                         run_in_background=False,
			                         block_other_commands=True))
		shutit.handle_note_after(note=note)
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
		shutit = self.shutit
		shutit.handle_note(note)
		shutit_global.shutit_global_object.log('Matching output from: "' + send + '" to one of these regexps:' + str(matches),level=logging.INFO)
		echo = shutit.get_echo_override(echo)
		output = self.send_and_get_output(send,
		                                  retry=retry,
		                                  strip=strip,
		                                  echo=echo,
		                                  loglevel=loglevel)
		if isinstance(matches, str):
			matches = [matches]
		shutit.handle_note_after(note=note)
		for match in matches:
			if shutit.match_string(output, match) != None:
				shutit_global.shutit_global_object.log('Matched output, return True',level=logging.DEBUG)
				return True
		shutit_global.shutit_global_object.log('Failed to match output, return False',level=logging.DEBUG)
		return False


	def send_and_get_output(self,
	                        send,
	                        timeout=None,
	                        retry=3,
	                        strip=True,
	                        preserve_newline=False,
	                        note=None,
	                        record_command=True,
	                        echo=None,
	                        fail_on_empty_before=True,
	                        check_sudo=True,
	                        nonewline=False,
	                        ignore_background=False,
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
		shutit = self.shutit
		shutit.handle_note(note, command=str(send))
		shutit_global.shutit_global_object.log('Retrieving output from command: ' + send,level=loglevel)
		# Don't check exit, as that will pollute the output. Also, it's quite likely the submitted command is intended to fail.
		echo = shutit.get_echo_override(echo)
		send = shutit.get_send_command(send)
		self.send(ShutItSendSpec(self,
		                         send=send,
		                         check_exit=False,
		                         retry=retry,
		                         echo=echo,
		                         timeout=timeout,
		                         record_command=record_command,
		                         fail_on_empty_before=fail_on_empty_before,
		                         check_sudo=check_sudo,
		                         nonewline=nonewline,
		                         loglevel=loglevel,
		                         ignore_background=ignore_background))
		before = self.pexpect_child.before

		if len(before):
			preserve_newline = bool(preserve_newline and before[-1] == '\n')
		# Remove the command we ran in from the output.
		before = before.strip(send)
		if strip:
			# cf: http://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
			ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
			string_with_termcodes = before.strip()
			string_without_termcodes = ansi_escape.sub('', string_with_termcodes)
			#string_without_termcodes_stripped = string_without_termcodes.strip()
			# Strip out \rs to make it output the same as a typical CL. This could be optional.
			string_without_termcodes_stripped_no_cr = string_without_termcodes.replace('\r','')
			if preserve_newline:
				ret = string_without_termcodes_stripped_no_cr + '\n'
			else:
				ret = string_without_termcodes_stripped_no_cr
		else:
			ret = before
		shutit_global.shutit_global_object.log('send_and_get_output returning:\n' + ret, level=logging.DEBUG)
		shutit.handle_note_after(note=note)
		return ret


	def get_env_pass(self,user=None,msg=None,note=None):
		"""Gets a password from the user if one is not already recorded for this environment.

		@param user:    username we are getting password for
		@param msg:     message to put out there
		"""
		shutit = self.shutit
		shutit.handle_note(note)
		user = user or self.whoami()
		# cygwin does not have root
		if self.current_environment.distro == 'cygwin':
			return
		if user not in self.current_environment.users.keys():
			self.current_environment.users.update({user:None})
		if not self.current_environment.users[user] and user != 'root':
			msg = msg or 'Please input the sudo password for user: ' + user
			self.current_environment.users[user] = shutit_util.get_input(msg,ispass=True)
			shutit_global.shutit_global_object.secret_words_set.add(self.current_environment.users[user])
		return self.current_environment.users[user]


	def whoarewe(self,
	             note=None,
	             loglevel=logging.DEBUG):
		"""Returns the current group.

		@param note:     See send()

		@return: the first group found
		@rtype: string
		"""
		shutit = self.shutit
		shutit.handle_note(note)
		res = self.send_and_get_output(' command id -n -g',
		                               echo=False,
		                               loglevel=loglevel).strip()
		shutit.handle_note_after(note=note)
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
		shutit = self.shutit
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
						shutit.get_current_shutit_pexpect_session_environment().build['apt_update_done'] = True
						self.send(ShutItSendSpec(self,
						                         send='DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y -qq lsb-release',
						                         loglevel=loglevel,
						                         ignore_background=True))
				d = self.lsb_release()
				install_type   = d['install_type']
				distro         = d['distro']
				distro_version = d['distro_version']
			elif install_type == 'yum' and shutit.build['delivery'] in ('docker', 'dockerfile'):
				if self.file_exists('/etc/redhat-release'):
					output = self.send_and_get_output(' command cat /etc/redhat-release',
					                                  echo=False,
					                                  loglevel=loglevel)
					if re.match('^centos.*$', output.lower()) or re.match('^red hat.*$', output.lower()) or re.match('^fedora.*$', output.lower()) or True:
						self.send_and_match_output('yum install -y -t redhat-lsb epel-release',
						                           'Complete!',
						                           loglevel=loglevel)
				else:
					if not self.command_available('lsb_release'):
						self.send(ShutItSendSpec(self,
						                         send='yum install -y lsb-release',
						                         loglevel=loglevel,
						                         ignore_background=True))
				install_type   = d['install_type']
				distro         = d['distro']
				distro_version = d['distro_version']
			elif install_type == 'apk' and shutit.build['delivery'] in ('docker','dockerfile'):
				if not shutit.get_current_shutit_pexpect_session_environment().build['apk_update_done'] and self.whoami() == 'root':
					self.send(ShutItSendSpec(self,
					                         send='apk -q update',
					                         ignore_background=True,
					                         loglevel=logging.INFO))
					shutit.get_current_shutit_pexpect_session_environment().build['apk_update_done'] = True
				self.send(ShutItSendSpec(self,
				                         send='apk -q add bash',
				                         ignore_background=True,
				                         loglevel=loglevel))
				install_type   = 'apk'
				distro         = 'alpine'
				distro_version = '1.0'
			elif install_type == 'pacman' and shutit.build['delivery'] in ('docker','dockerfile') and self.whoami() == 'root':
				if not shutit.get_current_shutit_pexpect_session_environment().build['pacman_update_done']:
					shutit.get_current_shutit_pexpect_session_environment().build['pacman_update_done'] = True
					self.send(ShutItSendSpec(self,
					                         send='pacman -Syy',
					                         ignore_background=True,
					                         loglevel=logging.INFO))
				install_type   = d['install_type']
				distro         = d['distro']
				distro_version = '1.0'
			elif install_type == 'emerge' and shutit.build['delivery'] in ('docker','dockerfile'):
				if not shutit.get_current_shutit_pexpect_session_environment().build['emerge_update_done'] and self.whoami() == 'root':
					# Takes bloody ages!
					#self.send(ShutItSendSpec(self,send='emerge --sync',loglevel=loglevel,timeout=9999,ignore_background=True))
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
			issue_output = self.send_and_get_output(' command cat /etc/issue',
			                                        echo=False,
			                                        ignore_background=True,
			                                        loglevel=loglevel).lower()
			if not re.match('.*No such file.*',issue_output):
				for key in package_map.INSTALL_TYPE_MAP:
					if issue_output.find(key) != -1:
						distro       = key
						install_type = package_map.INSTALL_TYPE_MAP[key]
						break
			elif self.file_exists('/cygdrive'):
				distro       = 'cygwin'
				install_type = 'apt-cyg'
			if install_type == '' or distro == '':
				if self.file_exists('/etc/os-release'):
					os_name = self.send_and_get_output(' command cat /etc/os-release | grep ^NAME',
					                                   echo=False,
					                                   ignore_background=True,
					                                   loglevel=loglevel).lower()
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
				else:
					uname_output = self.send_and_get_output(" command uname -a | awk '{print $1}'",
					                                        echo=False,
					                                        ignore_background=True,
					                                        loglevel=loglevel)
					if uname_output == 'Darwin':
						distro = 'osx'
						install_type = 'brew'
						if not self.command_available('brew'):
							shutit.fail('ShutiIt requires brew be installed. See http://brew.sh for details on installation.') # pragma: no cover
						if not self.file_exists('/tmp/shutit_brew_list'):
							self.send(ShutItSendSpec(self,
							                         send='brew list > .shutit_brew_list',
							                         echo=False,
							                         ignore_background=True,
							                         loglevel=loglevel))
						for package in ('coreutils','findutils','gnu-tar','gnu-sed','gawk','gnutls','gnu-indent','gnu-getopt'):
							if self.send_and_get_output(' command cat .shutit_brew_list | grep -w ' + package,
							                            echo=False,
							                            loglevel=loglevel) == '':
								self.send(ShutItSendSpec(self,
								                         send='brew install ' + package,
								                         ignore_background=True,
								                         loglevel=loglevel))
						self.send(ShutItSendSpec(self,
						                         send='rm -f .shutit_brew_list',
						                         echo=False,
						                         ignore_background=True,
						                         loglevel=loglevel))
					if uname_output[:6] == 'CYGWIN':
						distro       = 'cygwin'
						install_type = 'apt-cyg'
				if install_type == '' or distro == '':
					shutit.fail('Could not determine Linux distro information. ' + 'Please inform ShutIt maintainers at https://github.com/ianmiell/shutit', shutit_pexpect_child=self.pexpect_child) # pragma: no cover
			# The call to self.package_installed with lsb-release above
			# may fail if it doesn't know the install type, so
			# if we've determined that now
			if install_type == 'apt' and shutit.build['delivery'] in ('docker','dockerfile'):
				if not self.command_available('lsb_release'):
					if not shutit.get_current_shutit_pexpect_session_environment().build['apt_update_done'] and self.whoami() == 'root':
						shutit.get_current_shutit_pexpect_session_environment().build['apt_update_done'] = True
						self.send(ShutItSendSpec(self,
						                         send='DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y -qq lsb-release',
						                         loglevel=loglevel,
						                         ignore_background=True))
					self.send(ShutItSendSpec(self,
					                         send='DEBIAN_FRONTEND=noninteractive apt-get install -y -qq lsb-release',
					                         loglevel=loglevel,
					                         ignore_background=True))
				d = self.lsb_release()
				install_type   = d['install_type']
				distro         = d['distro']
				distro_version = d['distro_version']
			elif install_type == 'yum' and shutit.build['delivery'] in ('docker','dockerfile'):
				if self.file_exists('/etc/redhat-release'):
					output = self.send_and_get_output(' command cat /etc/redhat-release',
					                                  echo=False,
					                                  loglevel=loglevel)
					if re.match('^centos.*$', output.lower()) or re.match('^red hat.*$', output.lower()) or re.match('^fedora.*$', output.lower()) or True:
						self.send_and_match_output('yum install -y -t redhat-lsb epel-release',
						                           'Complete!',
						                           loglevel=loglevel)
				else:
					if not self.command_available('lsb_release'):
						self.send(ShutItSendSpec(self,
						                         send='yum install -y lsb-release',
						                         ignore_background=True,
						                         loglevel=loglevel))
				d = self.lsb_release()
				install_type   = d['install_type']
				distro         = d['distro']
				distro_version = d['distro_version']
			elif install_type == 'apk' and shutit.build['delivery'] in ('docker','dockerfile'):
				if not shutit.get_current_shutit_pexpect_session_environment().build['apk_update_done'] and self.whoami() == 'root':
					self.send(ShutItSendSpec(self,
					                         send='apk -q update',
					                         ignore_background=True,
					                         loglevel=logging.INFO))
					shutit.get_current_shutit_pexpect_session_environment().build['apk_update_done'] = True
				self.send(ShutItSendSpec(self,
				                         send='apk -q add bash',
				                         ignore_background=True,
				                         loglevel=loglevel))
				install_type   = 'apk'
				distro         = 'alpine'
				distro_version = '1.0'
			elif install_type == 'emerge' and shutit.build['delivery'] in ('docker','dockerfile'):
				if not shutit.get_current_shutit_pexpect_session_environment().build['emerge_update_done'] and self.whoami() == 'root':
					# Takes bloody ages!
					#self.send(ShutItSendSpec(self,send='emerge --sync',loglevel=logging.INFO,ignore_background=True))
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



	def multisend(self, sendspec):
		"""Multisend. Same as send, except it takes multiple sends and expects in a dict that are
		processed while waiting for the end "expect" argument supplied.

		@param send:                 See send()
		@param send_dict:            See ShutItSendSpec
		@param expect:               See send()
		@param timeout:              See send()
		@param check_exit:           See send()
		@param fail_on_empty_before: See send()
		@param record_command:       See send()
		@param exit_values:          See send()
		@param escape:               See send()
		@param echo:                 See send()
		@param note:                 See send()
		@param secret:               See send()
		@param check_sudo:           See send()
		@param remove_on_match       See ShutItSendSpec
		@param loglevel:             See send()

		@return:                     The pexpect return value (ie which expected
		                             string in the list matched).
		                             If return is -1, the task was backgrounded. See also multisend.
		@rtype:                      int
		"""
		self.shutit.handle_note(sendspec.note)
		expect           = sendspec.expect or self.default_expect
		send_iteration   = sendspec.send
		expect_list      = list(sendspec.send_dict)
		# Put breakout item(s) in last.
		n_breakout_items = 0
		shutit_global.shutit_global_object.log('In multisend, send: ' + sendspec.send,level=logging.DEBUG)
		if isinstance(expect, str):
			shutit_global.shutit_global_object.log('Adding: "' + expect + '" to expect list.',level=logging.DEBUG)
			expect_list.append(expect)
			n_breakout_items = 1
		elif isinstance(expect, list):
			shutit_global.shutit_global_object.log('Adding: "' + str(expect) + '" to expect list.',level=logging.DEBUG)
			for item in expect:
				expect_list.append(item)
				n_breakout_items += 1
		shutit_global.shutit_global_object.log('Number of breakout items: ' + str(n_breakout_items),level=logging.DEBUG)
		while True:
			# If it's the last n items in the list, it's the breakout one.
			# Must be a separate sendspec object each time, must be run .
			res = self.send(ShutItSendSpec(self,
			                               send=send_iteration,
			                               expect=expect_list,
			                               check_exit=sendspec.check_exit,
			                               fail_on_empty_before=sendspec.fail_on_empty_before,
			                               timeout=sendspec.timeout,
			                               record_command=sendspec.record_command,
			                               exit_values=sendspec.exit_values,
			                               echo=self.shutit.get_echo_override(sendspec.echo),
			                               escape=sendspec.escape,
			                               secret=sendspec.secret,
			                               check_sudo=sendspec.check_sudo,
			                               nonewline=sendspec.nonewline,
			                               ignore_background=sendspec.ignore_background,
			                               run_in_background=False,
			                               block_other_commands=True,
							               loglevel=sendspec.loglevel))
			if res == -1:
				# Will be run in the background later.
				shutit_global.shutit_global_object.log('Multisend will be run in the background: ' + str(send_iteration),level=logging.INFO)
				return -1
			if res >= len(expect_list) - n_breakout_items:
				break
			else:
				#print(str(sendspec.send_dict))
				#print(str(expect_list))
				#print(expect_list[res])
				next_send     = sendspec.send_dict[expect_list[res]][0]
				remove_items  = sendspec.send_dict[expect_list[res]][1]
				send_iteration = next_send
				if sendspec.remove_on_match and remove_items:
					shutit_global.shutit_global_object.log('Have matched a password (' + expect_list[res] + '), removing password expects from list in readiness of a prompt',level=logging.DEBUG)
					if isinstance(expect, str):
						expect_list = [expect]
					elif isinstance(expect, list):
						expect_list = expect
		self.shutit.handle_note_after(note=sendspec.note)
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
		shutit = self.shutit
		echo = shutit.get_echo_override(echo)
		return self.send_until(send,
		                       regexps,
		                       not_there=not_there,
		                       cadence=0,
		                       retries=1,
		                       echo=echo,
		                       note=note,
		                       loglevel=loglevel)


	def send_until(self,
	               send,
	               regexps,
	               not_there=False,
	               cadence=2,
	               retries=100,
	               echo=None,
	               note=None,
	               debug_command=None,
	               pause_point_on_fail=True,
	               nonewline=False,
	               loglevel=logging.INFO):
		"""Send string on a regular cadence until a string is either seen, or the timeout is triggered.

		@param send:                 See send()
		@param regexps:              List of regexps to wait for.
		@param not_there:            If True, wait until this a regexp is not seen in the output. If False
		                             wait until a regexp is seen in the output (default)
		@param echo:                 See send()
		@param note:                 See send()
		"""
		shutit = self.shutit
		shutit.handle_note(note, command=send + ' \nuntil one of these seen:\n' + str(regexps))
		shutit_global.shutit_global_object.log('Sending: "' + send + '" until one of these regexps seen: ' + str(regexps),level=loglevel)
		if isinstance(regexps, str):
			regexps = [regexps]
		if not isinstance(regexps, list):
			shutit.fail('regexps should be list') # pragma: no cover
		while retries > 0:
			retries -= 1
			echo = shutit.get_echo_override(echo)
			output = self.send_and_get_output(send,
			                                  retry=1,
			                                  strip=True,
			                                  echo=echo,
			                                  loglevel=loglevel,
			                                  nonewline=nonewline,
			                                  fail_on_empty_before=False)
			shutit_global.shutit_global_object.log('Failed to match regexps -> ' + str(regexps) + ' <- retries left:' + str(retries),level=loglevel)
			if not not_there:
				for regexp in regexps:
					if not shutit_util.check_regexp(regexp):
						shutit.fail('Illegal regexp found in send_until call: ' + regexp) # pragma: no cover
					if shutit.match_string(output, regexp):
						return True
			else:
				# Only return if _not_ seen in the output
				missing = False
				for regexp in regexps:
					if not shutit_util.check_regexp(regexp):
						shutit.fail('Illegal regexp found in send_until call: ' + regexp) # pragma: no cover
					if not shutit.match_string(output, regexp):
						missing = True
						break
				if missing:
					shutit.handle_note_after(note=note)
					return True
			if debug_command is not None:
				self.send(ShutItSendSpec(self,
				                         send=debug_command,
				                         check_exit=False,
				                         echo=echo,
			                             nonewline=nonewline,
				                         loglevel=loglevel,
			                             ignore_background=True))
			time.sleep(cadence)
		shutit.handle_note_after(note=note)
		if pause_point_on_fail:
			shutit.pause_point('send_until failed sending: ' + send + '\r\nand expecting: ' + str(regexps))
		else:
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
		shutit = self.shutit
		shutit.handle_note(note)
		fexists = self.file_exists(fname)
		if not fexists:
			if create:
				self.send(ShutItSendSpec(self,
				                         send=' command touch ' + fname,
				                         echo=False,
				                         loglevel=loglevel,
				                         ignore_background=True))
			else:
				shutit.fail(fname + ' does not exist and create=False') # pragma: no cover
		if replace:
			# If replace and no pattern FAIL
			if not pattern:
				shutit.fail('replace=True requires a pattern to be passed in') # pragma: no cover
			# If replace and delete FAIL
			if delete:
				shutit.fail('cannot pass replace=True and delete=True to insert_text') # pragma: no cover
		# ftext is the original file's text. If base64 is available, use it to
		# encode the text
		if self.command_available('base64'):
			if PY3:
				ftext = bytes(self.send_and_get_output(' command base64 ' + fname,
				                                       echo=False,
				                                       loglevel=loglevel),
				                                       'utf-8')
			else:
				ftext = self.send_and_get_output(' command base64 ' + fname,
				                                 echo=False,
				                                 loglevel=loglevel)
			ftext = base64.b64decode(ftext)
		else:
			# Replace the file text's ^M-newlines with simple newlines
			if PY3:
				ftext = bytes(self.send_and_get_output(' command cat ' + fname,
				                                       echo=False,
				                                       loglevel=loglevel),
				                                       'utf-8')
				ftext = ftext.replace(bytes('\r\n', 'utf-8'),bytes('\n', 'utf-8'))
			else:
				ftext = self.send_and_get_output(' command cat ' + fname,
				                                 echo=False,
				                                 loglevel=loglevel)
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
						shutit.fail('Illegal regexp found in change_text call: ' + pattern) # pragma: no cover
					# cf: http://stackoverflow.com/questions/9411041/matching-ranges-of-lines-in-python-like-sed-ranges
					if PY3:
						sre_match = re.search(bytes(pattern,'utf-8'),ftext,re.DOTALL|re.MULTILINE)
					else:
						sre_match = re.search(pattern,ftext,re.DOTALL|re.MULTILINE)
					if replace:
						if sre_match is None:
							cut_point = len(ftext)
							newtext1 = ftext[:cut_point]
							newtext2 = ftext[cut_point:]
						else:
							cut_point = sre_match.start()
							cut_point_after = sre_match.end()
							newtext1 = ftext[:cut_point]
							newtext2 = ftext[cut_point_after:]
					else:
						if sre_match is None:
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
						shutit.fail('Illegal regexp found in change_text call: ' + pattern) # pragma: no cover
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
		self.send_file(fname,
		               new_text,
		               truncate=True,
		               loglevel=loglevel)
		shutit.handle_note_after(note=note)
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
		shutit = self.shutit
		shutit.handle_note(note)
		# assume we're going to add it
		tmp_filename = '/tmp/' + shutit_util.random_id()
		if self.file_exists(filename):
			if literal:
				if match_regexp is None:
					#            v the space is intentional, to avoid polluting bash history.
					self.send(ShutItSendSpec(self,
					                         send=""" grep -v '^""" + line + """$' """ + filename + ' > ' + tmp_filename,
					                         exit_values=['0','1'],
					                         echo=False,
					                         loglevel=loglevel,
					                         ignore_background=True))
				else:
					if not shutit_util.check_regexp(match_regexp):
						shutit.fail('Illegal regexp found in remove_line_from_file call: ' + match_regexp) # pragma: no cover
					#            v the space is intentional, to avoid polluting bash history.
					self.send(ShutItSendSpec(self,
					                         send=""" grep -v '^""" + match_regexp + """$' """ + filename + ' > ' + tmp_filename,
					                         exit_values=['0','1'],
					                         echo=False,
					                         loglevel=loglevel,
					                         ignore_background=True))
			else:
				if match_regexp is None:
					#          v the space is intentional, to avoid polluting bash history.
					self.send(ShutItSendSpec(self,
					                         send=' command grep -v "^' + line + '$" ' + filename + ' > ' + tmp_filename,
					                         exit_values=['0','1'],
					                         echo=False,
					                         loglevel=loglevel,
					                         ignore_background=True))
				else:
					if not shutit_util.check_regexp(match_regexp):
						shutit.fail('Illegal regexp found in remove_line_from_file call: ' + match_regexp) # pragma: no cover
					#          v the space is intentional, to avoid polluting bash history.
					self.send(ShutItSendSpec(self,
					                         send=' command grep -v "^' + match_regexp + '$" ' + filename + ' > ' + tmp_filename,
					                         exit_values=['0','1'],
					                         echo=False,
					                         loglevel=loglevel,
					                         ignore_background=True))
			self.send(ShutItSendSpec(self,
			                         send=' command cat ' + tmp_filename + ' > ' + filename,
			                         check_exit=False,
			                         echo=False,
			                         loglevel=loglevel,
					                 ignore_background=True))
			self.send(ShutItSendSpec(self,
			                         send=' command rm -f ' + tmp_filename,
			                         exit_values=['0','1'],
			                         echo=False,
			                         loglevel=loglevel,
					                 ignore_background=True))
		shutit.handle_note_after(note=note)
		return True



	def send(self, sendspec):
		"""Send string as a shell command, and wait until the expected output
		is seen (either a string or any from a list of strings) before
		returning. The expected string will default to the currently-set
		default expected string (see get_default_shutit_pexpect_session_expect)

		Returns the pexpect return value (ie which expected string in the list
		matched)

		@return:                     The pexpect return value (ie which expected
		                             string in the list matched).
		                             If return is -1, the task was backgrounded. See also multisend.
		@rtype:                      int
		"""
		shutit_global.shutit_global_object.log('In send, trying to send: ' + str(sendspec.send),level=logging.DEBUG)
		if self._check_blocked(sendspec):
			shutit_global.shutit_global_object.log('In send for ' + str(sendspec.send) + ', check_blocked called and returned True.',level=logging.INFO)
			# _check_blocked will add to the list of background tasks and handle dupes, so leave there.
			return -1
		shutit = self.shutit
		cfg = shutit.cfg
		# Set up what we expect.
		sendspec.expect = sendspec.expect or self.default_expect
		if sendspec.send.strip() == '':
			sendspec.fail_on_empty_before=False
			sendspec.check_exit=False
		if isinstance(sendspec.expect, dict):
			return self.multisend(ShutItSendSpec(self,
			                                     send=sendspec.send,
			                                     send_dict=sendspec.expect,
			                                     expect=shutit.get_default_shutit_pexpect_session_expect(),
			                                     timeout=sendspec.timeout,
			                                     check_exit=sendspec.check_exit,
			                                     fail_on_empty_before=sendspec.fail_on_empty_before,
			                                     record_command=sendspec.record_command,
			                                     exit_values=sendspec.exit_values,
			                                     echo=sendspec.echo,
			                                     note=sendspec.note,
			                                     secret=sendspec.secret,
			                                     check_sudo=sendspec.check_sudo,
			                                     nonewline=sendspec.nonewline,
			                                     loglevel=sendspec.loglevel))
		# Before gathering expect, detect whether this is a sudo command and act accordingly.
		command_list = sendspec.send.strip().split()
		# If there is a first command, there is a sudo in there (we ignore
		# whether it's quoted in the command), and we do not have sudo rights
		# cached...
		# TODO: check for sudo in pipelines, eg 'cmd | sudo' or 'cmd |sudo' but not 'echo " sudo "'
		if sendspec.check_sudo and len(command_list) > 0 and command_list[0] == 'sudo' and not self.check_sudo():
			sudo_pass = self.get_sudo_pass_if_needed(shutit)
			# Turn expect into a dict.
			return self.multisend(ShutItSendSpec(self,
			                                     send=sendspec.send,
			                                     send_dict={'assword':[sudo_pass,True]},
			                                     expect=shutit.get_default_shutit_pexpect_session_expect(),
			                                     timeout=sendspec.timeout,
			                                     check_exit=sendspec.check_exit,
			                                     fail_on_empty_before=sendspec.fail_on_empty_before,
			                                     record_command=sendspec.record_command,
			                                     exit_values=sendspec.exit_values,
			                                     echo=sendspec.echo,
			                                     note=sendspec.note,
			                                     check_sudo=False,
			                                     nonewline=sendspec.nonewline,
			                                     loglevel=sendspec.loglevel))

		shutit_global.shutit_global_object.log('Sending data in session: ' + self.pexpect_session_id,level=logging.DEBUG)
		shutit.handle_note(sendspec.note, command=str(sendspec.send), training_input=str(sendspec.send))
		if sendspec.timeout is None:
			sendspec.timeout = 3600

		sendspec.echo = shutit.get_echo_override(sendspec.echo)

		# Handle OSX to get the GNU version of the command
		if sendspec.assume_gnu:
			sendspec.send = shutit.get_send_command(sendspec.send)

		# If check_exit is not passed in
		# - if the expect matches the default, use the default check exit
		# - otherwise, default to doing the check
		if sendspec.check_exit is None:
			# If we are in video mode, ignore exit value
			if (shutit.build['video'] != -1 or shutit.build['video'] is True) or shutit.build['training'] or shutit.build['walkthrough'] or shutit.build['exam']:
				sendspec.check_exit = False
			elif sendspec.expect == shutit.get_default_shutit_pexpect_session_expect():
				sendspec.check_exit = shutit.get_default_shutit_pexpect_session_check_exit()
			else:
				# If expect given doesn't match the defaults and no argument
				# was passed in (ie check_exit was passed in as None), set
				# check_exit to true iff it matches a prompt.
				expect_matches_prompt = False
				for prompt in shutit.expect_prompts:
					if prompt == sendspec.expect:
						expect_matches_prompt = True
				if not expect_matches_prompt:
					sendspec.check_exit = False
				else:
					sendspec.check_exit = True

		# Determine whether we record this command.
		ok_to_record = False
		if not sendspec.echo and sendspec.record_command is None:
			sendspec.record_command = False
		if sendspec.record_command is None or sendspec.record_command:
			ok_to_record = True
			for i in cfg.keys():
				if isinstance(cfg[i], dict):
					for j in cfg[i].keys():
						if (j == 'password' or j == 'passphrase') and cfg[i][j] == sendspec.send:
							shutit.build['shutit_command_history'].append ('#redacted command, password')
							ok_to_record = False
							break
				if not ok_to_record or sendspec.send in shutit_global.shutit_global_object.secret_words_set:
					sendspec.secret = True
					break
			if ok_to_record:
				shutit.build['shutit_command_history'].append(sendspec.send)

		# Log - tho not if secret.
		if sendspec.send != None:
			if not sendspec.echo and not sendspec.secret:
				shutit_global.shutit_global_object.log('Sending: ' + sendspec.send,level=sendspec.loglevel)
			elif not sendspec.echo and sendspec.secret:
				shutit_global.shutit_global_object.log('Sending: [SECRET]',level=sendspec.loglevel)
			shutit_global.shutit_global_object.log('================================================================================',level=logging.DEBUG)
			if not sendspec.secret:
				shutit_global.shutit_global_object.log('Sending>>>' + sendspec.send + '<<<',level=logging.DEBUG)
			else:
				shutit_global.shutit_global_object.log('Sending>>>[SECRET]<<<',level=logging.DEBUG)
			shutit_global.shutit_global_object.log('Expecting>>>' + str(sendspec.expect) + '<<<',level=logging.DEBUG)

		while sendspec.retry > 0:
			if sendspec.escape:
				escaped_str = "eval $'"
				_count = 7
				for char in sendspec.send:
					if char in string.ascii_letters:
						escaped_str += char
						_count += 1
					else:
						escaped_str += shutit_util.get_wide_hex(char)
						_count += 4
					if _count > shutit_global.shutit_global_object.line_limit:
						# The newline here is deliberate!
						escaped_str += r"""'\
$'"""
						_count = 0
				escaped_str += "'"
				if not sendspec.secret:
					shutit_global.shutit_global_object.log('This string was sent safely: ' + sendspec.send, level=logging.DEBUG)
				else:
					shutit_global.shutit_global_object.log('The string was sent safely.', level=logging.DEBUG)
				string_to_send = escaped_str
			else:
				string_to_send = sendspec.send
			if string_to_send is not None:
				if len(string_to_send) > shutit_global.shutit_global_object.line_limit:
					fname = self._create_command_file(sendspec.expect,string_to_send)
					res = self.send(ShutItSendSpec(self,
					                               send=' command source ' + fname,
					                               expect=sendspec.expect,
					                               timeout=sendspec.timeout,
					                               check_exit=sendspec.check_exit,
					                               fail_on_empty_before=False,
					                               record_command=False,
					                               exit_values=sendspec.exit_values,
					                               echo=False,
					                               escape=False,
					                               retry=sendspec.retry,
					                               loglevel=sendspec.loglevel,
					                               follow_on_commands=sendspec.follow_on_commands,
					                               delaybeforesend=sendspec.delaybeforesend,
			                                       nonewline=sendspec.nonewline,
			                                       run_in_background=sendspec.run_in_background,
					                               ignore_background=True,
			                                       block_other_commands=sendspec.block_other_commands))
					if not self.sendline(ShutItSendSpec(self,
					                                    send=' rm -f ' + fname,
					                                    nonewline=sendspec.nonewline,
			                                            run_in_background=sendspec.run_in_background,
					                                    echo=False,
					                                    ignore_background=True)):
						self.expect(sendspec.expect,
						            searchwindowsize=sendspec.searchwindowsize,
						            maxread=sendspec.maxread)
					return res
				else:
					if sendspec.echo:
						shutit.divert_output(sys.stdout)
					if not self.sendline(sendspec):
						expect_res = shutit.expect_allow_interrupt(self.pexpect_child, sendspec.expect, sendspec.timeout)
					else:
						expect_res = -1
					if sendspec.echo:
						shutit.divert_output(None)
			else:
				expect_res = shutit.expect_allow_interrupt(self.pexpect_child, sendspec.expect, sendspec.timeout)
			if isinstance(self.pexpect_child.after, type) or isinstance(self.pexpect_child.before, type):
				shutit_global.shutit_global_object.log('End of pexpect session detected, bailing.',level=logging.CRITICAL)
				shutit_global.shutit_global_object.handle_exit(exit_code=1)
			# Massage the output for summary sending.
			logged_output = ''.join((self.pexpect_child.before + str(self.pexpect_child.after)).split('\n')).replace(sendspec.send,'',1).replace('\r','')[:160] + ' [...]'
			if not sendspec.secret:
				if not sendspec.echo:
					shutit_global.shutit_global_object.log('Output (squashed): ' + logged_output,level=sendspec.loglevel)
				try:
					shutit_global.shutit_global_object.log('shutit_pexpect_child.buffer(hex)>>>\n'  + binascii.hexlify(self.pexpect_child.buffer) + '\n<<<',level=logging.DEBUG)
					shutit_global.shutit_global_object.log('shutit_pexpect_child.before (hex)>>>\n' + binascii.hexlify(self.pexpect_child.before) + '\n<<<',level=logging.DEBUG)
					shutit_global.shutit_global_object.log('shutit_pexpect_child.after (hex)>>>\n'  + binascii.hexlify(self.pexpect_child.after) + '\n<<<',level=logging.DEBUG)
				except TypeError as e:
					shutit_global.shutit_global_object.log('Exception at 2665: ' + str(e),level=logging.WARNING)
				shutit_global.shutit_global_object.log('shutit_pexpect_child.buffer>>>\n' + str(self.pexpect_child.buffer) + '\n<<<',level=logging.DEBUG)
				shutit_global.shutit_global_object.log('shutit_pexpect_child.before>>>\n' + str(self.pexpect_child.before) + '\n<<<',level=logging.DEBUG)
				shutit_global.shutit_global_object.log('shutit_pexpect_child.after>>>\n' + str(self.pexpect_child.after) + '\n<<<',level=logging.DEBUG)
			else:
				shutit_global.shutit_global_object.log('[Send was marked secret; getting output debug will require code change]',level=logging.DEBUG)
			if sendspec.fail_on_empty_before:
				if self.pexpect_child.before.strip() == '':
					shutit.fail('before empty after sending: ' + str(sendspec.send) + '\n\nThis is expected after some commands that take a password.\nIf so, add fail_on_empty_before=False to the send call.\n\nIf that is not the problem, did you send an empty string to a prompt by mistake?', shutit_pexpect_child=self.pexpect_child) # pragma: no cover
			else:
				# Don't check exit if fail_on_empty_before is False
				sendspec.check_exit = False
				for prompt in shutit.expect_prompts:
					if prompt == sendspec.expect:
						# Reset prompt
						self.setup_prompt('reset_tmp_prompt')
						self.revert_prompt('reset_tmp_prompt', sendspec.expect)
						break
			# Last output - remove the first line, as it is the previous command.
			# Get this before we check exit.
			last_output = '\n'.join(self.pexpect_child.before.split('\n')[1:])
			if sendspec.check_exit:
				# store the output
				if not self.check_last_exit_values(sendspec.send,
				                                   expect=sendspec.expect,
				                                   exit_values=sendspec.exit_values,
				                                   retry=sendspec.retry):
					if not sendspec.secret:
						shutit_global.shutit_global_object.log('Sending: ' + sendspec.send + ' : failed, retrying', level=logging.DEBUG)
					else:
						shutit_global.shutit_global_object.log('Send failed, retrying', level=logging.DEBUG)
					sendspec.retry -= 1
					assert sendspec.retry > 0
					continue
			break
		# check self.pexpect_child.before for matches for follow-on commands
		if sendspec.follow_on_commands is not None:
			for match in sendspec.follow_on_commands:
				sendspec.send = sendspec.follow_on_commands[match]
				if shutit.match_string(last_output, match):
					# send (with no follow-on commands)
					self.send(ShutItSendSpec(self,
					                         send=sendspec.send,
					                         expect=sendspec.expect,
					                         timeout=sendspec.timeout,
					                         check_exit=sendspec.check_exit,
					                         fail_on_empty_before=False,
					                         record_command=sendspec.record_command,
					                         exit_values=sendspec.exit_values,
					                         echo=sendspec.echo,
					                         escape=sendspec.escape,
					                         retry=sendspec.retry,
					                         loglevel=sendspec.loglevel,
					                         delaybeforesend=sendspec.delaybeforesend,
			                                 run_in_background=False,
					                         ignore_background=True,
			                                 block_other_commands=sendspec.block_other_commands))
		if shutit.build['step_through']:
			self.pause_point('pause point: stepping through')
		if shutit.build['ctrlc_stop']:
			shutit.build['ctrlc_stop'] = False
			self.pause_point('pause point: interrupted by CTRL-c')
		shutit.handle_note_after(note=sendspec.note, training_input=str(sendspec.send))
		return expect_res
	# alias send to send_and_expect
	send_and_expect = send


	def quick_send(self, send, loglevel=logging.INFO):
		"""Quick and dirty send that ignores background tasks. Intended for internal use.
		"""
		shutit_global.shutit_global_object.log('Quick send: ' + send, level=loglevel)
		res = self.sendline(ShutItSendSpec(self,
		                                    send=send,
		                                    check_exit=False,
		                                    fail_on_empty_before=False,
		                                    record_command=False,
		                                    ignore_background=True))
		if not res:
			self.expect(self.default_expect)


	def send_file(self,
	              path,
	              contents,
	              echo=False,
	              truncate=False,
	              note=None,
	              user=None,
	              group=None,
	              loglevel=logging.INFO,
	              encoding=None):
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
		shutit = self.shutit
		shutit.handle_note(note, 'Sending contents to path: ' + path)
		# make more efficient by only looking at first 10000 chars, stop when we get to 30 chars rather than reading whole file.
		if PY3:
			split_contents = ''.join((str(contents[:10000]).split()))
		else:
			split_contents = ''.join((contents[:10000].split()))
		strings_from_file = re.findall("[^\x00-\x1F\x7F-\xFF]", split_contents)
		shutit_global.shutit_global_object.log('Sending file contents beginning: "' + ''.join(strings_from_file)[:30] + ' [...]" to file: ' + path, level=loglevel)
		if user is None:
			user = self.whoami()
		if group is None:
			group = self.whoarewe()
		if self.current_environment.environment_id == 'ORIGIN_ENV' and False:
			# If we're on the root env (ie the same one that python is running on, then use python.
			if isinstance(contents, str):
				f = open(path,'w')
				if truncate:
					f.truncate(0)
				try:
					f.write(contents)
				except (UnicodeDecodeError, TypeError) as e:
					shutit_global.shutit_global_object.log('Error decoding: ' + str(e), level=logging.DEBUG)
					if encoding is not None:
						f.write(contents.decode(encoding))
					else:
						f.write(contents.decode('utf-8'))
			elif isinstance(contents, bytes):
				f = open(path,'w')
				if truncate:
					f.truncate(0)
				try:
					f.write(contents)
				except (UnicodeDecodeError, TypeError) as e:
					if encoding is not None:
						f.write(contents.decode(encoding))
					else:
						f.write(contents.decode('utf-8'))
			else:
				shutit.fail('type: ' + str(type(contents)) + ' not handled in 1') # pragma: no cover
			f.close()
		elif shutit.build['delivery'] in ('bash','dockerfile'):
			if truncate and self.file_exists(path):
				self.send(ShutItSendSpec(self,
				                         send=' command rm -f ' + path,
				                         echo=echo,
				                         loglevel=loglevel,
				                         ignore_background=True))
			random_id = shutit_util.random_id()
			# set the searchwindowsize to a low number to speed up processing of large output
			if PY3:
				if encoding is not None:
					b64contents = base64.b64encode(contents.encode(encoding)).decode(encoding)
				else:
					if isinstance(contents, str):
						b64contents = base64.b64encode(contents.encode('utf-8')).decode('utf-8')
					elif isinstance(contents, bytes):
						b64contents = base64.b64encode(contents).decode('utf-8')
					else:
						shutit.fail('type: ' + str(type(contents)) + ' not handled in 2') # pragma: no cover
			else:
				b64contents = base64.b64encode(contents)
			if len(b64contents) > 100000:
				shutit_global.shutit_global_object.log('File is larger than ~100K - this may take some time',level=logging.WARNING)
			self.send(ShutItSendSpec(self,
			                         send=' ' + shutit.get_command('head') + ' -c -1 > ' + path + "." + random_id + " << 'END_" + random_id + """'\n""" + b64contents + '''\nEND_''' + random_id,
			                         echo=echo,
			                         loglevel=loglevel,
			                         timeout=99999,
			                         ignore_background=True))
			self.send(ShutItSendSpec(self,
			                         send=' command cat ' + path + '.' + random_id + ' | base64 --decode > ' + path,
			                         echo=echo,
			                         loglevel=loglevel,
			                         ignore_background=True))
			# Remove the file
			self.send(ShutItSendSpec(self,
			                         send=' command rm -f ' + path + '.' + random_id,
			                         loglevel=loglevel,
			                         ignore_background=True))
		else:
			host_child = shutit.get_shutit_pexpect_session_from_id('host_child').pexpect_child
			path = path.replace(' ', r'\ ')
			# get host session
			tmpfile = shutit_global.shutit_global_object.shutit_state_dir + 'tmp_' + shutit_util.random_id()
			f = open(tmpfile,'wb')
			f.truncate(0)
			# TODO: try taking out trys
			if isinstance(contents, bytes):
				try:
					if PY3:
						f.write(contents)
					elif encoding is not None:
						f.write(contents.encode(encoding))
					else:
						f.write(contents.encode('utf-8'))
				except (UnicodeDecodeError, TypeError) as e:
					f.write(contents)
			else:
				# We assume it's unicode, or str. Can't be explicit because python3 and 2 differ in how they handle...
				try:
					if encoding is not None:
						f.write(contents.encode(encoding))
					else:
						f.write(contents.encode('utf-8'))
				except (UnicodeDecodeError, TypeError) as e:
					f.write(contents)
			f.close()
			# Create file so it has appropriate permissions
			self.send(ShutItSendSpec(self,
			                         send=' command touch ' + path,
			                         loglevel=loglevel,
			                         echo=echo,
			                         ignore_background=True))
			# If path is not absolute, add $HOME to it.
			if path[0] != '/':
				shutit.send(' command cat ' + tmpfile + ' | ' + shutit.host['docker_executable'] + ' exec -i ' + shutit.target['container_id'] + " bash -c 'cat > $HOME/" + path + "'",
				            shutit_pexpect_child=host_child,
				            expect=shutit.expect_prompts['ORIGIN_ENV'],
				            loglevel=loglevel,
				            echo=echo)
			else:
				shutit.send(' command cat ' + tmpfile + ' | ' + shutit.host['docker_executable'] + ' exec -i ' + shutit.target['container_id'] + " bash -c 'cat > " + path + "'",
				            shutit_pexpect_child=host_child,
				            expect=shutit.expect_prompts['ORIGIN_ENV'],
				            loglevel=loglevel,
				            echo=echo)
			self.send(ShutItSendSpec(self,
			                         send=' command chown ' + user + ' ' + path + ' && chgrp ' + group + ' ' + path,
			                         echo=echo,
			                         loglevel=loglevel,
			                         ignore_background=True))
			os.remove(tmpfile)
		shutit.handle_note_after(note=note)
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
		shutit = self.shutit
		shutit.handle_note(note, 'Script: ' + str(script))
		shutit_global.shutit_global_object.log('Running script beginning: "' + ''.join(script.split())[:30] + ' [...]', level=logging.INFO)
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
		self.quick_send('command mkdir -p ' + shutit_global.shutit_global_object.shutit_state_dir + '/scripts && chmod 777 ' + shutit_global.shutit_global_object.shutit_state_dir + '/scripts')
		self.send_file(shutit_global.shutit_global_object.shutit_state_dir + '/scripts/shutit_script.sh',
		               script,
		               loglevel=loglevel)
		self.quick_send('command chmod +x ' + shutit_global.shutit_global_object.shutit_state_dir + '/scripts/shutit_script.sh')
		shutit.build['shutit_command_history'].append('    ' + script.replace('\n', '\n    '))
		if in_shell:
			ret = self.send(ShutItSendSpec(self,
			                               send=' . ' + shutit_global.shutit_global_object.shutit_state_dir + '/scripts/shutit_script.sh && rm -f ' + shutit_global.shutit_global_object.shutit_state_dir + '/scripts/shutit_script.sh && rm -f ' + shutit_global.shutit_global_object.shutit_state_dir + '/scripts/shutit_script.sh',
			                               echo=False,
			                               loglevel=loglevel))
		else:
			ret = self.send(ShutItSendSpec(self,
			                               send=' ' + shutit_global.shutit_global_object.shutit_state_dir + '/scripts/shutit_script.sh && rm -f ' + shutit_global.shutit_global_object.shutit_state_dir + '/scripts/shutit_script.sh',
			                               echo=False,
			                               loglevel=loglevel))
		shutit.handle_note_after(note=note)
		return ret



	def challenge(self,
	              shutit,
	              task_desc,
	              expect=None,
	              hints=None,
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
	              follow_on_context=None,
	              difficulty=1.0,
	              reduction_per_minute=0.2,
	              reduction_per_reset=0,
	              reduction_per_hint=0.5,
	              grace_period=30,
	              new_stage=True,
	              final_stage=False,
	              num_stages=None):
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
		shutit = self.shutit
		signal_id = shutit_global.shutit_global_object.signal_id
		if new_stage and shutit.build['exam_object']:
			if num_stages is None:
				num_stages = shutit.build['exam_object'].num_stages
			elif shutit.build['exam_object'].num_stages < 1:
				shutit.build['exam_object'].num_stages = num_stages
			elif shutit.build['exam_object'].num_stages > 0:
				shutit.fail('Error! num_stages passed in should be None if already set in exam object (ie > 0)') # pragma: no cover
			curr_stage = str(shutit.build['exam_object'].curr_stage)
			if num_stages > 0:
				task_desc = 80*'*' + '\n' + '* QUESTION ' + str(curr_stage) + '/' + str(num_stages) + '\n' + 80*'*' + '\n' + task_desc
			else:
				task_desc = 80*'*' + '\n' + '* QUESTION \n' + 80*'*' + '\n' + task_desc
			shutit.build['exam_object'].new_stage(difficulty=difficulty,
			                                      reduction_per_minute=reduction_per_minute,
			                                      reduction_per_reset=reduction_per_reset,
			                                      reduction_per_hint=reduction_per_hint,
			                                      grace_period=grace_period)
			# If this is an exam, then remove history.
			self.send(ShutItSendSpec(self,
			                         send=' history -c',
			                         check_exit=False,
			                         ignore_background=True))
		# don't catch CTRL-C, pass it through.
		shutit.build['ctrlc_passthrough'] = True
		preserve_newline                  = False
		skipped                           = False
		if expect_type == 'regexp':
			if isinstance(expect, str):
				expect = [expect]
			if not isinstance(expect, list):
				shutit.fail('expect_regexps should be list') # pragma: no cover
		elif expect_type == 'md5sum':
			preserve_newline = True
		elif expect_type == 'exact':
			pass
		else:
			shutit.fail('Must pass either expect_regexps or md5sum in') # pragma: no cover
		if hints is not None and len(hints):
			shutit.build['pause_point_hints'] = hints
		else:
			shutit.build['pause_point_hints'] = []
		if challenge_type == 'command':
			help_text = shutit_util.colourise('32','''\nType 'help' or 'h' to get a hint, 'exit' to skip, 'shutitreset' to reset state.''')
			ok = False
			while not ok:
				shutit_global.shutit_global_object.log(shutit_util.colourise('32','''\nChallenge!'''),transient=True)
				if hints is not None and len(hints):
					shutit_global.shutit_global_object.log(shutit_util.colourise('32',help_text),transient=True)
				time.sleep(pause)
				# TODO: bash path completion
				send = shutit_util.get_input(task_desc + ' => ',colour='31')
				if not send or send.strip() == '':
					continue
				if send in ('help','h'):
					if hints is not None and len(hints):
						shutit_global.shutit_global_object.log(help_text,transient=True,level=logging.CRITICAL)
						shutit_global.shutit_global_object.log(shutit_util.colourise('32',hints.pop()),transient=True,level=logging.CRITICAL)
					else:
						shutit_global.shutit_global_object.log(help_text,transient=True,level=logging.CRITICAL)
						shutit_global.shutit_global_object.log(shutit_util.colourise('32','No hints left, sorry! CTRL-g to reset state, CTRL-s to skip this step, CTRL-] to submit for checking'),transient=True,level=logging.CRITICAL)
					time.sleep(pause)
					continue
				if send == 'shutitreset':
					self._challenge_done(shutit, result='reset',follow_on_context=follow_on_context,final_stage=False)
					continue
				if send == 'shutitquit':
					self._challenge_done(shutit, result='reset',follow_on_context=follow_on_context,final_stage=True)
					shutit_global.shutit_global_object.handle_exit(exit_code=1)
				if send == 'exit':
					self._challenge_done(shutit, result='exited',follow_on_context=follow_on_context,final_stage=True)
					shutit.build['pause_point_hints'] = []
					return True
				output = self.send_and_get_output(send,
				                                  timeout=timeout,
				                                  retry=1,
				                                  record_command=record_command,
				                                  echo=echo,
				                                  loglevel=loglevel,
				                                  fail_on_empty_before=False,
				                                  preserve_newline=preserve_newline)
				md5sum_output = md5(output).hexdigest()
				shutit_global.shutit_global_object.log('output: ' + output + ' is md5sum: ' + md5sum_output,level=logging.DEBUG)
				if expect_type == 'md5sum':
					output = md5sum_output
					if output == expect:
						ok = True
				elif expect_type == 'exact':
					if output == expect:
						ok = True
				elif expect_type == 'regexp':
					for regexp in expect:
						if shutit.match_string(output, regexp):
							ok = True
							break
				if not ok and failed:
					if shutit.build['exam_object']:
						shutit.build['exam_object'].add_fail()
						shutit.build['exam_object'].end_timer()
					shutit_global.shutit_global_object.log('\n\n' + shutit_util.colourise('32','failed') + '\n',transient=True,level=logging.CRITICAL)
					self._challenge_done(shutit, result='failed',final_stage=final_stage)
					continue
		elif challenge_type == 'golf':
			# pause, and when done, it checks your working based on check_command.
			ok = False
			# hints
			if hints is not None and len(hints):
				task_desc_new = task_desc + '\r\n\r\nHit CTRL-h for help, CTRL-g to reset state, CTRL-s to skip, CTRL-] to submit for checking'
			else:
				task_desc_new = '\r\n' + task_desc
			while not ok:
				if shutit.build['exam_object'] and new_stage:
					shutit.build['exam_object'].start_timer()
					# Set the new_stage to False, as we're in a loop that doesn't need to mark a new state.
					new_stage = False
				self.pause_point(shutit_util.colourise('31',task_desc_new),colour='31')
				if signal_id == 8:
					if shutit.build['exam_object']:
						shutit.build['exam_object'].add_hint()
					if len(shutit.build['pause_point_hints']):
						shutit_global.shutit_global_object.log(shutit_util.colourise('31','\r\n========= HINT ==========\r\n\r\n' + shutit.build['pause_point_hints'].pop(0)),transient=True,level=logging.CRITICAL)
					else:
						shutit_global.shutit_global_object.log(shutit_util.colourise('31','\r\n\r\n' + 'No hints available!'),transient=True,level=logging.CRITICAL)
					time.sleep(1)
					# clear the signal
					signal_id = 0
					continue
				elif signal_id == 17:
					# clear the signal and ignore CTRL-q
					signal_id = 0
					continue
				elif signal_id == 7:
					if shutit.build['exam_object']:
						shutit.build['exam_object'].add_reset()
					shutit_global.shutit_global_object.log(shutit_util.colourise('31','\r\n========= RESETTING STATE ==========\r\n\r\n'),transient=True,level=logging.CRITICAL)
					self._challenge_done(shutit, result='reset', follow_on_context=follow_on_context,final_stage=False)
					# clear the signal
					signal_id = 0
					# Get the new target child, which is the new 'self'
					target_child = shutit.get_shutit_pexpect_session_from_id('target_child')
					return target_child.challenge(
						shutit,
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
				elif signal_id == 19:
					if shutit.build['exam_object']:
						shutit.build['exam_object'].add_skip()
						shutit.build['exam_object'].end_timer()
					# Clear the signal.
					signal_id = 0
					# Skip test.
					shutit_global.shutit_global_object.log('\r\nTest skipped... please wait',level=logging.CRITICAL,transient=True)
					skipped=True
					self._challenge_done(shutit, result='skipped',follow_on_context=follow_on_context,skipped=True,final_stage=final_stage)
					return True
				shutit_global.shutit_global_object.log('\r\nState submitted, checking your work...',level=logging.CRITICAL,transient=True)
				check_command = follow_on_context.get('check_command')
				output = self.send_and_get_output(check_command,
				                                  timeout=timeout,
				                                  retry=1,
				                                  record_command=record_command,
				                                  echo=False,
				                                  loglevel=loglevel,
				                                  fail_on_empty_before=False,
				                                  preserve_newline=preserve_newline)
				shutit_global.shutit_global_object.log('output: ' + output,level=logging.DEBUG)
				md5sum_output = md5(output).hexdigest()
				if expect_type == 'md5sum':
					shutit_global.shutit_global_object.log('output: ' + output + ' is md5sum: ' + md5sum_output,level=logging.DEBUG)
					output = md5sum_output
					if output == expect:
						ok = True
				elif expect_type == 'exact':
					if output == expect:
						ok = True
				elif expect_type == 'regexp':
					for regexp in expect:
						if shutit.match_string(output,regexp):
							ok = True
							break
				if not ok and failed:
					shutit_global.shutit_global_object.log('\r\n\n' + shutit_util.colourise('31','Failed! CTRL-g to reset state, CTRL-h for a hint, CTRL-] to submit for checking') + '\n',transient=True,level=logging.CRITICAL)
					# No second chances if exam!
					if shutit.build['exam_object']:
						shutit.build['exam_object'].add_fail()
						shutit.build['exam_object'].end_timer()
						self._challenge_done(shutit, result='failed_test',follow_on_context=follow_on_context,final_stage=final_stage)
						return False
					else:
						continue
		else:
			shutit.fail('Challenge type: ' + challenge_type + ' not supported') # pragma: no cover
		self._challenge_done(shutit,
		                     result='ok',
		                     follow_on_context=follow_on_context,
		                     congratulations=congratulations,
		                     skipped=skipped,
		                     final_stage=final_stage)
		if shutit.build['exam_object']:
			shutit.build['exam_object'].add_ok()
			shutit.build['exam_object'].end_timer()
		# Tidy up hints
		shutit.build['pause_point_hints'] = []
		return True


	def init_pexpect_session_environment(self, prefix):
		shutit = self.shutit
		environment_id_dir = shutit_global.shutit_global_object.shutit_state_dir + '/environment_id'
		#print('=================================================================================')
		#print('environment_id_dir')
		if self.file_exists(environment_id_dir,directory=True):
			files = self.ls(environment_id_dir)
			if len(files) != 1 or not isinstance(files, list):
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
								shutit.fail('Should not get here: environment reached but with unique build_id that matches ' + environment_id_dir + ', but object not in existence') # pragma: no cover
				else:
					## See comment above re: cygwin.
					if self.file_exists('/cygdrive'):
						self.current_environment = shutit.get_shutit_pexpect_session_environment('ORIGIN_ENV')
					else:
						shutit.fail('Wrong number of files in environment_id_dir: ' + environment_id_dir) # pragma: no cover
					shutit.fail('Wrong number of files in environment_id_dir: ' + environment_id_dir) # pragma: no cover
			else:
				environment_id = files[0]
				environment = shutit.get_shutit_pexpect_session_environment(environment_id)
				if environment:
					# Set that object to the _current_ environment in the PexpectSession
					# OBJECT TO _CURRENT_ ENVIRONMENT IN SHUTIT PEXPECT session OBJECT AND RETURN that object.
					self.current_environment = environment
				else:
					shutit.fail('Should not get here: environment reached but with unique build_id that matches ' + environment_id_dir + ', but object not in existence, ' + environment_id) # pragma: no cover
			self.current_environment = environment
			return shutit.get_shutit_pexpect_session_environment(environment_id)
		# At this point we have determined it is a 'new' environment. So create a new ShutItPexpectSessionEnvironment identified by the prefix.
		new_environment = ShutItPexpectSessionEnvironment(prefix)
		# If not, create new env object, set it to current.
		self.current_environment = new_environment
		add_shutit_pexpect_session_environment(new_environment)
		self.get_distro_info()
		self.send(ShutItSendSpec(self,
		                         send=' command mkdir -p ' + environment_id_dir + ' && ( chmod -R 777 ' + shutit_global.shutit_global_object.shutit_state_dir + ' || /bin/true ) && touch ' + environment_id_dir + '/' + new_environment.environment_id,
		                         echo=False,
		                         loglevel=logging.DEBUG,
		                         ignore_background=True))
		return new_environment


	# Determines whether we have sudo available, and whether we already have sudo rights cached.
	def check_sudo(self):
		if self.command_available('sudo'):
			self.send(ShutItSendSpec(self,
			                         send=' sudo -n echo',
			                         check_exit=False,
			                         check_sudo=False,
			                         ignore_background=True))
			if self.send_and_get_output(' echo $?') == '0':
				shutit_global.shutit_global_object.log('check_sudo returning True',level=logging.DEBUG)
				return True
		shutit_global.shutit_global_object.log('check_sudo returning False',level=logging.DEBUG)
		return False


	# Created specifically to help when logging in and the prompt is not ready.
	def get_exit_value(self):
		# The quotes in the middle of the string are there to prevent the output matching the command.
		self.pexpect_child.send(''' if [ $? = 0 ]; then echo 'SHUTIT''_RESULT:0'; else echo 'SHUTIT''_RESULT:1'; fi\n''')
		shutit_global.shutit_global_object.log('Checking exit value.',level=logging.DEBUG)
		success_check = self.pexpect_child.expect(['SHUTIT_RESULT:0','SHUTIT_RESULT:1'])
		if success_check == 0:
			shutit_global.shutit_global_object.log('Returning true.',level=logging.DEBUG)
			return True
		elif success_check == 1:
			shutit_global.shutit_global_object.log('Returning false.',level=logging.DEBUG)
			return False


	def get_sudo_pass_if_needed(self, shutit, ignore_brew=False):
		pw = ''
		whoiam = self.whoami()
		# Cygwin does not have root
		if self.current_environment.distro == 'cygwin':
			return
		if whoiam != 'root':
			if ignore_brew and self.current_environment.install_type == 'brew':
				shutit_global.shutit_global_object.log('brew installation environment, and ignor_brew set, returning',logging.DEBUG)
			else:
				if not self.command_available('sudo'):
					shutit.pause_point('Please install sudo and then continue with CTRL-]',shutit_pexpect_child=self.pexpect_child)
				if not self.check_sudo():
					pw = self.get_env_pass(whoiam,'Please input your sudo password in case it is needed (for user: ' + whoiam + ')\nJust hit return if you do not want to submit a password.\n')
		if isinstance(pw,str):
			shutit_global.shutit_global_object.secret_words_set.add(pw)
		return pw


	# Internal functions
	def _create_command_file(self, expect, send):
		"""Internal function. Do not use.

		Takes a long command, and puts it in an executable file ready to run. Returns the filename.
		"""
		shutit = self.shutit
		random_id = shutit_util.random_id()
		fname = shutit_global.shutit_global_object.shutit_state_dir + '/tmp_' + random_id
		working_str = send
		# truncate -s must be used as --size is not supported everywhere (eg busybox)
		assert not self.sendline(ShutItSendSpec(self,
		                                        send=' truncate -s 0 '+ fname,
		                                        ignore_background=True))
		self.pexpect_child.expect(expect)
		size = shutit_global.shutit_global_object.line_limit
		while len(working_str) > 0:
			curr_str = working_str[:size]
			working_str = working_str[size:]
			assert not self.sendline(ShutItSendSpec(self,
			                                        send=' ' + shutit.get_command('head') + ''' -c -1 >> ''' + fname + """ << 'END_""" + random_id + """'\n""" + curr_str + """\nEND_""" + random_id,
		                                            ignore_background=True))
			self.expect(expect)
		assert not self.sendline(ShutItSendSpec(self,
		                                        send=' chmod +x ' + fname,
		                                        ignore_background=True))
		self.expect(expect)
		return fname


	def _challenge_done(self,
	                    shutit,
	                    result=None,
	                    congratulations=None,
	                    follow_on_context=None,
	                    pause=1,
	                    skipped=False,
	                    final_stage=False):
		if result == 'ok' or result == 'failed_test' or result == 'skipped':
			shutit.build['ctrlc_passthrough'] = False
			if congratulations and result == 'ok':
				shutit_global.shutit_global_object.log('\n\n' + shutit_util.colourise('32',congratulations) + '\n',transient=True)
			time.sleep(pause)
			if follow_on_context is not None:
				if follow_on_context.get('context') == 'docker':
					container_name = follow_on_context.get('ok_container_name')
					if not container_name:
						shutit_global.shutit_global_object.log('No reset context available, carrying on.',level=logging.INFO)
					elif skipped or result == 'failed_test':
						# We need to ensure the correct state.
						self.replace_container(container_name,go_home=False)
						shutit_global.shutit_global_object.log('State restored.',level=logging.INFO)
					elif final_stage:
						shutit_global.shutit_global_object.log(shutit_util.colourise('31','Finished! Please wait...'),transient=True)
					else:
						shutit_global.shutit_global_object.log(shutit_util.colourise('31','Continuing, remember you can restore to a known state with CTRL-g.'),transient=True)
				else:
					shutit.fail('Follow-on context not handled on pass') # pragma: no cover
			return True
		elif result == 'exited':
			shutit.build['ctrlc_passthrough'] = False
			return
		elif result == 'failed':
			time.sleep(1)
			return False
		elif result == 'reset':
			if follow_on_context is not None:
				if follow_on_context.get('context') == 'docker':
					container_name = follow_on_context.get('reset_container_name')
					if not container_name:
						shutit_global.shutit_global_object.log('No reset context available, carrying on.',level=logging.DEBUG)
					else:
						self.replace_container(container_name,go_home=False)
						shutit_global.shutit_global_object.log('State restored.',level=logging.INFO)
				else:
					shutit.fail('Follow-on context not handled on reset') # pragma: no cover
			return True
		else:
			shutit.fail('result: ' + result + ' not handled') # pragma: no cover
		shutit.fail('_challenge_done should not get here') # pragma: no cover
		return True


	def _pause_input_filter(self, input_string):
		"""Input filter for pause point to catch special keystrokes
		"""
		shutit = self.shutit
		# Can get errors with eg up/down chars
		if len(input_string) == 1:
			# Picked CTRL-u as the rarest one accepted by terminals.
			if ord(input_string) == 21 and shutit.build['delivery'] == 'docker':
				shutit_global.shutit_global_object.log('CTRL and u caught, forcing a tag at least',level=logging.INFO)
				shutit.do_repository_work('tagged_by_shutit', password=shutit.host['password'], docker_executable=shutit.host['docker_executable'], force=True)
				shutit_global.shutit_global_object.log('Commit and tag done. Hit CTRL and ] to continue with build. Hit return for a prompt.',level=logging.CRITICAL)
			# CTRL-d
			elif ord(input_string) == 4:
				shutit_global.shutit_global_object.log("""\r\n\r\nCTRL-D ignored in pause points. Type 'exit' to log out, but be warned that continuing the run with CTRL-] may then give unexpected results!\r\n""", level=logging.INFO, transient=True)
				return ''
			# CTRL-h
			elif ord(input_string) == 8:
				shutit_global.shutit_global_object.signal_id = 8
				# Return the escape from pexpect char
				return '\x1d'
			# CTRL-g
			elif ord(input_string) == 7:
				shutit_global.shutit_global_object.signal_id = 7
				# Return the escape from pexpect char
				return '\x1d'
			# CTRL-p - used as part of CTRL-p - CTRL-q
			elif ord(input_string) == 16:
				shutit_global.shutit_global_object.signal_id = 16
				if shutit.build['exam'] and shutit_global.shutit_global_object.loglevel not in ('DEBUG','INFO'):
					return ''
				else:
					return '\x10'
			# CTRL-q
			elif ord(input_string) == 17:
				shutit_global.shutit_global_object.signal_id = 17
				if not shutit.build['exam'] and shutit_global.shutit_global_object.loglevel not in ('DEBUG',):
					shutit_global.shutit_global_object.log('CTRL-q hit, quitting ShutIt',transient=True,level=logging.CRITICAL)
					shutit_global.shutit_global_object.handle_exit(exit_code=1)
			# CTRL-s
			elif ord(input_string) == 19:
				shutit_global.shutit_global_object.signal_id = 19
				# Return the escape from pexpect char
				return '\x1d'
			# CTRL-]
			# Foreign keyboard?: http://superuser.com/questions/398/how-to-send-the-escape-character-on-os-x-terminal/427#427
			elif ord(input_string) == 29:
				shutit_global.shutit_global_object.signal_id = 29
				# Return the escape from pexpect char
				return '\x1d'
		return input_string



def add_shutit_pexpect_session_environment(pexpect_session_environment):
	"""Adds an environment object to a shutit_pexpect_session object.
	"""
	shutit_global.shutit_global_object.shutit_pexpect_session_environments.add(pexpect_session_environment)
