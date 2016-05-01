"""Contains all the core ShutIt methods and functionality, and public interface
off to internal objects such as shutit_pexpect.
"""

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
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#ITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

import sys
import os
import socket
import time
import shutit_util
import string
import re
import textwrap
import base64
import getpass
import datetime
import pexpect
import md5
from shutit_module import ShutItFailException
import logging


class ShutIt(object):
	"""ShutIt build class.
	Represents an instance of a ShutIt run/session/build with associated config.
	"""

	def __init__(self, **kwargs):
		"""Constructor.
		Sets up:

				- shutit_pexpect_sessions - pexpect objects representing shell interactions
				- shutit_modules          - representation of loaded shutit modules
				- shutit_main_dir         - directory in which shutit is located
				- cfg                     - dictionary of configuration of build
				- cwd                     - working directory of build
				- shutit_map              - maps module_ids to module objects
		"""
		# These used to be in shutit_global, so we pass them in as args so
		# the original reference can be put in shutit_global
		self.current_shutit_pexpect_session = kwargs['current_shutit_pexpect_session']
		self.shutit_pexpect_sessions        = kwargs['shutit_pexpect_sessions']
		self.shutit_modules                 = kwargs['shutit_modules']
		self.shutit_main_dir                = kwargs['shutit_main_dir']
		self.cfg                            = kwargs['cfg']
		self.cwd                            = kwargs['cwd']
		self.shutit_command_history         = kwargs['shutit_command_history']
		self.shutit_map                     = kwargs['shutit_map']
		# These are new members we dont have to provide compatibility for
		self.conn_modules = set()


	def get_current_shutit_pexpect_session(self):
		"""Returns the currently-set default pexpect child.

		@return: default shutit pexpect child object
		"""
		return self.current_shutit_pexpect_session


	def get_default_shutit_pexpect_session_expect(self):
		"""Returns the currently-set default pexpect string (usually a prompt).

		@return: default pexpect string
		"""
		return self.current_shutit_pexpect_session.default_expect


	def get_default_shutit_pexpect_session_check_exit(self):
		"""Returns default value of check_exit. See send method.

		@rtype:  boolean
		@return: Default check_exit value
		"""
		return self.current_shutit_pexpect_session.check_exit


	def set_default_shutit_pexpect_session(self, shutit_pexpect_session):
		"""Sets the default pexpect child.

		@param shutit_pexpect_session: pexpect child to set as default
		"""
		self.current_shutit_pexpect_session = shutit_pexpect_session


	def set_default_shutit_pexpect_session_expect(self, expect=None):
		"""Sets the default pexpect string (usually a prompt).
		Defaults to the configured root prompt if no
		argument is passed.

		@param expect: String to expect in the output
		@type expect: string
		"""
		if expect == None:
			self.current_shutit_pexpect_session.default_expect = self.cfg['expect_prompts']['root']
		else:
			self.current_shutit_pexpect_session.default_expect = expect


	def fail(self, msg, shutit_pexpect_child=None, throw_exception=False):
		"""Handles a failure, pausing if a pexpect child object is passed in.

		@param shutit_pexpect_child: pexpect child to work on
		@param throw_exception: Whether to throw an exception.
		@type throw_exception: boolean
		"""
		# Note: we must not default to a child here
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		if shutit_pexpect_child is not None:
			shutit_pexpect_session.pause_point('Pause point on fail: ' + msg, colour='31')
		if throw_exception:
			print >> sys.stderr, 'Error caught: ' + msg
			print >> sys.stderr
			raise ShutItFailException(msg)
		else:
			# This is an "OK" failure, ie we don't need to throw an exception.
			# However, it's still a failure, so return 1
			self.log(msg,level=logging.DEBUG)
			self.log('Error seen, exiting with status 1',level=logging.DEBUG)
			shutit_util.handle_exit(exit_code=1,msg=msg)


	def log(self, msg, add_final_message=False, level=logging.INFO, transient=False, newline=True):
		"""Logging function.

		@param code:              Colour code for logging.
		@param add_final_message: Add this log line to the final message output to the user
		@param level:             Python log level
		@param transient:         Just write to terminal, no new line
		"""
		global cfg
		if transient:
			if newline:
				msg += '\n'
			sys.stdout.write(msg)
			return
		else:
			logging.log(level,msg)
			if add_final_message:
				cfg['build']['report_final_messages'] += msg + '\n'


	# TODO: sort out environments
	def get_current_environment(self):
		return self.cfg['environment'][self.cfg['build']['current_environment_id']]


	def multisend(self,
	              send,
	              send_dict,
	              expect=None,
	              shutit_pexpect_child=None,
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
		@param shutit_pexpect_child:                See send()
		@param timeout:              See send()
		@param check_exit:           See send()
		@param fail_on_empty_before: See send()
		@param record_command:       See send()
		@param exit_values:          See send()
		@param echo:                 See send()
		@param note:                 See send()
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		expect = expect or self.get_current_shutit_pexpect_session().default_expect
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.multisend(send,send_dict,expect=expect,timeout=timeout,check_exit=check_exit,fail_on_empty_before=fail_on_empty_before,record_command=record_command,exit_values=exit_values,escape=escape,echo=echo,note=note,delaybeforesend=delaybeforesend,loglevel=loglevel)


	def send_until(self,
	               send,
	               regexps,
	               not_there=False,
	               shutit_pexpect_child=None,
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
		@param expect:               See send()
		@param shutit_pexpect_child:                See send()
		@param fail_on_empty_before: See send()
		@param record_command:       See send()
		@param echo:                 See send()
		@param note:                 See send()
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.send_until(send,regexps,not_there=not_there,cadence=cadence,retries=retries,echo=echo,note=note,delaybeforesend=delaybeforesend,loglevel=loglevel)


	# TODO: move to shutit_pexpect, pass through
	def challenge(self,
                  task_desc,
                  expect=None,
                  hints=[],
                  congratulations='OK',
                  failed='FAILED',
	              expect_type='exact',
	              challenge_type='command',
	              shutit_pexpect_child=None,
	              timeout=None,
	              check_exit=None,
	              fail_on_empty_before=True,
	              record_command=True,
	              exit_values=None,
	              echo=True,
	              escape=False,
	              pause=1,
	              loglevel=logging.DEBUG,
	              delaybeforesend=0,
	              follow_on_context={}):
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
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		# don't catch CTRL-C, pass it through.
		self.cfg['build']['ctrlc_passthrough'] = True
		preserve_newline                       = False
		skipped                                = False
		if expect_type == 'regexp':
			if type(expect) == str:
				expect = [expect]
			if type(expect) != list:
				self.fail('expect_regexps should be list')
		elif expect_type == 'md5sum':
			preserve_newline = True
			pass
		elif expect_type == 'exact':
			pass
		else:
			self.fail('Must pass either expect_regexps or md5sum in')
		if len(hints):
			cfg['build']['pause_point_hints'] = hints
		else:
			cfg['build']['pause_point_hints'] = []
		if challenge_type == 'command':
			help_text = shutit_util.colourise('32','''\nType 'help' or 'h' to get a hint, 'exit' to skip, 'shutitreset' to reset state.''')
			ok = False
			while not ok:
				self.log(shutit_util.colourise('32','''\nChallenge!'''),transient=True)
				if len(hints):
					self.log(shutit_util.colourise('32',help_text),transient=True)
				time.sleep(pause)
				# TODO: bash path completion
				send = shutit_util.get_input(task_desc + ' => ',colour='31')
				if not send or send.strip() == '':
					continue
				if send in ('help','h'):
					if len(hints):
						self.log(help_text,transient=True)
						self.log(shutit_util.colourise('32',hints.pop()),transient=True)
					else:
						self.log(help_text,transient=True)
						self.log(shutit_util.colourise('32','No hints left, sorry! CTRL-g to reset state, CTRL-s to skip this step'),transient=True)
					time.sleep(pause)
					continue
				if send == 'shutitreset':
					self._challenge_done(shutit_pexpect_session,result='reset',follow_on_context=follow_on_context)
					continue
				if send == 'shutitquit':
					self._challenge_done(shutit_pexpect_session,result='reset',follow_on_context=follow_on_context)
					shutit_util.handle_exit(exit_code=1)
				if send == 'exit':
					self._challenge_done(shutit_pexpect_session,result='exited',follow_on_context=follow_on_context)
					cfg['build']['pause_point_hints'] = []
					return
				output = self.send_and_get_output(send,shutit_pexpect_child=shutit_pexpect_child,timeout=timeout,retry=1,record_command=record_command,echo=echo, loglevel=loglevel, fail_on_empty_before=False, preserve_newline=preserve_newline, delaybeforesend=delaybeforesend)
				md5sum_output = md5.md5(output).hexdigest()
				self.log('output: ' + output + ' is md5sum: ' + md5sum_output,level=logging.DEBUG)
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
					self.log('\n\n' + shutit_util.colourise('32','failed') + '\n',transient=True)
					self._challenge_done(shutit_pexpect_session,result='failed')
					continue
		elif challenge_type == 'golf':
			# pause, and when done, it checks your working based on check_command.
			ok = False
			# hints
			if len(hints):
				task_desc_new = task_desc + '\r\n\r\nHit CTRL-h for help, CTRL-g to reset state, CTRL-s to skip'
			else:
				task_desc_new = task_desc
			while not ok:
				shutit_pexpect_session.pause_point(shutit_util.colourise('31',task_desc_new),colour='31') # TODO: message
				if cfg['SHUTIT_SIGNAL']['ID'] == 8:
					if len(cfg['build']['pause_point_hints']):
						self.log(shutit_util.colourise('31','\r\n========= HINT ==========\r\n\r\n' + cfg['build']['pause_point_hints'].pop(0)),transient=True)
					else:
						self.log(shutit_util.colourise('31','\r\n\r\n' + 'No hints available!'),transient=True)
					time.sleep(1)
					# clear the signal
					cfg['SHUTIT_SIGNAL']['ID'] = 0
					continue
				elif cfg['SHUTIT_SIGNAL']['ID'] == 7:
					self.log(shutit_util.colourise('31','\r\n========= RESETTING STATE ==========\r\n\r\n'),transient=True)
					self._challenge_done(shutit_pexpect_session,result='reset', follow_on_context=follow_on_context)
					# clear the signal
					cfg['SHUTIT_SIGNAL']['ID'] = 0
					self.challenge(
						task_desc=task_desc,
						expect=expect,
						hints=hints,
						congratulations=congratulations,
						failed=failed,
						expect_type=expect_type,
						challenge_type=challenge_type,
						shutit_pexpect_child=None,
						timeout=timeout,
						check_exit=check_exit,
						fail_on_empty_before=fail_on_empty_before,
						record_command=record_command,
						exit_values=exit_values,
						echo=echo,
						escape=escape,
						pause=pause,
						loglevel=loglevel,
	                    delaybeforesend=0,
						follow_on_context=follow_on_context
					)
					return
				elif cfg['SHUTIT_SIGNAL']['ID'] == 19:
					# Clear the signal.
					cfg['SHUTIT_SIGNAL']['ID'] = 0
					# Skip test.
					shutit.log('Test skipped',level=logging.INFO)
					skipped=True
					break
				shutit.log('State submitted, checking your work...',level=logging.INFO)
				check_command = follow_on_context.get('check_command')
				output = self.send_and_get_output(check_command,shutit_pexpect_child=shutit_pexpect_child,timeout=timeout,retry=1,record_command=record_command,echo=False, loglevel=loglevel, fail_on_empty_before=False, preserve_newline=preserve_newline, delaybeforesend=delaybeforesend)
				self.log('output: ' + output,level=logging.DEBUG)
				md5sum_output = md5.md5(output).hexdigest()
				if expect_type == 'md5sum':
					self.log('output: ' + output + ' is md5sum: ' + md5sum_output,level=logging.DEBUG)
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
					shutit.log('\n\n' + shutit_util.colourise('31','Failed! CTRL-g to reset state, CTRL-h for a hint') + '\n',transient=True)
					self._challenge_done(shutit_pexpect_session,result='failed')
					continue
		else:
			self.fail('Challenge type: ' + challenge_type + ' not supported')
		self._challenge_done(shutit_pexpect_session,result='ok',follow_on_context=follow_on_context,congratulations=congratulations,skipped=skipped)
		# Tidy up hints
		cfg['build']['pause_point_hints'] = []
	# Alternate names
	practice = challenge
	golf     = challenge


	# TODO: move to shutit_pexpect
	def _challenge_done(self, shutit_pexpect_session, result=None, congratulations=None, follow_on_context={},pause=1,skipped=False):
		if result == 'ok':
			if congratulations:
				self.log('\n\n' + shutit_util.colourise('32',congratulations) + '\n',transient=True)
			time.sleep(pause)
			self.cfg['build']['ctrlc_passthrough'] = False
			if follow_on_context != {}:
				if follow_on_context.get('context') == 'docker':
					container_name = follow_on_context.get('ok_container_name')
					if not container_name:
						self.log('No reset context available, carrying on.',level=logging.INFO)
					elif skipped:
						# We need to ensure the correct state.
						shutit_pexpect_session.replace_container(container_name)
						self.log('State restored.',level=logging.INFO)
					else:
						self.log(shutit_util.colourise('31','Continuing, remember you can restore to a known state with CTRL-g.'),transient=True)
				else:
					self.fail('Follow-on context not handled on pass')
			return
		elif result in ('failed'):
			self.cfg['build']['ctrlc_passthrough'] = False
			time.sleep(1)
			return
		elif result == 'exited':
			self.cfg['build']['ctrlc_passthrough'] = False
			return
		elif result in ('reset'):
			if follow_on_context != {}:
				if follow_on_context.get('context') == 'docker':
					container_name = follow_on_context.get('reset_container_name')
					if not container_name:
						self.log('No reset context available, carrying on.',level=logging.DEBUG)
					else:
						shutit_pexpect_session.replace_container(container_name)
						self.log('State restored.',level=logging.INFO)
				else:
					self.fail('Follow-on context not handled on reset')
			return
		else:
			self.fail('result: ' + result + ' not handled')
		self.fail('_challenge_done should not get here')


	# TODO: move to shutit_pexpect, pass through
	def send(self,
	         send,
	         expect=None,
	         shutit_pexpect_child=None,
	         timeout=None,
	         check_exit=None,
	         fail_on_empty_before=True,
	         record_command=True,
	         exit_values=None,
	         echo=False,
	         escape=False,
	         retry=3,
	         note=None,
	         assume_gnu=True,
	         delaybeforesend=0,
		     loglevel=logging.INFO):
		"""Send string as a shell command, and wait until the expected output
		is seen (either a string or any from a list of strings) before
		returning. The expected string will default to the currently-set
		default expected string (see get_default_shutit_pexpect_session_expect)

		Returns the pexpect return value (ie which expected string in the list matched)

		@param send: String to send, ie the command being issued. If set to None, we consume up to the expect string, which is useful if we just matched output that came before a standard command that returns to the prompt.
		@param expect: String that we expect to see in the output. Usually a prompt. Defaults to currently-set expect string (see set_default_shutit_pexpect_session_expect)
		@param shutit_pexpect_child: pexpect child to issue command to.
		@param timeout: Timeout on response
		@param check_exit: Whether to check the shell exit code of the passed-in command.  If the exit value was non-zero an error is thrown.  (default=None, which takes the currently-configured check_exit value) See also fail_on_empty_before.
		@param fail_on_empty_before: If debug is set, fail on empty match output string (default=True) If this is set to False, then we don't check the exit value of the command.
		@param record_command: Whether to record the command for output at end. As a safety measure, if the command matches any 'password's then we don't record it.
		@param exit_values: Array of acceptable exit values as strings
		@param echo: Whether to suppress any logging output from pexpect to the terminal or not.  We don't record the command if this is set to False unless record_command is explicitly passed in as True.
		@param escape: Whether to escape the characters in a bash-friendly way, ie $'\Uxxxxxx'
		@param retry: Number of times to retry the command if the first attempt doesn't work. Useful if going to the network
		@param note: If a note is passed in, and we are in walkthrough mode, pause with the note printed
		@param assume_gnu: Assume the gnu version of commands, which are not in OSx by default (for example)
		@return: The pexpect return value (ie which expected string in the list matched)
		@rtype: string
		"""
		global cfg
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		if type(expect) == dict:
			return shutit_pexpect_session.multisend(send=send,send_dict=expect,expect=self.get_default_shutit_pexpect_session_expect(),timeout=timeout,check_exit=check_exit,fail_on_empty_before=fail_on_empty_before,record_command=record_command,exit_values=exit_values,echo=echo,note=note,loglevel=loglevel,delaybeforesend=delaybeforesend)
		expect = expect or self.get_current_shutit_pexpect_session().default_expect
		shutit.log('Sending in session: ' + self.get_shutit_pexpect_session_id(shutit_pexpect_child),level=logging.DEBUG)
		self._handle_note(note, command=str(send), training_input=str(send))
		if timeout == None:
			timeout = 3600
		
		if cfg['build']['loglevel'] <= logging.DEBUG:
			echo=True

		# Handle OSX to get the GNU version of the command
		if assume_gnu:
			send = shutit_util.get_send_command(send)
			
		# If check_exit is not passed in
		# - if the expect matches the default, use the default check exit
		# - otherwise, default to doing the check
		if check_exit == None:
			# If we are in video mode, ignore exit value
			if cfg['build']['video'] or cfg['build']['training'] or cfg['build']['walkthrough']:
				check_exit = False
			elif expect == self.get_default_shutit_pexpect_session_expect():
				check_exit = self.get_default_shutit_pexpect_session_check_exit()
			else:
				# If expect given doesn't match the defaults and no argument
				# was passed in (ie check_exit was passed in as None), set
				# check_exit to true iff it matches a prompt.
				expect_matches_prompt = False
				for prompt in cfg['expect_prompts']:
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
							self.shutit_command_history.append ('#redacted command, password')
							ok_to_record = False
							break
					if not ok_to_record:
						break
			if ok_to_record:
				self.shutit_command_history.append(send)
		if send != None:
			self.log('Sending: ' + send,level=loglevel)
		if send != None:
			self.log('================================================================================',level=logging.DEBUG)
			self.log('Sending>>>' + send + '<<<',level=logging.DEBUG)
			self.log('Expecting>>>' + str(expect) + '<<<',level=logging.DEBUG)
		# Don't echo if echo passed in as False
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
					if _count > cfg['build']['stty_cols'] - 50:
						escaped_str += r"""'\
$'"""
						_count = 0
				escaped_str += "'"
				self.log('This string was sent safely: ' + send, level=logging.DEBUG)
			if not echo:
				oldlog = shutit_pexpect_child.logfile_send
				shutit_pexpect_child.logfile_send = None
				if escape:
					# 'None' escaped_str's are possible from multisends with nothing to send.
					if escaped_str != None:
						if len(escaped_str) + 25 > cfg['build']['stty_cols']:
							fname = shutit_pexpect_session.create_command_file(expect,escaped_str)
							res = self.send(' ' + fname,expect=expect,shutit_pexpect_child=shutit_pexpect_child,timeout=timeout,check_exit=check_exit,fail_on_empty_before=False,record_command=False,exit_values=exit_values,echo=False,escape=False,retry=retry,loglevel=loglevel, delaybeforesend=delaybeforesend)
							shutit_pexpect_session.sendline(' rm -f ' + fname,delaybeforesend=delaybeforesend)
							shutit_pexpect_session.expect(expect)
							return res
						else:
							shutit_pexpect_session.sendline(escaped_str,delaybeforesend=delaybeforesend)
							expect_res = self._expect_allow_interrupt(shutit_pexpect_child, expect, timeout)
					else:
						expect_res = self._expect_allow_interrupt(shutit_pexpect_child, expect, timeout)
				else:
					if send != None:
						if len(send) + 25 > cfg['build']['stty_cols']:
							fname = shutit_pexpect_session.create_command_file(expect,send)
							res = self.send(' ' + fname,expect=expect,shutit_pexpect_child=shutit_pexpect_child,timeout=timeout,check_exit=check_exit,fail_on_empty_before=False,record_command=False,exit_values=exit_values,echo=False,escape=False,retry=retry,loglevel=loglevel, delaybeforesend=delaybeforesend)
							shutit_pexpect_session.sendline(' rm -f ' + fname,delaybeforesend=delaybeforesend)
							shutit_pexpect_child.expect(expect)
							return res
						else:
							shutit_pexpect_session.sendline(send,delaybeforesend=delaybeforesend)
							expect_res = self._expect_allow_interrupt(shutit_pexpect_child, expect, timeout)
					else:
						expect_res = self._expect_allow_interrupt(shutit_pexpect_child, expect, timeout)
				shutit_pexpect_child.logfile_send = oldlog
			else:
				if escape:
					if escaped_str != None:
						if len(escaped_str) + 25 > cfg['build']['stty_cols']:
							fname = shutit_pexpect_session.create_command_file(expect,escaped_str)
							res = self.send(' ' + fname,expect=expect,shutit_pexpect_child=shutit_pexpect_child,timeout=timeout,check_exit=check_exit,fail_on_empty_before=False,record_command=False,exit_values=exit_values,echo=False,escape=False,retry=retry,loglevel=loglevel, delaybeforesend=delaybeforesend)
							shutit_pexpect_session.sendline(' rm -f ' + fname,delaybeforesend=delaybeforesend)
							shutit_pexpect_child.expect(expect)
							return res
						else:
							shutit_pexpect_session.send(escaped_str,delaybeforesend=delaybeforesend)
							expect_res = self._expect_allow_interrupt(shutit_pexpect_child, expect, timeout)
					else:
						expect_res = self._expect_allow_interrupt(shutit_pexpect_child, expect, timeout)
				else:
					if send != None:
						if len(send) + 25 > cfg['build']['stty_cols']:
							fname = shutit_pexpect_session.create_command_file(expect,send)
							res = self.send(' ' + fname,expect=expect,shutit_pexpect_child=shutit_pexpect_child,timeout=timeout,check_exit=check_exit,fail_on_empty_before=False,record_command=False,exit_values=exit_values,echo=False,escape=False,retry=retry,loglevel=loglevel, delaybeforesend=delaybeforesend)
							shutit_pexpect_session.sendline(' rm -f ' + fname,delaybeforesend=delaybeforesend)
							shutit_pexpect_child.expect(expect)
							return res
						else:
							if echo:
								self.divert_output(sys.stdout)
							shutit_pexpect_session.sendline(send,delaybeforesend=delaybeforesend)
							expect_res = self._expect_allow_interrupt(shutit_pexpect_child, expect, timeout)
							if echo:
								self.divert_output(None)
					else:
						expect_res = self._expect_allow_interrupt(shutit_pexpect_child, expect, timeout)
			# Handles 'cannot concatenate 'str' and 'type' objects' errors
			try:
				logged_output = ''.join((shutit_pexpect_child.before + shutit_pexpect_child.after).split('\n'))
				logged_output = logged_output.replace(send,'',1)
				logged_output = logged_output.replace('\r','')
				logged_output = logged_output[:30] + ' [...]'
				self.log('Output (squashed): ' + logged_output,level=loglevel)
				self.log('shutit_pexpect_child.before>>>' + shutit_pexpect_child.before + '<<<',level=logging.DEBUG)
				self.log('shutit_pexpect_child.after>>>' + shutit_pexpect_child.after + '<<<',level=logging.DEBUG)
			except:
				pass
			if fail_on_empty_before:
				if shutit_pexpect_child.before.strip() == '':
					self.fail('before empty after sending: ' + str(send) + '\n\nThis is expected after some commands that take a password.\nIf so, add fail_on_empty_before=False to the send call.\n\nIf that is not the problem, did you send an empty string to a prompt by mistake?', shutit_pexpect_child=shutit_pexpect_child)
			elif not fail_on_empty_before:
				# Don't check exit if fail_on_empty_before is False
				self.log('' + shutit_pexpect_child.before + '<<<', level=logging.DEBUG)
				check_exit = False
				for prompt in cfg['expect_prompts']:
					if prompt == expect:
						# Reset prompt
						shutit_pexpect_session.setup_prompt('reset_tmp_prompt')
						shutit_pexpect_child.revert_prompt('reset_tmp_prompt', expect)
			# Last output - remove the first line, as it is the previous command.
			cfg['build']['last_output'] = '\n'.join(shutit_pexpect_child.before.split('\n')[1:])
			if check_exit:
				# store the output
				if not shutit_pexpect_session.check_last_exit_values(send, expect=expect, exit_values=exit_values, retry=retry):
					self.log('Sending: ' + send + ' : failed, retrying', level=logging.DEBUG)
					retry -= 1
					assert(retry > 0)
					continue
			break
		if cfg['build']['step_through']:
			shutit_pexpect_session.pause_point('pause point: stepping through')
		if cfg['build']['ctrlc_stop']:
			cfg['build']['ctrlc_stop'] = False
			shutit_pexpect_session.pause_point('pause point: interrupted by CTRL-c')
		self._handle_note_after(note=note)
		return expect_res
	# alias send to send_and_expect
	send_and_expect = send

	

	def _handle_note(self, note, command='', training_input=''):
		"""Handle notes and walkthrough option.

		@param note:                 See send()
		"""
		global cfg
		if cfg['build']['walkthrough'] and note != None:
			wait = self.cfg['build']['walkthrough_wait']
			wrap = '\n' + 80*'=' + '\n'
			message = wrap + note + wrap
			if command != '':
				message += 'Command to be run is:\n\t' + command + wrap
			if wait >= 0:
				self.pause_point(message, colour=31, wait=wait)
			else:
				if training_input != '' and cfg['build']['training']:
					print(shutit_util.colourise('31',message))
					while shutit_util.util_raw_input(prompt=shutit_util.colourise('32','Type in the command to continue: ')) != training_input:
						print('Wrong! Try again!')
				else:
					self.pause_point(message, colour=31)


	def _handle_note_after(self, note):
		if self.cfg['build']['walkthrough'] and note != None:
			wait = self.cfg['build']['walkthrough_wait']
			if wait >= 0:
				time.sleep(wait)


	def _expect_allow_interrupt(self, shutit_pexpect_child, expect, timeout, iteration_s=1):
		"""This function allows you to interrupt the run at more or less any point by breaking up the timeout into interactive chunks.
		"""
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		accum_timeout = 0
		if type(expect) == str:
			expect = [expect]
		if timeout < 1:
			timeout = 1
		if iteration_s > timeout:
			iteration_s = timeout - 1
		if iteration_s < 1:
			iteration_s = 1
		timed_out = True
		while accum_timeout < timeout:
			res = shutit_pexpect_session.expect(expect, timeout=iteration_s)
			if res == len(expect):
				if shutit.cfg['build']['ctrlc_stop']:
					timed_out = False
					shutit.cfg['build']['ctrlc_stop'] = False
					break
				accum_timeout += iteration_s
			else:
				return res
		if timed_out and not shutit_util.determine_interactive():
			self.log('Command timed out, trying to get terminal back for you', level=logging.DEBUG)
			self.fail('Timed out and could not recover')
		else:
			if shutit_util.determine_interactive():
				shutit_pexpect_child.send('\x03')
				res = shutit_pexpect_child.expect(expect,timeout=1)
				if res == len(expect):
					shutit_pexpect_child.send('\x1a')
					res = shutit_pexpect_child.expect(expect,timeout=1)
					if res == len(expect):
						self.fail('CTRL-C sent by ShutIt following a timeout, and could not recover')
				shutit_pexpect_session.pause_point('CTRL-C sent by ShutIt following a timeout; the command has been cancelled')
				return res
			else:
				if timed_out:
					self.fail('Timed out and interactive, but could not recover')
				else:
					self.fail('CTRL-C hit and could not recover')
		self.fail('Should not get here (_expect_allow_interrupt)')




	# TODO: move to shutit_pexpect, pass through
	def run_script(self,
	               script,
	               expect=None,
	               shutit_pexpect_child=None,
	               in_shell=True,
	               note=None,
	               delaybeforesend=0,
	               loglevel=logging.DEBUG):
		"""Run the passed-in string as a script on the target's command line.

		@param script:   String representing the script. It will be de-indented
						 and stripped before being run.
		@param expect:   See send()
		@param shutit_pexpect_child:    See send()
		@param in_shell: Indicate whether we are in a shell or not. (Default: True)
		@param note:     See send()

		@type script:    string
		@type in_shell:  boolean
		"""
		global cfg
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		expect = expect or self.get_current_shutit_pexpect_session().default_expect
		self._handle_note(note, 'Script: ' + str(script))
		self.log('Running script beginning: "' + string.join(script.split())[:30] + ' [...]', level=logging.INFO)
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
		if cfg['build']['delivery'] in ('docker','dockerfile') and in_shell:
				script = ('set -o xtrace \n\n' + script + '\n\nset +o xtrace')
		self.send(' mkdir -p ' + cfg['build']['shutit_state_dir'] + '/scripts && chmod 777 ' + cfg['build']['shutit_state_dir'] + '/scripts', expect=expect, shutit_pexpect_child=shutit_pexpect_child, echo=False,loglevel=loglevel, delaybeforesend=delaybeforesend)
		self.send_file(cfg['build']['shutit_state_dir'] + '/scripts/shutit_script.sh', script, loglevel=loglevel, delaybeforesend=delaybeforesend)
		self.send(' chmod +x ' + cfg['build']['shutit_state_dir'] + '/scripts/shutit_script.sh', expect=expect, shutit_pexpect_child=shutit_pexpect_child, echo=False,loglevel=loglevel, delaybeforesend=delaybeforesend)
		self.shutit_command_history.append('    ' + script.replace('\n', '\n    '))
		if in_shell:
			ret = self.send(' . ' + cfg['build']['shutit_state_dir'] + '/scripts/shutit_script.sh && rm -f ' + cfg['build']['shutit_state_dir'] + '/scripts/shutit_script.sh && rm -f ' + cfg['build']['shutit_state_dir'] + '/scripts/shutit_script.sh', expect=expect, shutit_pexpect_child=shutit_pexpect_child, echo=False,loglevel=loglevel, delaybeforesend=delaybeforesend)
		else:
			ret = self.send(' ' + cfg['build']['shutit_state_dir'] + '/scripts/shutit_script.sh && rm -f ' + cfg['build']['shutit_state_dir'] + '/scripts/shutit_script.sh', expect=expect, shutit_pexpect_child=shutit_pexpect_child, echo=False,loglevel=loglevel, delaybeforesend=delaybeforesend)
		self._handle_note_after(note=note)
		return ret


	# TODO: move to shutit_pexpect, pass through
	def send_file(self,
	              path,
	              contents,
	              expect=None,
	              shutit_pexpect_child=None,
	              truncate=False,
	              note=None,
	              user=None,
	              group=None,
	              delaybeforesend=0,
	              loglevel=logging.INFO):
		"""Sends the passed-in string as a file to the passed-in path on the
		target.

		@param path:        Target location of file on target.
		@param contents:    Contents of file as a string.
		@param expect:      See send()
		@param shutit_pexpect_child:       See send()
		@param note:        See send()
		@param user:        Set ownership to this user (defaults to whoami)
		@param group:       Set group to this user (defaults to first group in groups)

		@type path:         string
		@type contents:     string
		"""
		global cfg
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		expect = expect or self.get_current_shutit_pexpect_session().default_expect
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		self._handle_note(note, 'Sending contents to path: ' + path)
		# make more efficient by only looking at first 10000 chars, stop when we get to 30 chars rather than reading whole file.
		split_contents = ''.join((contents[:10000].split()))
		strings_from_file = re.findall("[^\x00-\x1F\x7F-\xFF]", split_contents)
		self.log('Sending file contents beginning: "' + ''.join(strings_from_file)[:30] + ' [...]" to file: ' + path, level=loglevel)
		if user == None:
			user = shutit_pexpect_session.whoami()
		if group == None:
			group = self.whoarewe()
		if cfg['build']['current_environment_id'] == 'ORIGIN_ENV':
			# If we're on the root env (ie the same one that python is running on, then use python.
			f = open(path,'w')
			if truncate:
				f.truncate(0)
			f.write(contents)
			f.close()
		elif cfg['build']['delivery'] in ('bash','dockerfile'):
			if truncate and self.file_exists(path):
				self.send(' rm -f ' + path, expect=expect, shutit_pexpect_child=shutit_pexpect_child, echo=False,loglevel=loglevel, delaybeforesend=delaybeforesend)
			random_id = shutit_util.random_id()
			self.send(' ' + shutit_util.get_command('head') + ' -c -1 > ' + path + "." + random_id + " << 'END_" + random_id + """'\n""" + base64.b64encode(contents) + '''\nEND_''' + random_id, echo=False,loglevel=loglevel, delaybeforesend=delaybeforesend)
			self.send(' cat ' + path + '.' + random_id + ' | base64 -d > ' + path, echo=False,loglevel=loglevel, delaybeforesend=delaybeforesend)
		else:
			host_child = self.get_shutit_pexpect_session_from_id('host_child').pexpect_child
			path = path.replace(' ', '\ ')
			# get host session
			tmpfile = cfg['build']['shutit_state_dir_base'] + 'tmp_' + shutit_util.random_id()
			f = open(tmpfile,'w')
			f.truncate(0)
			f.write(contents)
			f.close()
			# Create file so it has appropriate permissions
			self.send(' touch ' + path, shutit_pexpect_child=shutit_pexpect_child, expect=expect, echo=False,loglevel=loglevel, delaybeforesend=delaybeforesend)
			# If path is not absolute, add $HOME to it.
			if path[0] != '/':
				self.send(' cat ' + tmpfile + ' | ' + cfg['host']['docker_executable'] + ' exec -i ' + cfg['target']['container_id'] + " bash -c 'cat > $HOME/" + path + "'", shutit_pexpect_child=host_child, expect=cfg['expect_prompts']['origin_prompt'], echo=False,loglevel=loglevel, delaybeforesend=delaybeforesend)
			else:
				self.send(' cat ' + tmpfile + ' | ' + cfg['host']['docker_executable'] + ' exec -i ' + cfg['target']['container_id'] + " bash -c 'cat > " + path + "'", shutit_pexpect_child=host_child, expect=cfg['expect_prompts']['origin_prompt'], echo=False,loglevel=loglevel, delaybeforesend=delaybeforesend)
			self.send(' chown ' + user + ' ' + path + ' && chgrp ' + group + ' ' + path, shutit_pexpect_child=shutit_pexpect_child, expect=expect, echo=False,loglevel=loglevel, delaybeforesend=delaybeforesend)
			os.remove(tmpfile)
		self._handle_note_after(note=note)


	def chdir(self,
	          path,
	          expect=None,
	          shutit_pexpect_child=None,
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
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		expect = expect or self.get_current_shutit_pexpect_session().default_expect
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		shutit_pexpect_session.chdir(path,expect=expect,timeout=timeout,note=note,delaybeforesend=delaybeforesend,loglevel=loglevel)
		


	def send_host_file(self,
	                   path,
	                   hostfilepath,
	                   expect=None,
	                   shutit_pexpect_child=None,
	                   timeout=3600,
	                   note=None,
	                   user=None,
	                   group=None,
	                   delaybeforesend=0,
	                   loglevel=logging.INFO):
		"""Send file from host machine to given path

		@param path:          Path to send file to.
		@param hostfilepath:  Path to file from host to send to target.
		@param expect:        See send()
		@param shutit_pexpect_child:         See send()
		@param note:          See send()
		@param user:          Set ownership to this user (defaults to whoami)
		@param group:         Set group to this user (defaults to first group in groups)

		@type path:           string
		@type hostfilepath:   string
		"""
		global cfg
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		expect = expect or self.get_current_shutit_pexpect_session().default_expect
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		self._handle_note(note, 'Sending file from host: ' + hostfilepath + ' to target path: ' + path)
		self.log('Sending file from host: ' + hostfilepath + ' to: ' + path, level=loglevel)
		if user == None:
			user = shutit_pexpect_session.whoami()
		if group == None:
			group = self.whoarewe()
		if cfg['build']['delivery'] in ('bash','dockerfile'):
			retdir = self.send_and_get_output('pwd',loglevel=loglevel, delaybeforesend=delaybeforesend)
			self.send(' pushd ' + cfg['environment'][cfg['build']['current_environment_id']]['module_root_dir'], echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
			self.send(' cp -r ' + hostfilepath + ' ' + retdir + '/' + path,expect=expect, shutit_pexpect_child=shutit_pexpect_child, timeout=timeout, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
			self.send(' chown ' + user + ' ' + hostfilepath + ' ' + retdir + '/' + path,expect=expect, shutit_pexpect_child=shutit_pexpect_child, timeout=timeout, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
			self.send(' chgrp ' + group + ' ' + hostfilepath + ' ' + retdir + '/' + path,expect=expect, shutit_pexpect_child=shutit_pexpect_child, timeout=timeout, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
			self.send(' popd', expect=expect, shutit_pexpect_child=shutit_pexpect_child, timeout=timeout, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
		else:
			if os.path.isfile(hostfilepath):
				self.send_file(path, open(hostfilepath).read(), expect=expect, shutit_pexpect_child=shutit_pexpect_child, user=user, group=group,loglevel=loglevel, delaybeforesend=delaybeforesend)
			elif os.path.isdir(hostfilepath):
				self.send_host_dir(path, hostfilepath, expect=expect, shutit_pexpect_child=shutit_pexpect_child, user=user, group=group, loglevel=loglevel, delaybeforesend=delaybeforesend)
			else:
				self.fail('send_host_file - file: ' + hostfilepath + ' does not exist as file or dir. cwd is: ' + os.getcwd(), shutit_pexpect_child=shutit_pexpect_child, throw_exception=False)
		self._handle_note_after(note=note)


	def send_host_dir(self,
					  path,
					  hostfilepath,
					  expect=None,
					  shutit_pexpect_child=None,
	                  note=None,
	                  user=None,
	                  group=None,
	                  delaybeforesend=0,
	                  loglevel=logging.DEBUG):
		"""Send directory and all contents recursively from host machine to
		given path.  It will automatically make directories on the target.

		@param path:          Path to send directory to
		@param hostfilepath:  Path to file from host to send to target
		@param expect:        See send()
		@param shutit_pexpect_child:         See send()
		@param note:          See send()
		@param user:          Set ownership to this user (defaults to whoami)
		@param group:         Set group to this user (defaults to first group in groups)

		@type path:          string
		@type hostfilepath:  string
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		expect = expect or self.get_current_shutit_pexpect_session().default_expect
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		self._handle_note(note, 'Sending host directory: ' + hostfilepath + ' to target path: ' + path)
		self.log('Sending host directory: ' + hostfilepath + ' to: ' + path, level=logging.INFO)
		self.send(' mkdir -p ' + path, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
		if user == None:
			user = shutit_pexpect_session.whoami()
		if group == None:
			group = self.whoarewe()
		for root, subfolders, files in os.walk(hostfilepath):
			subfolders.sort()
			files.sort()
			for subfolder in subfolders:
				self.send(' mkdir -p ' + path + '/' + subfolder, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
				self.log('send_host_dir recursing to: ' + hostfilepath + '/' + subfolder, level=logging.DEBUG)
				self.send_host_dir(path + '/' + subfolder, hostfilepath + '/' + subfolder, expect=expect, shutit_pexpect_child=shutit_pexpect_child, loglevel=loglevel, delaybeforesend=delaybeforesend)
			for fname in files:
				hostfullfname = os.path.join(root, fname)
				targetfname = os.path.join(path, fname)
				self.log('send_host_dir sending file ' + hostfullfname + ' to ' + 'target file: ' + targetfname, level=logging.DEBUG)
				self.send_file(targetfname, open(hostfullfname).read(), expect=expect, shutit_pexpect_child=shutit_pexpect_child, user=user, group=group, loglevel=loglevel, delaybeforesend=delaybeforesend)
		self._handle_note_after(note=note)


	def file_exists(self,
	                filename,
	                shutit_pexpect_child=None,
	                directory=False,
	                note=None,
	                delaybeforesend=0,
	                loglevel=logging.DEBUG):
		"""Return True if file exists on the target host, else False

		@param filename:   Filename to determine the existence of.
		@param shutit_pexpect_child:      See send()
		@param directory:  Indicate that the file is a directory.
		@param note:       See send()

		@type filename:    string
		@type directory:   boolean

		@rtype: boolean
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.file_exists(filename=filename,directory=directory,note=note,delaybeforesend=delaybeforesend,loglevel=loglevel)


	def get_file_perms(self,
	                   filename,
	                   shutit_pexpect_child=None,
	                   note=None,
	                   delaybeforesend=0,
	                   loglevel=logging.DEBUG):
		"""Returns the permissions of the file on the target as an octal
		string triplet.

		@param filename:  Filename to get permissions of.
		@param shutit_pexpect_child:     See send()
		@param note:      See send()

		@type filename:   string

		@rtype:           string
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.get_file_perms(filename,note=note,delaybeforesend=delaybeforesend,loglevel=loglevel)



	# TODO: move to shutit_pexpect, pass through
	def remove_line_from_file(self,
							  line,
							  filename,
							  expect=None,
							  shutit_pexpect_child=None,
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
		@param expect:        See send()
		@param shutit_pexpect_child:         See send()
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
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		expect = expect or self.get_current_shutit_pexpect_session().default_expect
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		self._handle_note(note)
		# assume we're going to add it
		tmp_filename = '/tmp/' + shutit_util.random_id()
		if shutit_pexpect_session.file_exists(filename, expect=expect):
			if literal:
				if match_regexp == None:
					#            v the space is intentional, to avoid polluting bash history.
					self.send(""" grep -v '^""" + line + """$' """ + filename + ' > ' + tmp_filename, expect=expect, shutit_pexpect_child=shutit_pexpect_child, exit_values=['0', '1'], echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
				else:
					if not shutit_util.check_regexp(match_regexp):
						shutit.fail('Illegal regexp found in remove_line_from_file call: ' + match_regexp)
					#            v the space is intentional, to avoid polluting bash history.
					self.send(""" grep -v '^""" + match_regexp + """$' """ + filename + ' > ' + tmp_filename, expect=expect, shutit_pexpect_child=shutit_pexpect_child, exit_values=['0', '1'], echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
			else:
				if match_regexp == None:
					#          v the space is intentional, to avoid polluting bash history.
					self.send(' grep -v "^' + line + '$" ' + filename + ' > ' + tmp_filename, expect=expect, shutit_pexpect_child=shutit_pexpect_child, exit_values=['0', '1'], echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
				else:
					if not shutit_util.check_regexp(match_regexp):
						shutit.fail('Illegal regexp found in remove_line_from_file call: ' + match_regexp)
					#          v the space is intentional, to avoid polluting bash history.
					self.send(' grep -v "^' + match_regexp + '$" ' + filename + ' > ' + tmp_filename, expect=expect, shutit_pexpect_child=shutit_pexpect_child, exit_values=['0', '1'], echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
			self.send(' cat ' + tmp_filename + ' > ' + filename, expect=expect, shutit_pexpect_child=shutit_pexpect_child, check_exit=False, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
			self.send(' rm -f ' + tmp_filename, expect=expect, shutit_pexpect_child=shutit_pexpect_child, exit_values=['0', '1'], echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
		self._handle_note_after(note=note)
		return True


	# TODO: move to shutit_pexpect, pass through
	def change_text(self,
	                text,
	                fname,
	                pattern=None,
	                expect=None,
	                shutit_pexpect_child=None,
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
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		expect = expect or self.get_current_shutit_pexpect_session().default_expect
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		self._handle_note(note)
		fexists = self.file_exists(fname)
		if not fexists:
			if create:
				self.send(' touch ' + fname,expect=expect,shutit_pexpect_child=shutit_pexpect_child, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
			else:
				shutit.fail(fname + ' does not exist and create=False')
		if replace:
			# If replace and no pattern FAIL
			if not pattern:
				shutit.fail('replace=True requires a pattern to be passed in')
			# If replace and delete FAIL
			if delete:
				shutit.fail('cannot pass replace=True and delete=True to insert_text')
		if shutit_pexpect_session.command_available('base64'):
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
						shutit.fail('Illegal regexp found in change_text call: ' + pattern)
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
		self.send_file(fname,new_text,expect=expect,shutit_pexpect_child=shutit_pexpect_child,truncate=True,loglevel=loglevel, delaybeforesend=delaybeforesend)
		self._handle_note_after(note=note)
		return True


	# TODO: move to shutit_pexpect, pass through
	def insert_text(self, text, fname, pattern=None, expect=None, shutit_pexpect_child=None, before=False, force=False, note=None, replace=False, line_oriented=True, create=True, loglevel=logging.DEBUG):
		"""Insert a chunk of text at the end of a file, or after (or before) the first matching pattern
		in given file fname.
		See change_text"""
		self.change_text(text=text, fname=fname, pattern=pattern, expect=expect, shutit_pexpect_child=shutit_pexpect_child, before=before, force=force, note=note, line_oriented=line_oriented, create=create, replace=replace, delete=False, loglevel=loglevel)


	# TODO: move to shutit_pexpect, pass through
	def delete_text(self, text, fname, pattern=None, expect=None, shutit_pexpect_child=None, before=False, force=False, line_oriented=True, loglevel=logging.DEBUG):
		"""Delete a chunk of text from a file.
		See insert_text.
		"""
		return self.change_text(text, fname, pattern, expect, shutit_pexpect_child, before, force, delete=True, line_oriented=line_oriented, loglevel=loglevel)


	# TODO: move to shutit_pexpect, pass through
	def replace_text(self, text, fname, pattern=None, expect=None, shutit_pexpect_child=None, before=False, force=False, line_oriented=True, loglevel=logging.DEBUG):
		"""Replace a chunk of text from a file.
		See insert_text.
		"""
		return self.change_text(text, fname, pattern, expect, shutit_pexpect_child, before, force, line_oriented=line_oriented, replace=True, loglevel=loglevel)


	def add_line_to_file(self, line, filename, expect=None, shutit_pexpect_child=None, match_regexp=None, loglevel=logging.DEBUG):
		"""Deprecated.

		Use replace/insert_text instead.

		Adds line to file if it doesn't exist (unless Force is set, which it is not by default).
		Creates the file if it doesn't exist.
		Must be exactly the line passed in to match.
		Returns True if line(s) added OK, False if not.
		If you have a lot of non-unique lines to add, it's a good idea to have a sentinel value to add first, and then if that returns true, force the remainder.

		@param line:          Line to add. If a list, processed per-item, and match_regexp ignored.
		@param filename:      Filename to add it to.
		@param expect:        See send()
		@param shutit_pexpect_child:         See send()
		@param match_regexp:  If supplied, a regexp to look for in the file instead of the line itself, handy if the line has awkward characters in it.
		@param force:         Always write the line to the file.
		@param literal:       If true, then simply grep for the exact string without bash interpretation. (Default: False)
		@param note:          See send()

		@type line:           string
		@type filename:       string
		@type match_regexp:   string
		@type literal:        boolean

		"""
		if type(line) == str:
			lines = [line]
		elif type(line) == list:
			lines = line
			match_regexp = None
		fail = False
		for line in lines:
			if match_regexp == None:
				this_match_regexp = line
			else:
				this_match_regexp = match_regexp
			if not self.replace_text(line, filename, pattern=this_match_regexp, shutit_pexpect_child=shutit_pexpect_child, expect=expect, loglevel=loglevel):
				fail = True
		if fail:
			return False
		return True


	def add_to_bashrc(self, line, shutit_pexpect_child=None, match_regexp=None, note=None, loglevel=logging.DEBUG):
		"""Takes care of adding a line to everyone's bashrc
		(/etc/bash.bashrc, /etc/profile).

		@param line:          Line to add.
		@param shutit_pexpect_child:         See send()
		@param match_regexp:  See add_line_to_file()
		@param note:          See send()
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		shutit_pexpect_session.add_to_bashrc(line,match_regexp=match_regexp,note=note,loglevel=loglevel)


	def get_url(self,
	            filename,
	            locations,
	            command='curl',
	            shutit_pexpect_child=None,
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
		@param shutit_pexpect_child:                See send()
		@param timeout:              See send()
		@param fail_on_empty_before: See send()
		@param record_command:       See send()
		@param exit_values:          See send()
		@param echo:                 See send()
		@param retry:                How many times to retry the download
		                             in case of failure. Default: 3
		@param note:                 See send()

		@type filename:              string
		@type locations:             list of strings
		@type retry:                 integer

		@return: True if the download was completed successfully, False otherwise.
		@rtype: boolean
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.get_url(filename,locations,command=command,timeout=timeout,fail_on_empty_before=fail_on_empty_before,record_command=record_command,exit_values=exit_values,retry=retry,note=note,delaybeforesend=delaybeforesend,loglevel=loglevel)


	def user_exists(self,
	                user,
	                shutit_pexpect_child=None,
	                note=None,
	                delaybeforesend=0,
 	                loglevel=logging.DEBUG):
		"""Returns true if the specified username exists.
		
		@param user:   username to check for
		@param expect: See send()
		@param shutit_pexpect_child:  See send()
		@param note:   See send()

		@type user:    string

		@rtype:        boolean
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session(user,note=note,delaybeforesend=delaybeforesend,loglevel=loglevel)


	def package_installed(self,
	                      package,
	                      shutit_pexpect_child=None,
	                      note=None,
	                      delaybeforesend=0,
	                      loglevel=logging.DEBUG):
		"""Returns True if we can be sure the package is installed.

		@param package:   Package as a string, eg 'wget'.
		@param expect:    See send()
		@param shutit_pexpect_child:     See send()
		@param note:      See send()

		@rtype:           boolean
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session(package,note=note,delaybeforesend=delaybeforesend,loglevel=loglevel)



	def command_available(self,
	                      command,
	                      shutit_pexpect_child=None,
	                      note=None,
	                      delaybeforesend=0,
	                      loglevel=logging.DEBUG):
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.command_available(command,note=note,delaybeforesend=delaybeforesend,loglevel=loglevel)


	def is_shutit_installed(self,
	                        module_id,
	                        note=None,
	                        delaybeforesend=0,
	                        loglevel=logging.DEBUG):
		"""Helper proc to determine whether shutit has installed already here by placing a file in the db.
	
		@param module_id: Identifying string of shutit module
		@param note:      See send()
		"""
		shutit_pexpect_session = self.get_current_shutit_pexpect_session()
		return shutit_pexpect_session.is_shutit_installed(module_id,note=note,delaybeforesend=delaybeforesend,loglevel=loglevel)


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
		shutit_pexpect_session = self.get_current_shutit_pexpect_session()
		return shutit_pexpect_session.is_shutit_installed(directory,note=note,delaybeforesend=delaybeforesend,loglevel=loglevel)
		


	def get_file(self,
	             target_path,
	             host_path,
	             note=None,
	             delaybeforesend=0,
	             loglevel=logging.DEBUG):
		"""Copy a file from the target machine to the host machine

		@param target_path: path to file in the target
		@param host_path:   path to file on the host machine (e.g. copy test)
		@param note:        See send()

		@type target_path: string
		@type host_path:   string

		@return:           boolean
		@rtype:            string
		"""
		global cfg
		self._handle_note(note)
		# Only handle for docker initially, return false in case we care
		if cfg['build']['delivery'] != 'docker':
			return False
		# on the host, run:
		#Usage:  docker cp [OPTIONS] CONTAINER:PATH LOCALPATH|-
		# Need: host env, container id, path from and path to
		shutit_pexpect_child     = self.get_shutit_pexpect_session_from_id('host_child').pexpect_child
		expect    = cfg['expect_prompts']['origin_prompt']
		self.send('docker cp ' + cfg['target']['container_id'] + ':' + target_path + ' ' + host_path, shutit_pexpect_child=shutit_pexpect_child, expect=expect, check_exit=False, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
		self._handle_note_after(note=note)
		return True


	def prompt_cfg(self, msg, sec, name, ispass=False):
		"""Prompt for a config value, optionally saving it to the user-level
		cfg. Only runs if we are in an interactive mode.

		@param msg:    Message to display to user.
		@param sec:    Section of config to add to.
		@param name:   Config item name.
		@param ispass: If True, hide the input from the terminal.
		               Default: False.

		@type msg:     string
		@type sec:     string
		@type name:    string
		@type ispass:  boolean

		@return: the value entered by the user
		@rtype:  string
		"""
		global cfg
		cfgstr        = '[%s]/%s' % (sec, name)
		config_parser = cfg['config_parser']
		usercfg       = os.path.join(cfg['shutit_home'], 'config')

		self.log(shutit_util.colourise('32', '\nPROMPTING FOR CONFIG: %s' % (cfgstr,)),transient=True)
		self.log(shutit_util.colourise('32', '\n' + msg + '\n'),transient=True)
		
		if not shutit_util.determine_interactive():
			self.fail('ShutIt is not in a terminal so cannot prompt for values.', throw_exception=False)

		if config_parser.has_option(sec, name):
			whereset = config_parser.whereset(sec, name)
			if usercfg == whereset:
				self.fail(cfgstr + ' has already been set in the user config, edit ' + usercfg + ' directly to change it', throw_exception=False)
			for subcp, filename, _fp in reversed(config_parser.layers):
				# Is the config file loaded after the user config file?
				if filename == whereset:
					self.fail(cfgstr + ' is being set in ' + filename + ', unable to override on a user config level', throw_exception=False)
				elif filename == usercfg:
					break
		else:
			# The item is not currently set so we're fine to do so
			pass
		if ispass:
			val = getpass.getpass('>> ')
		else:
			val = shutit_util.util_raw_input(prompt='>> ')
		is_excluded = (
			config_parser.has_option('save_exclude', sec) and
			name in config_parser.get('save_exclude', sec).split()
		)
		# TODO: ideally we would remember the prompted config item for this invocation of shutit
		if not is_excluded:
			usercp = [
				subcp for subcp, filename, _fp in config_parser.layers
				if filename == usercfg
			][0]
			if shutit_util.util_raw_input(prompt=shutit_util.colourise('32', 'Do you want to save this to your user settings? y/n: '),default='y') == 'y':
				sec_toset, name_toset, val_toset = sec, name, val
			else:
				# Never save it
				if config_parser.has_option('save_exclude', sec):
					excluded = config_parser.get('save_exclude', sec).split()
				else:
					excluded = []
				excluded.append(name)
				excluded = ' '.join(excluded)
				sec_toset, name_toset, val_toset = 'save_exclude', sec, excluded
			if not usercp.has_section(sec_toset):
				usercp.add_section(sec_toset)
			usercp.set(sec_toset, name_toset, val_toset)
			usercp.write(open(usercfg, 'w'))
			config_parser.reload()
		return val


	def step_through(self, msg='', shutit_pexpect_child=None, level=1, print_input=True, value=True):
		"""Implements a step-through function, using pause_point.
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		if (not shutit_util.determine_interactive() or not cfg['build']['interactive'] or
			cfg['build']['interactive'] < level):
			return
		cfg['build']['step_through'] = value
		shutit_pexpect_session.pause_point(msg, print_input=print_input, level=level)


	def pause_point(self,
	                msg='SHUTIT PAUSE POINT',
	                shutit_pexpect_child=None,
	                print_input=True,
	                level=1,
	                resize=True,
	                colour='32',
	                default_msg=None,
	                wait=-1,
	                delaybeforesend=0):
		"""Inserts a pause in the build session, which allows the user to try
		things out before continuing. Ignored if we are not in an interactive
		mode, or the interactive level is less than the passed-in one.
		Designed to help debug the build, or drop to on failure so the
		situation can be debugged.

		@param msg:          Message to display to user on pause point.
		@param shutit_pexpect_child:        See send()
		@param print_input:  Whether to take input at this point (i.e. interact), or
		                     simply pause pending any input.
		                     Default: True
		@param level:        Minimum level to invoke the pause_point at.
		                     Default: 1
		@param resize:       If True, try to resize terminal.
		                     Default: False
		@param colour:       Colour to print message (typically 31 for red, 32 for green)
		@param default_msg:  Whether to print the standard blurb
		@param wait:         Wait a few seconds rather than for input

		@type msg:           string
		@type print_input:   boolean
		@type level:         integer
		@type resize:        boolean
		@type wait:          decimal

		@return:             True if pause point handled ok, else false
		"""
		global cfg
		if (not shutit_util.determine_interactive() or cfg['build']['interactive'] < 1 or
			cfg['build']['interactive'] < level):
			return
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		if shutit_pexpect_child:
			shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
			shutit_pexpect_session.pause_point(msg=msg,print_input=print_input,resize=resize,colour=colour,default_msg=default_msg,wait=wait,delaybeforesend=delaybeforesend)
		else:
			self.log(msg,level=logging.DEBUG)
			self.log('Nothing to interact with, so quitting to presumably the original shell',level=logging.DEBUG)
			shutit_util.handle_exit(exit_code=1)
		cfg['build']['ctrlc_stop'] = False
		return True



	def send_and_match_output(self,
	                          send,
	                          matches,
	                          shutit_pexpect_child=None,
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
		@param expect:   See send()
		@param shutit_pexpect_child:    See send()
		@param retry:    Number of times to retry command (default 3)
		@param strip:    Whether to strip output (defaults to True)
		@param note:     See send()

		@type send:      string
		@type matches:   list
		@type retry:     integer
		@type strip:     boolean
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.send_and_match_output(send,matches,retry=retry,strip=strip,note=note,echo=echo,delaybeforesend=delaybeforesend,loglevel=loglevel)


	def send_and_get_output(self,
	                        send,
	                        shutit_pexpect_child=None,
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
		@param shutit_pexpect_child:    See send()
		@param retry:    Number of times to retry command (default 3)
		@param strip:    Whether to strip output (defaults to True). Strips whitespace
		                 and ansi terminal codes
		@param note:     See send()
		@param echo:     See send()

		@type retry:     integer
		@type strip:     boolean
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.send_and_get_output(send,timeout=timeout,retry=retry,strip=strip,preserve_newline=preserve_newline,note=note,record_command=record_command,echo=echo,fail_on_empty_before=fail_on_empty_before,delaybeforesend=delaybeforesend,loglevel=loglevel)


	def install(self,
	            package,
	            shutit_pexpect_child=None,
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
		@param expect:     See send()
		@param shutit_pexpect_child:      See send()
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
		# If separated by spaces, install separately
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.install(package,options=options,timeout=timeout,force=force,check_exit=check_exit,reinstall=reinstall,note=note,delaybeforesend=delaybeforesend,loglevel=loglevel)


	def remove(self,
	           package,
	           shutit_pexpect_child=None,
	           options=None,
	           timeout=3600,
	           delaybeforesend=0,
	           note=None):
		"""Distro-independent remove function.
		Takes a package name and runs relevant remove function.

		@param package:  Package to remove, which is run through package_map.
		@param shutit_pexpect_child:    See send()
		@param options:  Dict of options to pass to the remove command,
		                 mapped by install_type.
		@param timeout:  See send(). Default: 3600
		@param note:     See send()

		@return: True if all ok (i.e. the package was successfully removed),
		         False otherwise.
		@rtype: boolean
		"""
		# If separated by spaces, remove separately
		if package.find(' ') != -1:
			for p in package.split(' '):
				self.install(p,shutit_pexpect_child=shutit_pexpect_child,options=options,timeout=timeout,note=note)
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.remove(package,options=options,timeout=timeout,delaybeforesend=delaybeforesend,note=note)


	def get_env_pass(self,
	                 user=None,
	                 msg=None,
	                 shutit_pexpect_child=None,
	                 note=None):
		"""Gets a password from the user if one is not already recorded for this environment.

		@param user:    username we are getting password for
		@param msg:     message to put out there
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.get_env_pass(user=user,msg=msg,note=note)


	def whoarewe(self,
	             shutit_pexpect_child=None,
	             note=None,
	             delaybeforesend=0,
	             loglevel=logging.DEBUG):
		"""Returns the current group.

		@param shutit_pexpect_child:    See send()
		@param expect:   See send()
		@param note:     See send()

		@return: the first group found
		@rtype: string
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.whoarewe(note=note,delaybeforesend=delaybeforesend,loglevel=loglevel)


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
		"""Logs user in on default child.
		"""
		shutit_pexpect_session = self.get_current_shutit_pexpect_session()
		shutit_pexpect_session.login(user=user,
		                             command=command,
		                             password=password,
		                             prompt_prefix=prompt_prefix,
		                             expect=expect,
		                             timeout=timeout,
		                             escape=escape,
		                             note=note,
		                             go_home=go_home,
		                             delaybeforesend=delaybeforesend,
		                             loglevel=loglevel)


	def logout(self,
	           expect=None,
	           command='exit',
	           note=None,
	           timeout=5,
	           delaybeforesend=0,
	           loglevel=logging.DEBUG):
		"""Logs the user out. Assumes that login has been called.
		If login has never been called, throw an error.

			@param expect:          See send()
			@param command:         Command to run to log out (default=exit)
			@param note:            See send()
		"""
		shutit_pexpect_session = self.get_current_shutit_pexpect_session()
		shutit_pexpect_session.logout(expect=expect,command=command,note=note,timeout=timeout,delaybeforesend=delaybeforesend,loglevel=loglevel)
	exit_shell = logout


	def get_input(self, msg, default='', valid=[], boolean=False, ispass=False, colour='32'):
		shutit_util.get_input(msg=msg,default=default,valid=valid,boolean=boolean,ispass=ispass,colour=colour)


	def get_memory(self,
	               shutit_pexpect_child=None,
	               delaybeforesend=0,
	               note=None):
		"""Returns memory available for use in k as an int"""
		global cfg
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.get_memory(delaybeforesend=delaybeforesend,note=note)

	
	def get_distro_info(self,
	                    environment_id,
	                    shutit_pexpect_child=None,
	                    delaybeforesend=0,
	                    loglevel=logging.DEBUG):
		"""Get information about which distro we are using, placing it in the cfg['environment'][environment_id] as a side effect.

		Fails if distro could not be determined.
		Should be called with the container is started up, and uses as core info
		as possible.

		Note: if the install type is apt, it issues the following:
		    - apt-get update
		    - apt-get install -y -qq lsb-release

		@param shutit_pexpect_child:       See send()
		@param container:   If True, we are in the container shell, otherwise we are gathering info about another shell. Defaults to True.

		@type container:    boolean
		"""
		global cfg
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		# TODO: environment_id should be within pexpect session object
		# TODO: logging within pexpect session
		shutit_pexpect_session.get_distro_info(environment_id, delaybeforesend=delaybeforesend,loglevel=loglevel)


	def lsb_release(self,
	                shutit_pexpect_child=None,
	                delaybeforesend=0,
	                loglevel=logging.DEBUG):
		"""Get distro information from lsb_release.
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.lsb_release(delaybeforesend=delaybeforesend,loglevel=loglevel)


	def set_password(self,
	                 password,
	                 user='',
	                 shutit_pexpect_child=None,
	                 delaybeforesend=0.05,
	                 note=None):
		"""Sets the password for the current user or passed-in user.

		As a side effect, installs the "password" package.

		@param user:        username to set the password for. Defaults to '' (i.e. current user)
		@param password:    password to set for the user
		@param shutit_pexpect_child:       See send()
		@param note:        See send()
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		# TODO: assume expect is default in session
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		shutit_pexpect_session.set_password(password,user=user,delaybeforesend=delaybeforesend,note=note)


	def is_user_id_available(self,
	                         user_id,
	                         shutit_pexpect_child=None,
	                         note=None,
	                         delaybeforesend=0,
	                         loglevel=logging.DEBUG):
		"""Determine whether the specified user_id available.

		@param user_id:  User id to be checked.
		@param expect:   See send()
		@param shutit_pexpect_child:    See send()
		@param note:     See send()

		@type user_id:   integer

		@rtype:          boolean
		@return:         True is the specified user id is not used yet, False if it's already been assigned to a user.
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.is_user_id_available(user_id,note=note,delaybeforesend=delaybeforesend,loglevel=loglevel)


	def push_repository(self,
	                    repository,
	                    docker_executable='docker',
	                    shutit_pexpect_child=None,
	                    expect=None,
	                    delaybeforesend=0.05,
	                    loglevel=logging.INFO):
		"""Pushes the repository.

		@param repository:          Repository to push.
		@param docker_executable:   Defaults to 'docker'
		@param expect:              See send()
		@param shutit_pexpect_child:               See send()

		@type repository:           string
		@type docker_executable:    string
		"""
		global cfg
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		expect = expect or self.get_current_shutit_pexpect_session().default_expect
		send = docker_executable + ' push ' + repository
		expect_list = ['Username', 'Password', 'Email', expect]
		timeout = 99999
		self.log('Running: ' + send,level=logging.DEBUG)
		res = self.send(send, expect=expect_list, shutit_pexpect_child=shutit_pexpect_child, timeout=timeout, check_exit=False, fail_on_empty_before=False, loglevel=loglevel,delaybeforesend=delaybeforesend)
		while True:
			if res == 3:
				break
			elif res == 0:
				res = self.send(cfg['repository']['user'], shutit_pexpect_child=shutit_pexpect_child, expect=expect_list, timeout=timeout, check_exit=False, fail_on_empty_before=False, loglevel=loglevel,delaybeforesend=delaybeforesend)
			elif res == 1:
				res = self.send(cfg['repository']['password'], shutit_pexpect_child=shutit_pexpect_child, expect=expect_list, timeout=timeout, check_exit=False, fail_on_empty_before=False,loglevel=loglevel,delaybeforesend=delaybeforesend)
			elif res == 2:
				res = self.send(cfg['repository']['email'], shutit_pexpect_child=shutit_pexpect_child, expect=expect_list, timeout=timeout, check_exit=False, fail_on_empty_before=False, loglevel=loglevel,delaybeforesend=delaybeforesend)



	def do_repository_work(self,
	                       repo_name,
	                       repo_tag=None,
	                       docker_executable='docker',
	                       password=None,
	                       force=None,
	                       delaybeforesend=0,
	                       loglevel=logging.DEBUG):
		"""Commit, tag, push, tar a docker container based on the configuration we have.

		@param repo_name:           Name of the repository.
		@param docker_executable:   Defaults to 'docker'
		@param password:
		@param force:

		@type repo_name:            string
		@type docker_executable:    string
		@type password:             string
		@type force:                boolean
		"""
		global cfg
		# TODO: make host and client configurable
		shutit_pexpect_session = self.get_current_shutit_pexpect_session()
		tag    = cfg['repository']['tag']
		push   = cfg['repository']['push']
		export = cfg['repository']['export']
		save   = cfg['repository']['save']
		if not (push or export or save or tag):
			# If we're forcing this, then tag as a minimum
			if force:
				tag = True
			else:
				return

		shutit_pexpect_child = self.get_shutit_pexpect_session_from_id('host_child').pexpect_child
		expect    = cfg['expect_prompts']['origin_prompt']
		server    = cfg['repository']['server']
		repo_user = cfg['repository']['user']
		repo_tag  = cfg['repository']['tag_name']

		if repo_user and repo_name:
			repository = '%s/%s' % (repo_user, repo_name)
			repository_tar = '%s%s' % (repo_user, repo_name)
		elif repo_user:
			repository = repository_tar = repo_user
		elif repo_name:
			repository = repository_tar = repo_name
		else:
			repository = repository_tar = ''

		if not repository:
			self.fail('Could not form valid repository name', shutit_pexpect_child=shutit_pexpect_child, throw_exception=False)
		if (export or save) and not repository_tar:
			self.fail('Could not form valid tar name', shutit_pexpect_child=shutit_pexpect_child, throw_exception=False)

		if server != '':
			repository = '%s/%s' % (server, repository)

		if cfg['build']['deps_only']:
			repo_tag += '_deps'

		if cfg['repository']['suffix_date']:
			suffix_date = time.strftime(cfg['repository']['suffix_format'])
			repository = '%s%s' % (repository, suffix_date)
			repository_tar = '%s%s' % (repository_tar, suffix_date)

		if repository != '':
			repository_with_tag = repository + ':' + repo_tag

		# Commit image
		# Only lower case accepted
		repository          = repository.lower()
		repository_with_tag = repository_with_tag.lower()

		if server == '' and len(repository) > 30 and push:
			self.fail("""repository name: '""" + repository + """' too long to push. If using suffix_date consider shortening, or consider adding "-s repository push no" to your arguments to prevent pushing.""", shutit_pexpect_child=shutit_pexpect_child, throw_exception=False)

		if self.send('SHUTIT_TMP_VAR=$(' + docker_executable + ' commit ' + cfg['target']['container_id'] + ')', expect=[expect,'assword'], shutit_pexpect_child=shutit_pexpect_child, timeout=99999, check_exit=False, loglevel=loglevel, delaybeforesend=delaybeforesend) == 1:
			self.send(cfg['host']['password'], expect=expect, check_exit=False, record_command=False, shutit_pexpect_child=shutit_pexpect_child, echo=False, loglevel=loglevel, delaybeforesend=delaybeforesend)
		# Tag image, force it by default
		cmd = docker_executable + ' tag -f $SHUTIT_TMP_VAR ' + repository_with_tag
		cfg['build']['report'] += '\nBuild tagged as: ' + repository_with_tag
		self.send(cmd, shutit_pexpect_child=shutit_pexpect_child, expect=expect, check_exit=False, echo=False, loglevel=loglevel,delaybeforesend=delaybeforesend)
		if export or save:
			shutit_pexpect_session.pause_point('We are now exporting the container to a bzipped tar file, as configured in\n[repository]\ntar:yes', print_input=False, level=3)
			if export:
				bzfile = (repository_tar + 'export.tar.bz2')
				self.log('Depositing bzip2 of exported container into ' + bzfile,level=logging.DEBUG)
				if self.send(docker_executable + ' export ' + cfg['target']['container_id'] + ' | bzip2 - > ' + bzfile, expect=[expect, 'assword'], timeout=99999, shutit_pexpect_child=shutit_pexpect_child, loglevel=loglevel, delaybeforesend=delaybeforesend) == 1:
					self.send(password, expect=expect, shutit_pexpect_child=shutit_pexpect_child, loglevel=loglevel, delaybeforesend=delaybeforesend)
				self.log('Deposited bzip2 of exported container into ' + bzfile, level=loglevel)
				self.log('Run: bunzip2 -c ' + bzfile + ' | sudo docker import - to get this imported into docker.', level=logging.DEBUG)
				cfg['build']['report'] += ('\nDeposited bzip2 of exported container into ' + bzfile)
				cfg['build']['report'] += ('\nRun:\n\nbunzip2 -c ' + bzfile + ' | sudo docker import -\n\nto get this imported into docker.')
			if save:
				bzfile = (repository_tar + 'save.tar.bz2')
				self.log('Depositing bzip2 of exported container into ' + bzfile,level=logging.DEBUG)
				if self.send(docker_executable + ' save ' + cfg['target']['container_id'] + ' | bzip2 - > ' + bzfile, expect=[expect, 'assword'], timeout=99999, shutit_pexpect_child=shutit_pexpect_child, loglevel=loglevel, delaybeforesend=delaybeforesend) == 1:
					self.send(password, expect=expect, shutit_pexpect_child=shutit_pexpect_child, loglevel=loglevel, delaybeforesend=delaybeforesend)
				self.log('Deposited bzip2 of exported container into ' + bzfile, level=logging.DEBUG)
				self.log('Run: bunzip2 -c ' + bzfile + ' | sudo docker import - to get this imported into docker.', level=logging.DEBUG)
				cfg['build']['report'] += ('\nDeposited bzip2 of exported container into ' + bzfile)
				cfg['build']['report'] += ('\nRun:\n\nbunzip2 -c ' + bzfile + ' | sudo docker import -\n\nto get this imported into docker.')
		if cfg['repository']['push']:
			# Pass the child explicitly as it's the host child.
			self.push_repository(repository, docker_executable=docker_executable, expect=expect, shutit_pexpect_child=shutit_pexpect_child)
			cfg['build']['report'] = (cfg['build']['report'] + '\nPushed repository: ' + repository)




	def get_config(self,
	               module_id,
	               option,
	               default=None,
	               boolean=False,
	               forcedefault=False,
	               forcenone=False,
	               hint=None):
		"""Gets a specific config from the config files, allowing for a default.

		Handles booleans vs strings appropriately.

		@param module_id:    module id this relates to, eg com.mycorp.mymodule.mymodule
		@param option:       config item to set
		@param default:      default value if not set in files
		@param boolean:      whether this is a boolean value or not (default False)
		@param forcedefault: if set to true, allows you to override any value already set (default False)
		@param forcenone:    if set to true, allows you to set the value to None (default False)
		@param hint:         if we are interactive, then show this prompt to help the user input a useful value

		@type module_id:     string
		@type option:        string
		@type default:       string
		@type boolean:       boolean
		@type forcedefault:  boolean
		@type forcenone:     boolean
		@type hint:          string
		"""
		if module_id not in cfg.keys():
			cfg[module_id] = {}
		if not cfg['config_parser'].has_section(module_id):
			cfg['config_parser'].add_section(module_id)
		if not forcedefault and cfg['config_parser'].has_option(module_id, option):
			if boolean:
				cfg[module_id][option] = cfg['config_parser'].getboolean(module_id, option)
			else:
				cfg[module_id][option] = cfg['config_parser'].get(module_id, option)
		else:
			if not forcenone:
				if cfg['build']['interactive'] > 0:
					if cfg['build']['accept_defaults'] == None:
						answer = None
						# util_raw_input may change the interactive level, so guard for this.
						while answer not in ('yes','no','') and cfg['build']['interactive'] > 1:
							answer = shutit_util.util_raw_input(prompt=shutit_util.colourise('32', 'Do you want to accept the config option defaults? ' + '(boolean - input "yes" or "no") (default: yes): \n'),default='yes')
						# util_raw_input may change the interactive level, so guard for this.
						if answer == 'yes' or answer == '' or cfg['build']['interactive'] < 2:
							cfg['build']['accept_defaults'] = True
						else:
							cfg['build']['accept_defaults'] = False
					if cfg['build']['accept_defaults'] and default != None:
						cfg[module_id][option] = default
					else:
						# util_raw_input may change the interactive level, so guard for this.
						if cfg['build']['interactive'] < 1:
							self.fail('Cannot continue. ' + module_id + '.' + option + ' config requires a value and no default is supplied. Adding "-s ' + module_id + ' ' + option + ' [your desired value]" to the shutit invocation will set this.')
						prompt = '\n\nPlease input a value for ' + module_id + '.' + option
						if default != None:
							prompt = prompt + ' (default: ' + str(default) + ')'
						if hint != None:
							prompt = prompt + '\n\n' + hint
						answer = None
						if boolean:
							while answer not in ('yes','no'):
								answer =  shutit_util.util_raw_input(prompt=shutit_util.colourise('32',prompt + ' (boolean - input "yes" or "no"): \n'))
							if answer == 'yes':
								answer = True
							elif answer == 'no':
								answer = False
						else:
							if re.search('assw',option) == None:
								answer =  shutit_util.util_raw_input(prompt=shutit_util.colourise('32',prompt) + ': \n')
							else:
								answer =  shutit_util.util_raw_input(ispass=True,prompt=shutit_util.colourise('32',prompt) + ': \n')
						if answer == '' and default != None:
							answer = default
						cfg[module_id][option] = answer
				else:
					if default != None:
						cfg[module_id][option] = default
					else:
						self.fail('Config item: ' + option + ':\nin module:\n[' + module_id + ']\nmust be set!\n\nOften this is a deliberate requirement to place in your ~/.shutit/config file, or you can pass in with:\n\n-s ' + module_id + ' ' + option + ' yourvalue\n\nto the build command', throw_exception=False)
			else:
				cfg[module_id][option] = default


	def get_emailer(self, cfg_section):
		"""Sends an email using the mailer
		"""
		from alerting import emailer
		return emailer.Emailer(cfg_section, self)


	# eg sys.stdout or None
	def divert_output(self, output):
		for key in self.shutit_pexpect_sessions.keys():
			self.shutit_pexpect_sessions[key].pexpect_child.logfile_send = output
			self.shutit_pexpect_sessions[key].pexpect_child.logfile_read = output


	def add_shutit_pexpect_session(self, shutit_pexpect_child):
		pexpect_session_id = shutit_pexpect_child.pexpect_sesssion_id
		# Check id is unique
		if self.shutit_pexpect_sessions.has_key(pexpect_session_id) and self.shutit_pexpect_sessions[pexpect_session_id] != shutit_pexpect_child:
			shutit.fail('shutit_pexpect_child already added and differs from passed-in object',throw_exception=True)
		self.shutit_pexpect_sessions.update({pexpect_session_id:shutit_pexpect_child})


	def remove_shutit_pexpect_session(self, shutit_pexpect_session_id=None, shutit_pexpect_child=None):
		if shutit_pexpect_session_id == None and shutit_pexpect_child == None:
			shutit.fail('Must pass value into remove_pexpect_child.',throw_exception=True)
		if shutit_pexpect_session_id == None:
			shutit_pexpect_session_id = shutit_pexpect_child.pexpect_session_id
		del self.shutit_pexpect_sessions[shutit_pexpect_session_id]

	
	def get_shutit_pexpect_session_from_child(self, shutit_pexpect_child):
		"""Given a pexpect/child object, return the shutit_pexpect_session object.
		"""
		if type(shutit_pexpect_child) != pexpect.pty_spawn.spawn:
			shutit.fail('Wrong type in get_shutit_pexpect_session_child: ' + str(type(shutit_pexpect_child)),throw_exception=True)
		#print '==================='
		#print shutit_pexpect_child
		#print self.shutit_pexpect_sessions
		for key in self.shutit_pexpect_sessions:
			#print key
			#print self.shutit_pexpect_sessions[key].pexpect_child
			#print shutit_pexpect_child
			if self.shutit_pexpect_sessions[key].pexpect_child == shutit_pexpect_child:
				return self.shutit_pexpect_sessions[key]
		shutit.fail('Should not get here in get_shutit_pexpect_session',throw_exception=True)

	def get_shutit_pexpect_session_id(self, shutit_pexpect_child):
		"""Given a pexpect child object, return the shutit_pexpect_session_id object.
		"""
		if type(shutit_pexpect_child) != pexpect.pty_spawn.spawn:
			shutit.fail('Wrong type in get_shutit_pexpect_session_id',throw_exception=True)
		for key in self.shutit_pexpect_sessions:
			if self.shutit_pexpect_sessions[key].pexpect_child == shutit_pexpect_child:
				return key
		shutit.fail('Should not get here in get_shutit_pexpect_session_id',throw_exception=True)

	def get_shutit_pexpect_session_from_id(self, shutit_pexpect_id):
		"""
		"""
		for key in self.shutit_pexpect_sessions:
			if self.shutit_pexpect_sessions[key].pexpect_session_id == shutit_pexpect_id:
				return self.shutit_pexpect_sessions[key]
		shutit.fail('Should not get here in get_shutit_pexpect_session_from_id',throw_exception=True)

def init():
	"""Initialize the shutit object. Called when imported.
	"""
	global shutit_pexpect_sessions
	global shutit_modules
	global shutit_main_dir
	global cfg
	global cwd
	global shutit_command_history
	global shutit_map
	global shutit

	current_shutit_pexpect_session = None
	shutit_pexpect_sessions      = {}
	shutit_map                   = {}
	shutit_modules               = set()
	shutit_command_history       = []
	# Store the root directory of this application.
	# http://stackoverflow.com/questions/5137497
	shutit_main_dir = os.path.abspath(os.path.dirname(__file__))
	cwd = os.getcwd()
	global cfg
	cfg = {}
	cfg['SHUTIT_SIGNAL']                  = {}
	cfg['action']                         = {}
	cfg['build']                          = {}
	cfg['build']['interactive']           = 1 # Default to true until we know otherwise
	cfg['build']['report']                = ''
	cfg['build']['report_final_messages'] = ''
	cfg['build']['loglevel']              = logging.INFO
	cfg['build']['completed']             = False
	cfg['build']['mount_docker']          = False
	cfg['build']['distro_override']       = ''
	# Whether to honour 'walkthrough' requests
	cfg['build']['walkthrough']           = False
	cfg['build']['walkthrough_wait']      = -1
	cfg['target']                         = {}
	cfg['environment']                    = {}
	cfg['host']                           = {}
	cfg['host']['shutit_path']            = sys.path[0]
	cfg['repository']                     = {}
	cfg['expect_prompts']                 = {}
	cfg['dockerfile']                     = {}
	cfg['list_modules']                   = {}
	cfg['list_configs']                   = {}
	cfg['list_deps']                      = {}

	# If no LOGNAME available,
	cfg['host']['username'] = os.environ.get('LOGNAME', '')
	if cfg['host']['username'] == '':
		try:
			if os.getlogin() != '':
				cfg['host']['username'] = os.getlogin()
		except Exception:
			cfg['host']['username'] = getpass.getuser()
		if cfg['host']['username'] == '':
			shutit.fail('LOGNAME not set in the environment, ' + 'and login unavailable in python; ' + 'please set to your username.', throw_exception=False)
	cfg['host']['real_user'] = os.environ.get('SUDO_USER', cfg['host']['username'])
	cfg['build']['shutit_state_dir_base'] = '/tmp/shutit_' + cfg['host']['username']
	cfg['build']['build_id'] = (socket.gethostname() + '_' + cfg['host']['real_user'] + '_' + str(time.time()) + '.' + str(datetime.datetime.now().microsecond))
	cfg['build']['shutit_state_dir']           = cfg['build']['shutit_state_dir_base'] + '/' + cfg['build']['build_id']
	cfg['build']['build_db_dir']               = cfg['build']['shutit_state_dir'] + '/build_db'

	return ShutIt(
		shutit_pexpect_sessions=shutit_pexpect_sessions,
		current_shutit_pexpect_session=current_shutit_pexpect_session,
		shutit_modules=shutit_modules,
		shutit_main_dir=shutit_main_dir,
		cfg=cfg,
		cwd=cwd,
		shutit_command_history=shutit_command_history,
		shutit_map=shutit_map
	)

shutit = init()

