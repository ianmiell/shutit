"""Contains all the core ShutIt methods and functionality.
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
import shutil
import socket
import time
import shutit_util
import string
import re
import textwrap
import base64
import getpass
import package_map
import datetime
import pexpect
from shutit_module import ShutItFailException

class ShutIt(object):
	"""ShutIt build class.
	Represents an instance of a ShutIt build with associated config.
	"""


	def __init__(self, **kwargs):
		"""Constructor.
		Sets up:

				- pexpect_children   - pexpect objects representing shell interactions
				- shutit_modules     - representation of loaded shutit modules
				- shutit_main_dir    - directory in which shutit is located
				- cfg                - dictionary of configuration of build
				- cwd                - working directory of build
				- shutit_map         - maps module_ids to module objects
		"""
		# These used to be in shutit_global, so we pass them in as args so
		# the original reference can be put in shutit_global
		self.pexpect_children       = kwargs['pexpect_children']
		self.shutit_modules         = kwargs['shutit_modules']
		self.shutit_main_dir        = kwargs['shutit_main_dir']
		self.cfg                    = kwargs['cfg']
		self.cwd                    = kwargs['cwd']
		self.shutit_command_history = kwargs['shutit_command_history']
		self.shutit_map             = kwargs['shutit_map']
		# These are new members we dont have to provide compaitibility for
		self.conn_modules = set()

		# Hidden attributes
		self._default_child      = [None]
		self._default_expect     = [None]
		self._default_check_exit = [None]


	def module_method_start(self):
		"""Gets called automatically by the metaclass decorator in
		shutit_module when a module method is called.
		This allows setting defaults for the 'scope' of a method.
		"""
		if self._default_child[-1] is not None:
			self._default_child.append(self._default_child[-1])
		if self._default_expect[-1] is not None:
			self._default_expect.append(self._default_expect[-1])
		if self._default_check_exit[-1] is not None:
			self._default_check_exit.append(self._default_check_exit[-1])


	def module_method_end(self):
		"""Gets called automatically by the metaclass decorator in
		shutit_module when a module method is finished.
		This allows setting defaults for the 'scope' of a method.
		"""
		if len(self._default_child) != 1:
			self._default_child.pop()
		if len(self._default_expect) != 1:
			self._default_expect.pop()
			self._default_check_exit.pop()


	def get_default_child(self):
		"""Returns the currently-set default pexpect child.

		@return: default pexpect child object
		"""
		if self._default_child == None:
			print 'Default child not set yet, exiting'
			sys.exit(1)
		if self._default_child[-1] is None:
			print '''Couldn't get default child'''
			sys.exit(1)
		return self._default_child[-1]


	def get_default_expect(self):
		"""Returns the currently-set default pexpect string (usually a prompt).

		@return: default pexpect string
		"""
		if self._default_expect[-1] is None:
			self.fail("Couldn't get default expect, quitting")
		return self._default_expect[-1]


	def get_default_check_exit(self):
		"""Returns default value of check_exit. See send method.

		@rtype:  boolean
		@return: Default check_exit value
		"""
		if self._default_check_exit[-1] is None:
			self.fail("Couldn't get default check exit")
		return self._default_check_exit[-1]


	def set_default_child(self, child):
		"""Sets the default pexpect child.

		@param child: pexpect child to set as default
		"""
		self._default_child[-1] = child


	def set_default_expect(self, expect=None, check_exit=True):
		"""Sets the default pexpect string (usually a prompt).
		Defaults to the configured root prompt if no
		argument is passed.

		@param expect: String to expect in the output
		@type expect: string
		@param check_exit: Whether to check the exit value of the command
		@type check_exit: boolean
		"""
		cfg = self.cfg
		if expect == None:
			expect = cfg['expect_prompts']['root']
		self._default_expect[-1] = expect
		self._default_check_exit[-1] = check_exit


	def fail(self, msg, child=None, throw_exception=False):
		"""Handles a failure, pausing if a pexpect child object is passed in.

		@param child: pexpect child to work on
		@param throw_exception: Whether to throw an exception.
		@type throw_exception: boolean
		"""
		# Note: we must not default to a child here
		if child is not None:
			self.pause_point('Pause point on fail: ' + msg, child=child, colour='31')
		print >> sys.stderr, 'Error caught: ' + msg
		print >> sys.stderr
		if throw_exception:
			if shutit_util.determine_interactive(self):
				self.pause_point('FAIL: ' + msg)
			else:
				raise ShutItFailException(msg)
		else:
			# This is an "OK" failure, ie we don't need to throw an exception.
			# However, it's still a failure, so return 1
			if shutit_util.determine_interactive(self):
				self.pause_point('FAIL: ' + msg)
			else:
				print msg
				print 'Error seen, exiting with status 1'
				sys.exit(1)


	def log(self, msg, code=None, pause=0, prefix=True, force_stdout=False, add_final_message=False):
		"""Logging function.

		@param code:              Colour code for logging. Ignored if we are in serve mode
		@param pause:             Length of time to pause after logging
		@param prefix:            Whether to output logging prefix (LOG: <time>)
		@param force_stdout:      If we are not in debug, put this in stdout anyway
		@param add_final_message: Add this log line to the final message output to the user
		"""
		cfg = self.cfg
		if prefix:
			prefix = 'LOG: ' + time.strftime("%Y-%m-%d %H:%M:%S", 
				time.localtime())
			logmsg = prefix + ' ' + str(msg)
		else:
			logmsg = msg
		# Don't colour message if we are in serve mode.
		if code != None and not cfg['action']['serve']:
			logmsg = shutit_util.colour(code, logmsg)
		if cfg['build']['debug'] or force_stdout:
			print >> sys.stdout, logmsg
			sys.stdout.flush()
		if cfg['build']['build_log'] and cfg['build']['build_log_file'] != None:
			print >> cfg['build']['build_log_file'], logmsg
			cfg['build']['build_log_file'].flush()
		if add_final_message:
			cfg['build']['report_final_messages'] += msg + '\n'
		time.sleep(pause)



	def setup_environment(self, prefix, expect=None, child=None):
		"""If we are in a new environment then set up a new data structure.
		A new environment is a new machine environment, whether that's
		over ssh, docker, whatever.
		If we are not in a new environment ensure the env_id is correct.
		Returns the environment id every time.
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		cfg = self.cfg
		environment_id_dir = cfg['build']['shutit_state_dir'] + '/environment_id'
		if self.file_exists(environment_id_dir,expect=expect,child=child,directory=True):
			files = self.ls(environment_id_dir)
			if len(files) != 1 or type(files) != list:
				if len(files) == 2 and (files[0] == 'ORIGIN_ENV' or files[1] == 'ORIGIN_ENV'):
					for f in files:
						if f != 'ORIGIN_ENV':
							environment_id = f
							cfg['build']['current_environment_id'] = environment_id
							break
				else:
					self.fail('Wrong number of files in environment_id_dir: ' + environment_id_dir)
			else:
				environment_id = files[0]
			if cfg['build']['current_environment_id'] != environment_id:
				# Clean out any trace of this new environment, and return the already-existing one.
				self.send('rm -rf ' + environment_id_dir + '/environment_id/' + environment_id, child=child, expect=expect)
				return cfg['build']['current_environment_id']
			if not environment_id == 'ORIGIN_ENV':
				return environment_id
		# Root is a special case
		if prefix == 'ORIGIN_ENV':
			environment_id = prefix
		else:
			environment_id = shutit_util.random_id()
		cfg['build']['current_environment_id']                             = environment_id
		cfg['environment'][environment_id] = {}
		# Directory to revert to when delivering in bash and reversion to context required.
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
			self.get_distro_info(environment_id)
		self.send('mkdir -p ' + environment_id_dir, child=child, expect=expect)
		self.send('chmod -R 777 ' + cfg['build']['shutit_state_dir_base'])
		fname = environment_id_dir + '/' + environment_id
		self.send('touch ' + fname, child=child, expect=expect)
		cfg['environment'][environment_id]['setup']                        = True
		return environment_id

	def get_current_environment(self):
		cfg = self.cfg
		return cfg['environment'][cfg['build']['current_environment_id']]



	def multisend(self,
	              send,
	              send_dict,
	              expect=None,
	              child=None,
	              timeout=3600,
	              check_exit=None,
	              fail_on_empty_before=True,
	              record_command=True,
	              exit_values=None,
	              escape=False,
	              echo=None,
	              note=None):
		"""Multisend. Same as send, except it takes multiple sends and expects in a dict that are
		processed while waiting for the end "expect" argument supplied.

		@param send_dict:            dict of sends and expects, eg: {'interim prompt:','some input','other prompt','some other input'}
		@param expect:               String or list of strings of final expected output that returns from this function. See send()
		@param send:                 See send()
		@param child:                See send()
		@param timeout:              See send()
		@param check_exit:           See send()
		@param fail_on_empty_before: See send()
		@param record_command:       See send()
		@param exit_values:          See send()
		@param echo:                 See send()
		@param note:                 See send()
		"""
		expect = expect or self.get_default_expect()
		child = child or self.get_default_child()
		self._handle_note(note)
		
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
			res = self.send(send_iteration, expect=expect_list, child=child, check_exit=check_exit, fail_on_empty_before=fail_on_empty_before, timeout=timeout, record_command=record_command, exit_values=exit_values, echo=echo, escape=escape)
			if res >= len(expect_list) - n_breakout_items:
				break
			else:
				send_iteration = send_dict[expect_list[res]]


	def send_until(self,
	               send,
	               regexps,
	               not_there=False,
	               expect=None,
	               child=None,
	               cadence=5,
	               retries=100,
	               fail_on_empty_before=True,
	               record_command=True,
	               echo=False,
	               escape=False,
	               note=None):
		"""Send string on a regular cadence until a string is either seen

		@param send:                 See send()
		@param regexps:              List of regexps to wait for.
		@param not_there:            If True, wait until this a regexp is not seen in the output. If False
		                             wait until a regexp is seen in the output (default)
		@param expect:               See send()
		@param child:                See send()
		@param timeout:              See send()
		@param check_exit:           See send()
		@param fail_on_empty_before: See send()
		@param record_command:       See send()
		@param exit_values:          See send()
		@param echo:                 See send()
		@param note:                 See send()
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		cfg = self.cfg
		self._handle_note(note, 'Command: ' + send + '\nUntil one of these seen:' + str(regexps))
		if type(regexps) == str:
			regexps = [regexps]
		if type(regexps) != list:
			self.fail('regexps should be list')
		while retries > 0:
			retries -= 1
			output = self.send_and_get_output(send, expect=expect, child=child, retry=1, strip=True)
			if not not_there:
				for regexp in regexps:
					if not shutit_util.check_regexp(regexp):
						shutit.fail('Illegal regexp found in send_until call: ' + regexp)
					if self.match_string(output, regexp):
						return True
			else:
				# Only return if _not_ seen in the output
				missing = False
				for regexp in regexps:
					if not shutit_util.check_regexp(regexp):
						shutit.fail('Illegal regexp found in send_until call: ' + regexp)
					if not self.match_string(output, regexp):
						missing = True
						break
				if missing:
					return True
			time.sleep(cadence)
		return False

	         
  
	def send(self,
	         send,
	         expect=None,
	         child=None,
	         timeout=None,
	         check_exit=None,
	         fail_on_empty_before=True,
	         record_command=True,
	         exit_values=None,
	         echo=False,
	         escape=False,
	         retry=3,
	         note=None,
	         assume_gnu=True):
		"""Send string as a shell command, and wait until the expected output
		is seen (either a string or any from a list of strings) before
		returning. The expected string will default to the currently-set
		default expected string (see get_default_expect)

		Returns the pexpect return value (ie which expected string in the list
		matched)

		@param send: String to send, ie the command being issued. If set to None, we consume up to the expect string, which is useful if we just matched output that came before a standard command that returns to the prompt.
		@param expect: String that we expect to see in the output. Usually a prompt. Defaults to currently-set expect string (see set_default_expect)
		@param child: pexpect child to issue command to.
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
		if type(expect) == dict:
			return self.multisend(send=send,send_dict=expect,expect=self.get_default_expect(),child=child,timeout=timeout,check_exit=check_exit,fail_on_empty_before=fail_on_empty_before,record_command=record_command,exit_values=exit_values,echo=echo,note=note)
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		cfg = self.cfg
		self._handle_note(note, 'Command is: ' + str(send))
		if timeout == None:
			timeout = 3600

		# Handle OSX to get the GNU version of the command
		if assume_gnu:
			send = self._get_send_command(send)

			
		# If check_exit is not passed in
		# - if the expect matches the default, use the default check exit
		# - otherwise, default to doing the check
		if check_exit == None:
			if expect == self.get_default_expect():
				check_exit = self.get_default_check_exit()
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
		if echo == False and record_command == None:
			record_command = False
		if record_command == None or record_command:
			ok_to_record = True
			for i in cfg.keys():
				if isinstance(cfg[i], dict):
					for j in cfg[i].keys():
						if ((j == 'password' or j == 'passphrase') 
								and cfg[i][j] == send):
							self.shutit_command_history.append \
								('#redacted command, password')
							ok_to_record = False
							break
					if not ok_to_record:
						break
			if ok_to_record:
				self.shutit_command_history.append(send)
		if cfg['build']['debug'] and send != None:
			self.log('===================================================' + 
				'=============================',code=32)
			self.log('Sending>>>' + send + '<<<',code=31)
			self.log('Expecting>>>' + str(expect) + '<<<',code=32)
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
				self.log('\nThis string was sent safely: ' + send, force_stdout=True)
			if echo == False:
				oldlog = child.logfile_send
				child.logfile_send = None
				if escape:
					# 'None' escaped_str's are possible from multisends with nothing to send.
					if escaped_str != None:
						if len(escaped_str) + 25 > cfg['build']['stty_cols']:
							fname = self._create_command_file(child,expect,escaped_str,timeout)
							res = self.send(fname,expect=expect,child=child,timeout=timeout,check_exit=check_exit,fail_on_empty_before=False,record_command=False,exit_values=exit_values,echo=echo,escape=False,retry=retry)
							child.sendline('rm -f ' + fname)
							child.expect(expect)
							return res
						else:
							child.sendline(escaped_str)
							expect_res = self._expect_allow_interrupt(child, expect, timeout)
					else:
						expect_res = self._expect_allow_interrupt(child, expect, timeout)
				else:
					if send != None:
						if len(send) + 25 > cfg['build']['stty_cols']:
							fname = self._create_command_file(child,expect,send,timeout)
							res = self.send(fname,expect=expect,child=child,timeout=timeout,check_exit=check_exit,fail_on_empty_before=False,record_command=False,exit_values=exit_values,echo=echo,escape=False,retry=retry)
							child.sendline('rm -f ' + fname)
							child.expect(expect)
							return res
						else:
							child.sendline(send)
							expect_res = self._expect_allow_interrupt(child, expect, timeout)
					else:
						expect_res = self._expect_allow_interrupt(child, expect, timeout)
				child.logfile_send = oldlog
			else:
				if escape:
					if escaped_str != None:
						if len(escaped_str) + 25 > cfg['build']['stty_cols']:
							fname = self._create_command_file(child,expect,escaped_str,timeout)
							res = self.send(fname,expect=expect,child=child,timeout=timeout,check_exit=check_exit,fail_on_empty_before=False,record_command=False,exit_values=exit_values,echo=echo,escape=False,retry=retry)
							child.sendline('rm -f ' + fname)
							child.expect(expect)
							return res
						else:
							child.sendline(escaped_str)
							expect_res = self._expect_allow_interrupt(child, expect, timeout)
					else:
						expect_res = self._expect_allow_interrupt(child, expect, timeout)
				else:
					if send != None:
						if len(send) + 25 > cfg['build']['stty_cols']:
							fname = self._create_command_file(child,expect,send,timeout)
							res = self.send(fname,expect=expect,child=child,timeout=timeout,check_exit=check_exit,fail_on_empty_before=False,record_command=False,exit_values=exit_values,echo=echo,escape=False,retry=retry)
							child.sendline('rm -f ' + fname)
							child.expect(expect)
							return res
						else:
							child.sendline(send)
							expect_res = self._expect_allow_interrupt(child, expect, timeout)
					else:
						expect_res = self._expect_allow_interrupt(child, expect, timeout)
			if cfg['build']['debug']:
				self.log('\nchild.before>>>' + child.before + '<<<',code=31)
				self.log('\nchild.after>>>' + child.after + '<<<',code=32)
			if fail_on_empty_before == True:
				if child.before.strip() == '':
					self.fail('before empty after sending: ' + str(send) +
						'\n\nThis is expected after some commands that take a ' + 
						'password.\nIf so, add fail_on_empty_before=False to ' + 
						'the send call.\n\nIf that is not the problem, did you ' +
				        'send an empty string to a prompt by mistake?', child=child)
			elif fail_on_empty_before == False:
				# Don't check exit if fail_on_empty_before is False
				self.log('' + child.before + '<<<')
				check_exit = False
				for prompt in cfg['expect_prompts']:
					if prompt == expect:
						# Reset prompt
						self.setup_prompt('reset_tmp_prompt', child=child)
						self.revert_prompt('reset_tmp_prompt', expect,
							child=child)
			# Last output - remove the first line, as it is the previous command.
			cfg['build']['last_output'] = '\n'.join(child.before.split('\n')[1:])
			if check_exit == True:
				# store the output
				if not self._check_exit(send, expect, child, timeout, exit_values, retry=retry):
					self.log('Sending: ' + send + '\nfailed, retrying')
					retry = retry - 1
					assert(retry > 0)
					continue
			break
		if cfg['build']['step_through']:
			self.pause_point('pause point: stepping through')
		if cfg['build']['ctrlc_stop']:
			cfg['build']['ctrlc_stop'] = False
			self.pause_point('pause point: interrupted by CTRL-c')
		return expect_res
	# alias send to send_and_expect
	send_and_expect = send

	
	def _get_send_command(self, send):
		"""Internal helper function to get command that's really sent"""
		if send == None:
			return send
		cmd_arr = send.split()
		if len(cmd_arr) and cmd_arr[0] in ('md5sum','sed','head'):
			cmd = self._get_command(cmd_arr[0])
			send = string.join(cmd + send[len(cmd_arr[0]):],'')
		return send

	def _handle_note(self, note, append=''):
		"""Handle notes and walkthrough option.

		@param note:                 See send()
		"""
		if self.cfg['build']['walkthrough'] and note != None:
			self.pause_point('\n' + 80*'=' + '\n' + note + '\n' + 80*'=' +
			                 '\n\n' + append + '\n', colour=31)


	def _expect_allow_interrupt(self, child, expect, timeout, iteration_s=1):
		"""This function allows you to interrupt the run at more or less any 
		point by breaking up the timeout into interative chunks.
		"""
		accum_timeout = 0
		# For testing
		#timeout = 1
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
			res = child.expect(expect + [pexpect.TIMEOUT], timeout=iteration_s)
			if res == len(expect):
				if shutit.cfg['build']['ctrlc_stop']:
					timed_out = False
					shutit.cfg['build']['crtlc_stop'] = False
					break
				accum_timeout += iteration_s
			else:
				return res
		if timed_out == True and not shutit_util.determine_interactive(self):
			self.log('\nCommand timed out, trying to get terminal back for you',code=31,force_stdout=True)
			self.fail('Timed out and could not recover')
		else:
			if shutit_util.determine_interactive(self):
				child.send('\x03')
				res = child.expect(expect + [pexpect.TIMEOUT],timeout=1)
				if res == len(expect):
					child.send('\x1a')
					res = child.expect(expect + [pexpect.TIMEOUT],timeout=1)
					if res == len(expect):
						self.fail('CTRL-C sent by ShutIt following a timeout, and could not recover')
				self.pause_point('CTRL-C sent by ShutIt following a timeout; the command has been cancelled',child=child)
				return res
			else:
				if timed_out:
					self.fail('Timed out and interactive, but could not recover')
				else:
					self.fail('CTRL-C hit and could not recover')
		self.fail('Should not get here (_expect_allow_interrupt)')


	def _get_command(self, command):
		cfg = self.cfg
		if command in ('head','md5sum'):
			if cfg['environment'][cfg['build']['current_environment_id']]['distro'] == 'osx':
				return '''PATH="/usr/local/opt/coreutils/libexec/gnubin:$PATH" ''' + command + ' '
			else:
				return command + ' '
		return command


	def _create_command_file(self, child, expect, send, timeout):
		"""Internal function. Do not use.

		Takes a long command, and puts it in an executable file ready to run. Returns the filename.
		"""
		cfg = self.cfg
		random_id = shutit_util.random_id()
		fname = cfg['build']['shutit_state_dir_base'] + '/tmp_' + random_id
		working_str = send
		child.sendline('truncate --size 0 '+ fname)
		child.expect(expect)
		size = cfg['build']['stty_cols'] - 25
		while len(working_str) > 0:
			curr_str = working_str[:size]
			working_str = working_str[size:]
			child.sendline(self._get_command('head') + ''' -c -1 >> ''' + fname + """ << 'END_""" + random_id + """'
""" + curr_str + """
END_""" + random_id)
			child.expect(expect)
		child.sendline('chmod +x ' + fname)
		child.expect(expect)
		return fname
		

	def _check_exit(self,
	                send,
	                expect=None,
	                child=None,
	                timeout=3600,
	                exit_values=None,
	                retry=0,
	                retbool=False):
		"""Internal function to check the exit value of the shell. Do not use.
		"""
		cfg = self.cfg
		if cfg['build']['check_exit'] == False:
			self.log('check_exit configured off, returning')
			return
		expect = expect or self.get_default_expect()
		child = child or self.get_default_child()
		if exit_values is None:
			exit_values = ['0']
		# Don't use send here (will mess up last_output)!
		# Space before "echo" here is sic - we don't need this to show up in bash history
		child.sendline(' echo EXIT_CODE:$?')
		child.expect(expect)
		res = self.match_string(child.before, 
			'^EXIT_CODE:([0-9][0-9]?[0-9]?)$')
		if res == None:
			# Try after - for some reason needed after login
			res = self.match_string(child.after, 
				'^EXIT_CODE:([0-9][0-9]?[0-9]?)$')
		if res not in exit_values or res == None:
			if res == None:
				res = str(res)
			self.log('child.after: \n' + child.after + '\n')
			self.log('Exit value from command:\n' + str(send) + '\nwas:\n' + res)
			msg = ('\nWARNING: command:\n' + send + 
				  '\nreturned unaccepted exit code: ' + 
				  res + 
				  '\nIf this is expected, pass in check_exit=False or ' + 
				  'an exit_values array into the send function call.')
			cfg['build']['report'] = cfg['build']['report'] + msg
			if retbool:
				return False
			elif cfg['build']['interactive'] >= 1:
				# This is a failure, so we pass in level=0
				self.pause_point(msg + '\n\nInteractive, so not retrying.\nPause point on exit_code != 0 (' +
					res + '). CTRL-C to quit', child=child, level=0)
			elif retry == 1:
				self.fail('Exit value from command\n' + send +
				    '\nwas:\n' + res, throw_exception=False)
			else:
				return False
		return True


	def run_script(self, script, expect=None, child=None, in_shell=True, note=None):
		"""Run the passed-in string as a script on the target's command line.

		@param script:   String representing the script. It will be de-indented
						 and stripped before being run.
		@param expect:   See send()
		@param child:    See send()
		@param in_shell: Indicate whether we are in a shell or not. (Default: True)
		@param note:     See send()

		@type script:    string
		@type in_shell:  boolean
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
	 	cfg = self.cfg
		self._handle_note(note, 'Script: ' + str(script))
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
		self.send('mkdir -p ' + cfg['build']['shutit_state_dir'] + '/scripts', expect, child)
		self.send('chmod 777 ' + cfg['build']['shutit_state_dir'] + '/scripts', expect, child)
		self.send_file(cfg['build']['shutit_state_dir'] + '/scripts/shutit_script.sh', script)
		self.send('chmod +x ' + cfg['build']['shutit_state_dir'] + '/scripts/shutit_script.sh', expect, child)
		self.shutit_command_history.append\
			('    ' + script.replace('\n', '\n    '))
		if in_shell:
			ret = self.send('. ' + cfg['build']['shutit_state_dir'] + '/scripts/shutit_script.sh', expect, child)
		else:
			ret = self.send(cfg['build']['shutit_state_dir'] + '/scripts/shutit_script.sh', expect, child)
		self.send('rm -f ' + cfg['build']['shutit_state_dir'] + '/scripts/shutit_script.sh', expect, child)
		return ret


	def send_file(self, path, contents, expect=None, child=None, log=True, truncate=False, note=None, user=None, group=None):
		"""Sends the passed-in string as a file to the passed-in path on the
		target.

		@param path:        Target location of file on target.
		@param contents:    Contents of file as a string. See log.
		@param expect:      See send()
		@param child:       See send()
		@param log:         Log the file contents if in debug.
		@param note:        See send()
		@param user:        Set ownership to this user (defaults to whoami)
		@param group:       Set group to this user (defaults to first group in groups)

		@type path:         string
		@type contents:     string
		@type log:          boolean
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		cfg = self.cfg
		self._handle_note(note, 'Sending contents to path: ' + path)
		if user == None:
			user = self.whoami()
		if group == None:
			group = self.whoarewe()
		if cfg['build']['debug']:
			self.log('='*80)
			self.log('Sending file to' + path)
			if log:
				for c in contents:
					if c not in string.ascii_letters:
						print_contents = string.replace(contents,c,'?')
				self.log('contents >>>' + print_contents + '<<<')
		if cfg['build']['current_environment_id'] == 'ORIGIN_ENV':
			# If we're on the root env (ie the same one that python is running on,
			# then use python.
			f = open(path,'w')
			if truncate:
				f.truncate(0)
			f.write(contents)
			f.close()
		elif cfg['build']['delivery'] in ('bash','dockerfile'):
			if truncate and self.file_exists(path):
				self.send('rm -f ' + path, expect=expect, child=child)
			random_id = shutit_util.random_id()
			# switch off tab-completion
			self.send('''bind '\C-i:self-insert' ''',check_exit=False)
			# TODO: BUG: blows up when the contents are large.
			self.send(self._get_command('head') + ' -c -1 > ' + path + " << 'END_" + random_id + """'
""" + contents + '''
END_''' + random_id)
			# switch back on tab-completion
			# this makes the assumption that tab-completion was on.
			self.send('''bind '\C-i:complete' ''',check_exit=False)
		else:
			host_child = self.pexpect_children['host_child']
			path = path.replace(' ', '\ ')
			# get host session
			tmpfile = cfg['build']['shutit_state_dir_base'] + 'tmp_' + shutit_util.random_id()
			f = open(tmpfile,'w')
			f.truncate(0)
			f.write(contents)
			f.close()
			# Create file so it has appropriate permissions
			self.send('touch ' + path, child=child, expect=expect)
			self.send('cat ' + tmpfile + ' | ' + cfg['host']['docker_executable'] + ' exec -i ' + cfg['target']['container_id'] + " bash -c 'cat > " + path + "'", child=host_child, expect=cfg['expect_prompts']['origin_prompt'])
			self.send('chown ' + user + ' ' + path, child=child, expect=expect)
			self.send('chgrp ' + group + ' ' + path, child=child, expect=expect)
			os.remove(tmpfile)


	def chdir(self,
	          path,
	          expect=None,
	          child=None,
	          timeout=3600,
	          log=True,
	          note=None):
		"""How to change directory will depend on whether we are in delivery mode bash or docker.

		@param path:          Path to send file to.
		@param expect:        See send()
		@param child:         See send()
		@param timeout:       Timeout on response
		@param log:           Arg to pass to send_file (default True)
		@param note:          See send()
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		cfg = self.cfg
		self._handle_note(note, 'Changing to path: ' + path)
		if cfg['build']['delivery'] in ('bash','dockerfile'):
			self.send('cd ' + path, expect=expect, child=child, timeout=timeout)
		elif cfg['build']['delivery'] in ('docker','ssh'):
			os.chdir(path)
		else:
			self.fail('chdir not supported for delivery method: ' + cfg['build']['delivery'])


	def send_host_file(self,
	                   path,
	                   hostfilepath,
	                   expect=None,
	                   child=None,
	                   timeout=3600,
	                   log=True,
	                   note=None,
	                   user=None,
	                   group=None):
		"""Send file from host machine to given path

		@param path:          Path to send file to.
		@param hostfilepath:  Path to file from host to send to target.
		@param expect:        See send()
		@param child:         See send()
		@param log:           arg to pass to send_file (default True)
		@param note:          See send()
		@param user:          Set ownership to this user (defaults to whoami)
		@param group:         Set group to this user (defaults to first group in groups)

		@type path:           string
		@type hostfilepath:   string
		@type log:            boolean
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		cfg = self.cfg
		self._handle_note(note, 'Sending file from host: ' + hostfilepath + '\nTo: ' + path)
		if user == None:
			user = self.whoami()
		if group == None:
			group = self.whoarewe()
		if cfg['build']['delivery'] in ('bash','dockerfile'):
			self.send('pushd ' + cfg['environment'][cfg['build']['current_environment_id']]['module_root_dir'])
			self.send('cp -r ' + hostfilepath + ' ' + path,expect=expect, child=child, timeout=timeout)
			self.send('chown ' + user + ' ' + hostfilepath + ' ' + path,expect=expect, child=child, timeout=timeout)
			self.send('chgrp ' + group + ' ' + hostfilepath + ' ' + path,expect=expect, child=child, timeout=timeout)
			self.send('popd', expect=expect, child=child, timeout=timeout)
		else:
			if os.path.isfile(hostfilepath):
				self.send_file(path, open(hostfilepath).read(), expect=expect, 
					child=child, log=log, user=user, group=group)
			elif os.path.isdir(hostfilepath):
				self.send_host_dir(path, hostfilepath, expect=expect,
					child=child, log=log, user=user, group=group)
			else:
				self.fail('send_host_file - file: ' + hostfilepath +
					' does not exist as file or dir. cwd is: ' + os.getcwd(),
					child=child, throw_exception=False)


	def send_host_dir(self,
					  path,
					  hostfilepath,
					  expect=None,
					  child=None,
					  log=True,
	                  note=None,
	                  user=None,
	                  group=None):
		"""Send directory and all contents recursively from host machine to
		given path.  It will automatically make directories on the target.

		@param path:          Path to send directory to
		@param hostfilepath:  Path to file from host to send to target
		@param expect:        See send()
		@param child:         See send()
		@param log:           Arg to pass to send_file (default True)
		@param note:          See send()
		@param user:          Set ownership to this user (defaults to whoami)
		@param group:         Set group to this user (defaults to first group in groups)

		@type path:          string
		@type hostfilepath:  string
		@type log:           boolean
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self.log('entered send_host_dir in: ' + os.getcwd())
		self._handle_note(note, 'Sending host directory: ' + hostfilepath + '\nTo: ' + path)
		if user == None:
			user = self.whoami()
		if group == None:
			group = self.whoarewe()
		for root, subfolders, files in os.walk(hostfilepath):
			subfolders.sort()
			files.sort()
			for subfolder in subfolders:
				self.send('mkdir -p ' + path + '/' + subfolder)
				self.log('send_host_dir recursing to: ' + hostfilepath +
					'/' + subfolder)
				self.send_host_dir(path + '/' + subfolder, hostfilepath +
					'/' + subfolder, expect=expect, child=child, log=log)
			for fname in files:
				hostfullfname = os.path.join(root, fname)
				targetfname = os.path.join(path, fname)
				self.log('send_host_dir sending file ' + hostfullfname + ' to ' + 
					'target file: ' + targetfname)
				self.send_file(targetfname, open(hostfullfname).read(), 
					expect=expect, child=child, log=log, user=user, group=group)


	def host_file_exists(self, filename, directory=False, note=None):
		"""Return True if file exists on the host, else False

		@param filename:   Filename to determine the existence of.
		@param directory:  Indicate that the file expected is a directory. (Default: False)
		@param note:       See send()

		@type filename:    string
		@type directory:   boolean

		@rtype: boolean
		"""
		self._handle_note(note, 'Looking for filename on host: ' + filename)
		if directory:
			return os.path.isdir(filename)
		else:
			return os.path.isfile(filename)



	def file_exists(self, filename, expect=None, child=None, directory=False, note=None):
		"""Return True if file exists on the target host, else False

		@param filename:   Filename to determine the existence of.
		@param expect:     See send()
		@param child:      See send()
		@param directory:  Indicate that the file is a directory.
		@param note:       See send()

		@type filename:    string
		@type directory:   boolean

		@rtype: boolean
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self._handle_note(note, 'Looking for filename in current environment: ' + filename)
		#       v the space is intentional, to avoid polluting bash history.
		test = ' test %s %s' % ('-d' if directory is True else '-a', filename)
		output = self.send_and_get_output(test +
			' && echo FILEXIST-""FILFIN || echo FILNEXIST-""FILFIN',
			expect=expect, child=child, record_command=False)
		res = self.match_string(output, '^(FILEXIST|FILNEXIST)-FILFIN$')
		ret = False
		if res == 'FILEXIST':
			ret = True
		elif res == 'FILNEXIST':
			pass
		else:
			# Change to log?
			print repr('before>>>>:%s<<<< after:>>>>%s<<<<' %
				(child.before, child.after))
			self.pause_point('Did not see FIL(N)?EXIST in output:\n' + output, child)
		return ret


	def get_file_perms(self, filename, expect=None, child=None, note=None):
		"""Returns the permissions of the file on the target as an octal
		string triplet.

		@param filename:  Filename to get permissions of.
		@param expect:    See send()
		@param child:     See send()
		@param note:      See send()

		@type filename:   string

		@rtype:           string
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self._handle_note(note)
		cmd = 'stat -c %a ' + filename
		self.send(cmd, expect, child=child, check_exit=False)
		res = self.match_string(child.before, '([0-9][0-9][0-9])')
		return res



	def remove_line_from_file(self,
							  line,
							  filename,
							  expect=None,
							  child=None,
							  match_regexp=None,
							  literal=False,
	                          note=None):
		"""Removes line from file, if it exists.
		Must be exactly the line passed in to match.
		Returns True if there were no problems, False if there were.
	
		@param line:          Line to remove.
		@param filename       Filename to remove it from.
		@param expect:        See send()
		@param child:         See send()
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
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self._handle_note(note)
		# assume we're going to add it
		tmp_filename = '/tmp/' + shutit_util.random_id()
		if self.file_exists(filename, expect=expect, child=child):
			if literal:
				if match_regexp == None:
					#            v the space is intentional, to avoid polluting bash history.
					self.send(""" grep -v '^""" + 
							  line +
							  """$' """ +
							  filename +
							  ' > ' + 
							  tmp_filename, 
							  expect=expect,
							  child=child,
							  exit_values=['0', '1'])
				else:
					if not shutit_util.check_regexp(match_regexp):
						shutit.fail('Illegal regexp found in remove_line_from_file call: ' + match_regexp)
					#            v the space is intentional, to avoid polluting bash history.
					self.send(""" grep -v '^""" + 
							  match_regexp + 
							  """$' """ +
							  filename +
							  ' > ' +
							  tmp_filename,
							  expect=expect,
							  child=child, 
							  exit_values=['0', '1'])
			else:
				if match_regexp == None:
					#          v the space is intentional, to avoid polluting bash history.
					self.send(' grep -v "^' +
							  line +
							  '$" ' +
							  filename +
							  ' > ' +
							  tmp_filename,
							  expect=expect,
							  child=child,
							  exit_values=['0', '1'])
				else:
					if not shutit_util.check_regexp(match_regexp):
						shutit.fail('Illegal regexp found in remove_line_from_file call: ' + match_regexp)
					#          v the space is intentional, to avoid polluting bash history.
					self.send(' grep -v "^' +
							  match_regexp +
							  '$" ' +
							  filename +
							  ' > ' +
							  tmp_filename,
							  expect=expect,
							  child=child,
							  exit_values=['0', '1'])
			self.send('cat ' + tmp_filename + ' > ' + filename,
					  expect=expect, child=child,
					  check_exit=False)
			self.send('rm -f ' + tmp_filename, expect=expect, child=child,
				exit_values=['0', '1'])
		return True
						 



	def change_text(self,
	                text,
	                fname,
	                pattern=None,
	                expect=None,
	                child=None,
	                before=False,
	                force=False,
	                delete=False,
	                note=None,
	                replace=False,
	                line_oriented=True,
	                create=True):

		"""Change text in a file.

		Returns None if there was no match for the regexp, True if it was matched
		and replaced, and False if the file did not exist or there was some other
		problem.

		@param text:          Text to insert.
		@param fname:         Filename to insert text to
		@param pattern:       Regexp for a line to match and insert after/before/replace.
		                      If none, put at end of file.
		@param expect:        See send()
		@param child:         See send()
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
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self._handle_note(note)
		fexists = self.file_exists(fname)
		if not fexists:
			if create:
				self.send('touch ' + fname,expect=expect,child=child)
			else:
				shutit.fail(fname + ' does not exist and create=False')
		if replace:
			# If replace and no pattern FAIL
			if not pattern:
				shutit.fail('replace=True requires a pattern to be passed in')
			# If replace and delete FAIL
			if delete:
				shutit.fail('cannot pass replace=True and delete=True to insert_text')
		if self.command_available('base64'):
			ftext = self.send_and_get_output('base64' + ' ' + fname)
			ftext = base64.b64decode(ftext)
		else:
			ftext = self.send_and_get_output('cat' + ' ' + fname)
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
				if line_oriented == False:
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
		self.send_file(fname,new_text,expect=expect,child=child,truncate=True)
		return True

	def insert_text(self,
	                text,
	                fname,
	                pattern=None,
	                expect=None,
	                child=None,
	                before=False,
	                force=False,
	                note=None,
	                replace=False,
	                line_oriented=True,
	                create=True):
		"""Insert a chunk of text at the end of a file, or after (or before) the first matching pattern
		in given file fname.
		See change_text"""
		self.change_text(text=text, fname=fname, pattern=pattern, expect=expect, child=child, before=before, force=force, note=note, line_oriented=line_oriented, create=create, replace=replace, delete=False)

	def delete_text(self, text, fname, pattern=None, expect=None, child=None, before=False, force=False, note=None, line_oriented=True):
		"""Delete a chunk of text from a file.
		See insert_text.
		"""
		return self.change_text(text, fname, pattern, expect, child, before, force, delete=True, line_oriented=line_oriented)

	def replace_text(self, text, fname, pattern=None, expect=None, child=None, before=False, force=False, note=None, line_oriented=True):
		"""Replace a chunk of text from a file.
		See insert_text.
		"""
		return self.change_text(text, fname, pattern, expect, child, before, force, line_oriented=line_oriented, replace=True)


	def add_line_to_file(self, line, filename, expect=None, child=None, match_regexp=None, force=False, literal=False, note=None):
		"""Deprecated.

		Use replace/insert_text instead.

		Adds line to file if it doesn't exist (unless Force is set,
		which it is not by default).
		Creates the file if it doesn't exist.
		Must be exactly the line passed in to match.
		Returns True if line(s) added OK, False if not.
		If you have a lot of non-unique lines to add, it's a good idea to
		have a sentinel value to add first, and then if that returns true,
		force the remainder.

		@param line:          Line to add. If a list, processed per-item,
		                      and match_regexp ignored.
		@param filename:      Filename to add it to.
		@param expect:        See send()
		@param child:         See send()
		@param match_regexp:  If supplied, a regexp to look for in the file
		                      instead of the line itself,
		                      handy if the line has awkward characters in it.
		@param force:         Always write the line to the file.
		@param literal:       If true, then simply grep for the exact string without
		                      bash interpretation. (Default: False)
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
			if not self.replace_text(line, filename, pattern=this_match_regexp, child=child, expect=expect, note=note):
				fail = True
		if fail:
			return False
		return True





	def add_to_bashrc(self, line, expect=None, child=None, match_regexp=None, note=None):
		"""Takes care of adding a line to everyone's bashrc
		(/etc/bash.bashrc, /etc/profile).

		@param line:          Line to add.
		@param expect:        See send()
		@param child:         See send()
		@param match_regexp:  See add_line_to_file()
		@param note:          See send()

		@return:              See add_line_to_file()
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self._handle_note(note)
		if not shutit_util.check_regexp(match_regexp):
			shutit.fail('Illegal regexp found in add_to_bashrc call: ' + match_regexp)
		self.add_line_to_file(line, '${HOME}/.bashrc', expect=expect, match_regexp=match_regexp) # This won't work for root - TODO
		self.add_line_to_file(line, '/etc/bash.bashrc', expect=expect, match_regexp=match_regexp)
		return self.add_line_to_file(line, '/etc/profile', expect=expect, match_regexp=match_regexp)


	def get_url(self,
	            filename,
	            locations,
	            command='curl',
	            expect=None,
	            child=None,
	            timeout=3600,
	            fail_on_empty_before=True,
	            record_command=True,
	            exit_values=None,
	            echo=False,
	            retry=3,
	            note=None):
		"""Handles the getting of a url for you.

		Example:
		get_url('somejar.jar', ['ftp://loc.org','http://anotherloc.com/jars'])

		@param filename:             name of the file to download
		@param locations:            list of URLs whence the file can be downloaded
		@param command:              program to use to download the file (Default: wget)
		@param expect:               See send()
		@param child:                See send()
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
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self._handle_note(note)
		if len(locations) == 0 or type(locations) != list:
			raise ShutItFailException('Locations should be a list containing base of the url.')
		retry_orig = retry
		if not shutit.command_available(command):
			shutit.install('curl')
			if not shutit.command_available('curl'):
				shutit.install('wget')
				command = 'wget -qO- '
				if not shutit.command_available('wget'):
					shutit.fail('Could not install curl or wget, inform maintainers.')
		for location in locations:
			retry = retry_orig
			if location[-1] == '/':
				location = location[0:-1]
			while retry >= 0:
				send = command + ' ' + location + '/' + filename + ' > ' + filename
				self.send(send,check_exit=False,child=child,expect=expect,timeout=timeout,fail_on_empty_before=fail_on_empty_before,record_command=record_command,echo=echo)
				if retry == 0:
					self._check_exit(send, expect, child, timeout, exit_values, retbool=False)
				elif not self._check_exit(send, expect, child, timeout, exit_values, retbool=True):
					self.log('Sending: ' + send + '\nfailed, retrying')
					retry = retry - 1
					continue
				# If we get here, all is ok.
				return True
		# If we get here, it didn't work
		return False



	def user_exists(self, user, expect=None, child=None, note=None):
		"""Returns true if the specified username exists.
		
		@param user:   username to check for
		@param expect: See send()
		@param child:  See send()
		@param note:   See send()

		@type user:    string

		@rtype:        boolean
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self._handle_note(note)
		exists = False
		if user == '': return exists
		ret = self.send(
			#v the space is intentional, to avoid polluting bash history.
			' id %s && echo E""XIST || echo N""XIST' % user,
			expect=['NXIST', 'EXIST'], child=child
		)
		if ret:
			exists = True
		# sync with the prompt
		child.expect(expect)
		return exists


	def package_installed(self, package, expect=None, child=None, note=None):
		"""Returns True if we can be sure the package is installed.

		@param package:   Package as a string, eg 'wget'.
		@param expect:    See send()
		@param child:     See send()
		@param note:      See send()

		@rtype:           boolean
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		cfg = self.cfg
		self._handle_note(note)
		if cfg['environment'][cfg['build']['current_environment_id']]['install_type'] == 'apt':
			#            v the space is intentional, to avoid polluting bash history.
			self.send(""" dpkg -l | awk '{print $2}' | grep "^""" +
				package + """$" | wc -l""", expect, check_exit=False)
		elif cfg['environment'][cfg['build']['current_environment_id']]['install_type'] == 'yum':
			#            v the space is intentional, to avoid polluting bash history.
			self.send(""" yum list installed | awk '{print $1}' | grep "^""" +
				package + """$" | wc -l""", expect, check_exit=False)
		else:
			return False
		if self.match_string(child.before, '^([0-9]+)$') != '0':
			return True
		else:
			return False


	def command_available(self, command, expect=None, child=None, note=None):
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		cfg = self.cfg
		self._handle_note(note)
		if self.send_and_get_output('command -v ' + command) != '':
			return True
		else:
			return False
		


	def is_shutit_installed(self, module_id, note=None):
		"""Helper proc to determine whether shutit has installed already here by placing a file in the db. 

	
		@param module_id: Identifying string of shutit module
		@param note:      See send()
		"""
		# If it's already in cache, then return True.
		# By default the cache is invalidated.
		cfg = self.cfg
		self._handle_note(note)
		if cfg['environment'][cfg['build']['current_environment_id']]['modules_recorded_cache_valid'] == False:
			if self.file_exists(cfg['build']['build_db_dir'] + '/module_record',directory=True):
				# Bit of a hack here to get round the long command showing up as the first line of the output.
				cmd = 'find ' + cfg['build']['build_db_dir'] + r"""/module_record/ -name built | sed 's@^.""" + cfg['build']['build_db_dir'] + r"""/module_record.\([^/]*\).built@\1@' > """ + cfg['build']['build_db_dir'] + '/' + cfg['build']['build_id']
				self.send(cmd)
				built = self.send_and_get_output('cat ' + cfg['build']['build_db_dir'] + '/' + cfg['build']['build_id']).strip()
				self.send('rm -f ' + cfg['build']['build_db_dir'] + '/' + cfg['build']['build_id'])
				built_list = built.split('\r\n')
				cfg['environment'][cfg['build']['current_environment_id']]['modules_recorded'] = built_list
			# Either there was no directory (so the cache is valid), or we've built the cache, so mark as good.
			cfg['environment'][cfg['build']['current_environment_id']]['modules_recorded_cache_valid'] = True
		# Modules recorded cache will be valid at this point, so check the pre-recorded modules and the in-this-run installed cache.
		if module_id in cfg['environment'][cfg['build']['current_environment_id']]['modules_recorded'] or module_id in cfg['environment'][cfg['build']['current_environment_id']]['modules_installed']:
			return True
		else:
			return False


	def ls(self, directory, note=None):
		"""Helper proc to list files in a directory

		@param directory:   directory to list.
		                    If the directory doesn't exist,
		                    shutit.fail() is called (i.e.
		                    the build fails.)
		@param note:        See send()

		@type directory:    string

		@rtype:             list of strings
		"""
		# should this blow up?
		self._handle_note(note)
		if not self.file_exists(directory,directory=True):
			self.fail('ls: directory\n\n' + directory + '\n\ndoes not exist',
			    throw_exception=False)
		files = self.send_and_get_output(' ls ' + directory)
		files = files.split(' ')
		# cleanout garbage from the terminal - all of this is necessary cause there are
		# random return characters in the middle of the file names
		files = filter(bool, files)
		files = [file.strip() for file in files]
		f = []
		for file in files:
			spl = file.split('\r')
			f = f + spl
		files = f
		# this is required again to remove the '\n's
		files = [file.strip() for file in files]
		return files


	def mount_tmp(self):
		"""mount a temporary file system as a workaround for AUFS /tmp issues.
		Not necessary if running devicemapper.
		"""
		self.send('mkdir -p /tmpbak')
		self.send('cp -r /tmp/* /tmpbak')
		self.send('mount -t tmpfs tmpfs /tmp')
		self.send('cp -r /tmpbak/* /tmp')
		self.send('rm -rf /tmpbak')


	def get_file(self,target_path,host_path,note=None):
		"""Copy a file from the target machine to the host machine, via the artifacts mount

		@param target_path: path to file in the target
		@param host_path:   path to file on the host machine (e.g. copy test)
		@param note:        See send()

		@type target_path: string
		@type host_path:   string

		@return:           ???
		@rtype:            string
		"""
		filename = os.path.basename(target_path)
		cfg = self.cfg
		self._handle_note(note)
		artifacts_dir = cfg['host']['artifacts_dir']
		if self.get_file_perms('/artifacts') != "777":
			user = self.send_and_get_output('whoami').strip()
			# revert to root to do attachments
			if user != 'root':
				self.logout()
			self.send('chmod 777 /artifacts')
			# we've done what we need to do as root, go home
			if user != 'root':
				self.login(user=user)
		self.send('cp ' + target_path + ' /artifacts')
		shutil.copyfile(os.path.join(artifacts_dir,filename),os.path.join(host_path,'{0}_'.format(cfg['build']['build_id']) + filename))
		self.send('rm -f /artifacts/' + filename)
		return os.path.join(host_path,'{0}_'.format(cfg['build']['build_id']) + filename)


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
		cfg = self.cfg
		cfgstr        = '[%s]/%s' % (sec, name)
		config_parser = cfg['config_parser']
		usercfg       = os.path.join(cfg['shutit_home'], 'config')

		print shutit_util.colour('32', '\nPROMPTING FOR CONFIG: %s' % (cfgstr,))
		print shutit_util.colour('32', '\n' + msg + '\n')
		
		if not shutit_util.determine_interactive(shutit):
			self.fail('ShutIt is not in a terminal so cannot prompt ' +
				'for values.', throw_exception=False)

		if config_parser.has_option(sec, name):
			whereset = config_parser.whereset(sec, name)
			if usercfg == whereset:
				self.fail(cfgstr + ' has already been set in the user ' +
				    'config, edit ' + usercfg + ' directly to change it',
				    throw_exception=False)
			for subcp, filename, _fp in reversed(config_parser.layers):
				# Is the config file loaded after the user config file?
				if filename == whereset:
					self.fail(cfgstr + ' is being set in ' + filename + ', ' +
					    'unable to override on a user config level',
					    throw_exception=False)
				elif filename == usercfg:
					break
		else:
			# The item is not currently set so we're fine to do so
			pass
		if ispass:
			val = getpass.getpass('>> ')
		else:
			val = shutit_util.util_raw_input(shutit=self,prompt='>> ')
		is_excluded = (
			config_parser.has_option('save_exclude', sec) and
			name in config_parser.get('save_exclude', sec).split()
		)
		# TODO: ideally we would remember the prompted config item for this
		# invocation of shutit
		if not is_excluded:
			usercp = [
				subcp for subcp, filename, _fp in config_parser.layers
				if filename == usercfg
			][0]
			if shutit_util.util_raw_input(shutit=self,prompt=shutit_util.colour('32',
					'Do you want to save this to your ' +
					'user settings? y/n: '),default='y') == 'y':
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


	def step_through(self, msg='', child=None, level=1, print_input=True, value=True):
		"""Implements a step-through function, using pause_point.
		"""
		child = child or self.get_default_child()
		cfg = self.cfg
		if (not shutit_util.determine_interactive(self) or not cfg['build']['interactive'] or 
			cfg['build']['interactive'] < level):
			return
		cfg['build']['step_through'] = value
		self.pause_point(msg, child=child, print_input=print_input, level=level, resize=False)


	def pause_point(self, msg='', child=None, print_input=True, level=1, resize=False, colour='32', default_msg=None):
		"""Inserts a pause in the build session, which allows the user to try
		things out before continuing. Ignored if we are not in an interactive
		mode, or the interactive level is less than the passed-in one.
		Designed to help debug the build, or drop to on failure so the
		situation can be debugged.

		@param msg:          Message to display to user on pause point.
		@param child:        See send()
		@param print_input:  Whether to take input at this point (i.e. interact), or
		                     simply pause pending any input.
		                     Default: True
		@param level:        Minimum level to invoke the pause_point at.
		                     Default: 1
		@param resize:       If True, try to resize terminal.
		                     Default: False
		@param colour:       Colour to print message (typically 31 for red, 32 for green)
		@param default_msg:  Whether to print the standard blurb

		@type msg:           string
		@type print_input:   boolean
		@type level:         integer
		@type resize:        boolean

		@return:             True if pause point handled ok, else false
		"""
		ok=True
		try:
			child = child or self.get_default_child()
		except Exception:
			ok=False
		if not ok:
			# If we get an exception here, assume we are exiting following a
			# problem before we have a child.
			sys.exit(1)
		cfg = self.cfg
		if (not shutit_util.determine_interactive(self) or cfg['build']['interactive'] < 1 or 
			cfg['build']['interactive'] < level):
			return
		if child:
			if print_input:
				if resize:
					if default_msg == None:
						print (shutit_util.colour(colour,'\nPause point:\n' +
							'resize==True, so attempting to resize terminal.\n\n' +
							'If you are not at a shell prompt when calling pause_point, then pass in resize=False.'))
					self.send_host_file('/tmp/resize',self.shutit_main_dir+'/assets/resize', child=child, log=False)
					self.send(' chmod 755 /tmp/resize')
					child.sendline(' sleep 2 && /tmp/resize')
				if default_msg == None:
					pp_msg = shutit_util.colour(colour,'\nYou can now type in commands and ' +
						'alter the state of the target.\nHit return to see the ' +
						'prompt\nHit CTRL and ] at the same time to continue with ' +
						'build\n')
					# TODO - only if in Docker container
					if False:
						pp_msg += '\nHit CTRL and u to save the state to a docker image\n'
					print '\n' + (shutit_util.colour(colour, msg) + shutit_util.colour(colour,pp_msg))
				else:
					print shutit_util.colour(colour, msg) + '\n' + default_msg + '\n'
				oldlog = child.logfile_send
				child.logfile_send = None
				try:
					child.interact(input_filter=self._pause_input_filter)
				except Exception as e:
					self.fail('Failed to interact, probably because this is run non-interactively,\nor was previously CTRL-C\'d\n' + str(e))
				child.logfile_send = oldlog
			else:
				pass
		else:
			print msg
			print 'Nothing to interact with, so quitting to presumably the original shell'
			sys.exit(1)
		cfg['build']['ctrlc_stop'] = False
		return True


	def _pause_input_filter(self, input_string):
		"""Input filter for pause point to catch special keystrokes"""
		# Can get errors with eg up/down chars
		cfg = self.cfg
		if len(input_string) == 1:
			# Picked CTRL-u as the rarest one accepted by terminals.
			if ord(input_string) == 21:
				self.log('\n\nCTRL and u caught, forcing a tag at least\n\n',
					force_stdout=True)
				self.do_repository_work('tagged_by_shutit',
					password=cfg['host']['password'],
					docker_executable=cfg['host']['docker_executable'],
					force=True)
				self.log('\n\nCommit and tag done\n\nHit CTRL and ] to continue with' + 
					' build. Hit return for a prompt.', force_stdout=True)
		return input_string


	def match_string(self, string, regexp):
		"""Get regular expression from the first of the lines passed
		in in string that matched. Handles first group of regexp as
		a return value.

		@param string: String to match on
		@param regexp: Regexp to check (per-line) against string

		@type string: string
		@type regexp: string

		Returns None if none of the lines matched.

		Returns True if there are no groups selected in the regexp.
		else returns matching group (ie non-None)
		"""
		cfg = self.cfg
		lines = string.split('\r\n')
		# sometimes they're separated by just a carriage return...
		new_lines = []
		for line in lines:
			new_lines = new_lines + line.split('\r')
		lines = new_lines
		if not shutit_util.check_regexp(regexp):
			shutit.fail('Illegal regexp found in match_string call: ' + regexp)
		for line in lines:
			#print line
			#print regexp
			match = re.match(regexp, line)
			#print match
			if match != None:
				if len(match.groups()) > 0:
					return match.group(1)
				else:
					return True
		return None
	# alias for back-compatibility
	get_re_from_child = match_string


	def send_and_match_output(self, send, matches, expect=None, child=None, retry=3, strip=True, note=None):
		"""Returns true if the output of the command matches any of the strings in 
		the matches list of regexp strings. Handles matching on a per-line basis
		and does not cross lines.

		@param send:     See send()
		@param matches:  String - or list of strings - of regexp(s) to check
		@param expect:   See send()
		@param child:    See send()
		@param retry:    Number of times to retry command (default 3)
		@param strip:    Whether to strip output (defaults to True)
		@param note:     See send()

		@type send:      string
		@type matches:   list
		@type retry:     integer
		@type strip:     boolean
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self._handle_note(note)
		output = self.send_and_get_output(send, child=child, retry=retry, strip=strip)
		if type(matches) == str:
			matches = [matches]
		for match in matches:
			if self.match_string(output, match) != None:
				return True
		return False



	def send_and_get_output(self, send, expect=None, child=None, timeout=None, retry=3, strip=True, note=None, record_command=False):
		"""Returns the output of a command run. send() is called, and exit is not checked.

		@param send:     See send()
		@param expect:   See send()
		@param child:    See send()
		@param retry:    Number of times to retry command (default 3)
		@param strip:    Whether to strip output (defaults to True). Strips whitespace
		                 and ansi terminal codes
		@param note:     See send()

		@type retry:     integer
		@type strip:     boolean
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self._handle_note(note, 'Command: ' + str(send))
		# Don't check exit, as that will pollute the output. Also, it's quite likely the
		# submitted command is intended to fail.
		self.send(self._get_send_command(send), child=child, expect=expect, check_exit=False, retry=retry, echo=False, timeout=timeout, record_command=record_command)
		before = self.get_default_child().before
		cfg = shutit.cfg
		try:
			if cfg['environment'][cfg['build']['current_environment_id']]['distro'] == 'osx':
				before_list = before.split('\r\n')
				before_list = before_list[1:]
				before = string.join(before_list,'\r\n')
			else:
				before = before.strip(send)
		except Exception:
			before = before.strip(send)
		if strip:
			ansi_escape = re.compile(r'\x1b[^m]*m')
			string_with_termcodes = before.strip()
			string_without_termcodes = ansi_escape.sub('', string_with_termcodes)
			return string_without_termcodes.strip()
		else:
			return before


	def install(self,
	            package,
	            child=None,
	            expect=None,
	            options=None,
	            timeout=3600,
	            force=False,
	            check_exit=True,
	            reinstall=False,
	            note=None):
		"""Distro-independent install function.
		Takes a package name and runs the relevant install function.

		@param package:    Package to install, which is run through package_map
		@param expect:     See send()
		@param child:      See send()
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
		if package.find(' ') != -1:
			for p in package.split(' '):
				self.install(p,child,expect,options,timeout,force,check_exit,reinstall,note)
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		cfg = self.cfg
		self._handle_note(note)
				
		if options is None: options = {}
		install_type = cfg['environment'][cfg['build']['current_environment_id']]['install_type']
		if install_type == 'src':
			# If this is a src build, we assume it's already installed.
			return True
		opts = ''
		whoiam = self.whoami()
		if whoiam != 'root' and install_type != 'brew':
			if not self.command_available('sudo',child=child,expect=expect):
				self.pause_point('Please install sudo and then continue with CTRL-]',child=child,expect=expect)
			cmd = 'sudo '
			pw = self.get_env_pass(whoiam,'Please input your sudo password in case it is needed (for user: ' + whoiam + ')\nJust hit return if you do not want to submit a password.\n')
		else:
			cmd = ''
			pw = ''
		if install_type == 'apt':
			cmd = cmd + 'apt-get install'
			if 'apt' in options:
				opts = options['apt']
			else:
				opts = '-y'
				if not cfg['build']['debug']:
					opts += ' -qq'
				if force:
					opts += ' --force-yes'
				if reinstall:
					opts += ' --reinstall'
		elif install_type == 'yum':
			cmd = cmd + 'yum install'
			if 'yum' in options:
				opts = options['yum']
			else:
				opts += ' -y'
			if reinstall:
				opts += ' reinstall'
		elif install_type == 'apk':
			cmd = cmd + 'apk add'
			if 'apk' in options:
				opts = options['apk']
		elif install_type == 'emerge':
			cmd = cmd + 'emerge'
			if 'emerge' in options:
				opts = options['emerge']
		elif install_type == 'docker':
			cmd = cmd + 'docker pull'
			if 'docker' in options:
				opts = options['docker']
		elif install_type == 'brew':
			cmd = 'brew install'
			if 'brew' in options:
				opts = options['brew']
			else:
				opts += ' --force'
		else:
			# Not handled
			return False
		# Get mapped packages.
		package = package_map.map_packages(package,
			cfg['environment'][cfg['build']['current_environment_id']]['install_type'])
		# Let's be tolerant of failure eg due to network.
		# This is especially helpful with automated testing.
		if package != '':
			fails = 0
			while True:
				if pw != '':
					res = self.multisend('%s %s %s' % (cmd, opts, package), {'assword':pw},
						expect=['Unable to fetch some archives',expect],
						timeout=timeout, check_exit=False, child=child)
				else:
					res = self.send('%s %s %s' % (cmd, opts, package),
						expect=['Unable to fetch some archives',expect],
						timeout=timeout, check_exit=check_exit, child=child)
				if res == 1:
					break
				else:
					fails += 1
				if fails >= 3:
					break
		else:
			# package not required
			pass
		return True

	def remove(self,
	           package,
	           child=None,
	           expect=None,
	           options=None,
	           timeout=3600,
	           note=None):
		"""Distro-independent remove function.
		Takes a package name and runs relevant remove function.

		@param package:  Package to remove, which is run through package_map.
		@param expect:   See send()
		@param child:    See send()
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
				self.install(p,child,expect,options,timeout,force,check_exit,reinstall,note)
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		cfg = self.cfg
		self._handle_note(note)
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
			cmd = cmd + 'apt-get purge'
			opts = options['apt'] if 'apt' in options else '-qq -y'
		elif install_type == 'yum':
			cmd = cmd + 'yum erase'
			opts = options['yum'] if 'yum' in options else '-y'
		elif install_type == 'apk':
			cmd = cmd + 'apk del'
			if 'apk' in options:
				opts = options['apk']
		elif install_type == 'emerge':
			cmd = cmd + 'emerge -cav'
			if 'emerge' in options:
				opts = options['emerge']
		elif install_type == 'docker':
			cmd = cmd + 'docker rmi'
			if 'docker' in options:
				opts = options['docker']
		elif install_type == 'brew':
			cmd = 'brew uninstall'
			if 'brew' in options:
				opts = options['brew']
			else:
				opts += ' --force'
		else:
			# Not handled
			return False
		# Get mapped package.
		package = package_map.map_package(package,
		          cfg['environment'][cfg['build']['current_environment_id']]['install_type'])
		if pw != '':
			self.multisend('%s %s %s' % (cmd, opts, package), {'assword:':pw}, child=child, expect=expect, timeout=timeout, exit_values=['0','100'])
		else:
			self.send('%s %s %s' % (cmd, opts, package), child=child, expect=expect, timeout=timeout, exit_values=['0','100'])
		return True


	def get_env_pass(self,user=None,msg=None,child=None,expect=None,note=None):
		"""Gets a password from the user if one is not already recorded for this environment.

		@param user:    username we are getting password for
		@param msg:     message to put out there
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self._handle_note(note)
		user = user or self.whoami()
		cfg = self.cfg
		msg = msg or 'Please input the sudo password for user: ' + user
		# Test for the existence of the data structure.
		try:
			cfg['environment'][cfg['build']['current_environment_id']][user]
		except:
			cfg['environment'][cfg['build']['current_environment_id']][user] = {}
		try:
			cfg['environment'][cfg['build']['current_environment_id']][user]['password']
		except Exception:
			# Try and get input, if we are not interactive, this should fail.
			cfg['environment'][cfg['build']['current_environment_id']][user]['password'] = shutit.get_input(msg,ispass=True)
		return cfg['environment'][cfg['build']['current_environment_id']][user]['password']


	def whoami(self, child=None, expect=None, note=None):
		"""Returns the current user by executing "whoami".

		@param child:    See send()
		@param expect:   See send()
		@param note:     See send()

		@return: the output of "whoami"
		@rtype: string
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self._handle_note(note)
		return self.send_and_get_output('whoami').strip()


	def whoarewe(self, child=None, expect=None, note=None):
		"""Returns the current group by executing "groups",
	    taking the first one

		@param child:    See send()
		@param expect:   See send()
		@param note:     See send()

		@return: the output of "whoami"
		@rtype: string
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self._handle_note(note)
		return self.send_and_get_output("groups | cut -f 1 -d ' '").strip()

	def login_stack_append(self, r_id, child=None, expect=None, new_user=''):
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		cfg = self.cfg
		cfg['build']['login_stack'].append(r_id)
		# Dictionary with details about login (eg whoami)
		cfg['build']['logins'][r_id] = {'whoami':new_user}


	def login(self,
	          user='root',
	          command='su -',
	          child=None,
	          password=None,
	          prompt_prefix=None,
	          expect=None,
	          timeout=20,
	          escape=False,
	          note=None,
	          go_home=True):
		"""Logs the user in with the passed-in password and command.
		Tracks the login. If used, used logout to log out again.
		Assumes you are root when logging in, so no password required.
		If not, override the default command for multi-level logins.
		If passwords are required, see setup_prompt() and revert_prompt()

		@param user:            User to login with. Default: root
		@param command:         Command to login with. Default: "su -"
		@param child:           See send()
		@param escape:          See send(). We default to true here in case
		                        it matches an expect we add.
		@param password:        Password.
		@param prompt_prefix:   Prefix to use in prompt setup.
		@param expect:          See send()
		@param timeout:         How long to wait for a response. Default: 20.
		@param note:            See send()
		@param go_home:         Whether to automatically cd to home.

		@type user:             string
		@type command:          string
		@type password:         string
		@type prompt_prefix:    string
		@type timeout:          integer
		"""
		child = child or self.get_default_child()
		# We don't get the default expect here, as it's either passed in, or a base default regexp.
		self._handle_note(note)
		r_id = shutit_util.random_id()
		if prompt_prefix == None:
			prompt_prefix = r_id
		self.login_stack_append(r_id)
		cfg = self.cfg
		# Be helpful.
		if ' ' in user:
			self.fail('user has space in it - did you mean: login(command="' + user + '")?')
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
		if not string.find(command,'ssh') == 0:
			general_expect = general_expect + [user+'@']
			general_expect = general_expect + ['\r\n.*[@#$]']
		if user == 'bash' and command == 'su -':
			print '\n' + 80 * '='
			self.log('WARNING! user is bash - if you see problems below, did you mean: login(command="' + user + '")?',force_stdout=True)
			print '\n' + 80 * '='
		self.multisend(send,{'ontinue connecting':'yes','assword':password,'login:':password},expect=general_expect,check_exit=False,timeout=timeout,fail_on_empty_before=False,escape=escape)
		#if not self._check_exit(send,expect=general_expect):
		#	self.pause_point('Login failed?')
		if prompt_prefix != None:
			self.setup_prompt(r_id,child=child,prefix=prompt_prefix)
		else:
			self.setup_prompt(r_id,child=child)
		if go_home:
			self.send('cd',child=child,check_exit=False)



	def logout(self, child=None, expect=None, command='exit', note=None, timeout=5):
		"""Logs the user out. Assumes that login has been called.
		If login has never been called, throw an error.

			@param child:           See send()
			@param expect:          See send()
			@param command:         Command to run to log out (default=exit)
			@param note:            See send()
		"""
		child = child or self.get_default_child()
		old_expect = expect or self.get_default_expect()
		cfg = self.cfg
		self._handle_note(note)
		if len(cfg['build']['login_stack']):
			current_prompt_name = cfg['build']['login_stack'].pop()
			if len(cfg['build']['login_stack']):
				old_prompt_name     = cfg['build']['login_stack'][-1]
				self.set_default_expect(cfg['expect_prompts'][old_prompt_name])
			else:
				# If none are on the stack, we assume we're going to the root prompt
				# set up in shutit_setup.py
				self.set_default_expect()
		else:
			self.fail('Logout called without corresponding login', throw_exception=False)
		# No point in checking exit here, the exit code will be
		# from the previous command from the logged in session
		self.send(command, expect=expect, check_exit=False, timeout=timeout)
	# alias exit_shell to logout
	exit_shell = logout



	def setup_prompt(self,
	                 prompt_name,
	                 prefix='default',
	                 child=None,
	                 set_default_expect=True,
	                 setup_environment=True):
		"""Use this when you've opened a new shell to set the PS1 to something
		sane. By default, it sets up the default expect so you don't have to
		worry about it and can just call shutit.send('a command').

		If you want simple login and logout, please use login() and logout()
		within this module.

		Typically it would be used in this boilerplate pattern::

		    shutit.send('su - auser',
		        expect=shutit.cfg['expect_prompts']['base_prompt'],
		        check_exit=False)
		    shutit.setup_prompt('tmp_prompt')
		    shutit.send('some command')
		    [...]
		    shutit.set_default_expect()
		    shutit.send('exit')

		This function is assumed to be called whenever there is a change
		of environment.

		@param prompt_name:         Reference name for prompt.
		@param prefix:              Prompt prefix. Default: 'default'
		@param child:               See send()
		@param set_default_expect:  Whether to set the default expect
		                            to the new prompt. Default: True
		@param setup_environment:   Whether to setup the environment config

		@type prompt_name:          string
		@type prefix:               string
		@type set_default_expect:   boolean
		"""
		child = child or self.get_default_child()
		local_prompt = 'SHUTIT_' + prefix + '#' + shutit_util.random_id() + '>'
		cfg = self.cfg
		cfg['expect_prompts'][prompt_name] = local_prompt
		# Set up the PS1 value.
		# Unset the PROMPT_COMMAND as this can cause nasty surprises in the output.
		# Set the cols value, as unpleasant escapes are put in the output if the
		# input is > n chars wide.
		self.send(
			(" export SHUTIT_BACKUP_PS1_%s=$PS1 && PS1='%s' && unset PROMPT_COMMAND && stty cols " + str(cfg['build']['stty_cols'])) %
				(prompt_name, local_prompt),
				# The newline in the list is a hack. On my work laptop this line hangs
				# and times out very frequently. This workaround seems to work, but I
				# haven't figured out why yet - imiell.
				expect=['\r\n' + cfg['expect_prompts'][prompt_name]],
				fail_on_empty_before=False, timeout=5, child=child)
		if set_default_expect:
			self.log('Resetting default expect to: ' +
				cfg['expect_prompts'][prompt_name])
			self.set_default_expect(cfg['expect_prompts'][prompt_name])
		# Ensure environment is set up OK.
		if setup_environment:
			self.setup_environment(prefix)


	def revert_prompt(self, old_prompt_name, new_expect=None, child=None):
		"""Reverts the prompt to the previous value (passed-in).

		It should be fairly rare to need this. Most of the time you would just
		exit a subshell rather than resetting the prompt.

			- old_prompt_name - 
			- new_expect      - 
			- child           - See send()
		"""
		child = child or self.get_default_child()
		expect = new_expect or self.get_default_expect()
		#	  v the space is intentional, to avoid polluting bash history.
		self.send(
			(' PS1="${SHUTIT_BACKUP_PS1_%s}" && unset SHUTIT_BACKUP_PS1_%s') %
				(old_prompt_name, old_prompt_name),
				expect=expect, check_exit=False, fail_on_empty_before=False)
		if not new_expect:
			self.log('Resetting default expect to default')
			self.set_default_expect()
		self.setup_environment()


	def get_memory(self, child=None, expect=None, note=None):
		"""Returns memory available for use in k as an int"""
		child = child or self.get_default_child()
		old_expect = expect or self.get_default_expect()
		cfg = self.cfg
		self._handle_note(note)
		if cfg['environment'][cfg['build']['current_environment_id']]['distro'] == 'osx':
			memavail = self.send_and_get_output("""vm_stat | grep ^Pages.free: | awk '{print $3}' | tr -d '.'""",child=child,expect=expect,timeout=3)
			memavail = int(memavail)
			memavail *= 4
		else:
			memavail = self.send_and_get_output("""cat /proc/meminfo  | grep MemAvailable | awk '{print $2}'""",child=child,expect=expect,timeout=3)
			if memavail == '':
				memavail = self.send_and_get_output("""free | grep buffers.cache | awk '{print $3}'""",child=child,expect=expect,timeout=3)
			memavail = int(memavail)
		return memavail

		


	def get_distro_info(self, environment_id, child=None, container=True):
		"""Get information about which distro we are using,
		placing it in the cfg['environment'][environment_id] as a side effect.

		Fails if distro could not be determined.
		Should be called with the container is started up, and uses as core info
		as possible.

		Note: if the install type is apt, it issues the following:
		    - apt-get update
		    - apt-get install -y -qq lsb-release

		@param child:       See send()
		@param container:   If True, we are in the container shell,
		                    otherwise we are gathering info about another
		                    shell. Defaults to True.

		@type container:    boolean
		"""
		child = child or self.get_default_child()
		install_type   = ''
		distro         = ''
		distro_version = ''
		cfg = self.cfg
		cfg['environment'][environment_id]['install_type']      = ''
		cfg['environment'][environment_id]['distro']            = ''
		cfg['environment'][environment_id]['distro_version']    = ''
		# A list of OS Family members
		# RedHat    = Scientific, SLC, Ascendos, CloudLinux, PSBM, OracleLinux, OVS, OEL, Amazon, XenServer 
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
		#
		#    # A list of dicts.  If there is a platform with more than one
		#    # package manager, put the preferred one last.  If there is an
		#    # ansible module, use that as the value for the 'name' key.
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
			install_type = cfg['build']['install_type_map'][key]
			distro_version = ''
			if install_type == 'apt' and cfg['build']['delivery'] in ('docker','dockerfile'):
				self.send('apt-get update')
				cfg['build']['do_update'] = False
				if not self.command_available('lsb_release'):
					self.send('apt-get install -y -qq lsb-release')
				d = self.lsb_release()
				install_type   = d['install_type']
				distro         = d['distro']
				distro_version = d['distro_version']
			elif install_type == 'yum' and cfg['build']['delivery'] in ('docker', 'dockerfile'):
				self.send('yum update -y',exit_values=['0','1'])
				cfg['build']['do_update'] = False
				if self.file_exists('/etc/redhat-release'):
					output = self.send_and_get_output('cat /etc/redhat-release')
					if re.match('^centos.*$', output.lower()) or re.match('^red hat.*$', output.lower()) or re.match('^fedora.*$', output.lower()) or True:
						self.send_and_match_output('yum install -y -t redhat-lsb','Complete!')
				else:
					if not self.command_available('lsb_release'):
						self.send('yum install -y lsb-release')
				install_type   = d['install_type']
				distro         = d['distro']
				distro_version = d['distro_version']
			elif install_type == 'apk' and cfg['build']['delivery'] in ('docker','dockerfile'):
				cfg['build']['do_update'] = False
				self.send('apk update')
				self.send('apk add bash')
				install_type   = 'apk'
				distro         = 'alpine'
				distro_version = '1.0'
			elif install_type == 'emerge' and cfg['build']['delivery'] in ('docker','dockerfile'):
				self.send('emerge --sync')
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
			if self.file_exists('/etc/issue'):
				issue_output = self.send_and_get_output(' cat /etc/issue').lower()
				for key in cfg['build']['install_type_map'].keys():
					if issue_output.find(key) != -1:
						distro       = key
						install_type = cfg['build']['install_type_map'][key]
						break
			if install_type == '' or distro == '':
				if self.file_exists('/etc/os-release'):
					os_name = self.send_and_get_output(' cat /etc/os-release | grep ^NAME').lower()
					if os_name.find('centos') != -1:
						distro       = 'centos'
						install_type = 'yum'
					elif os_name.find('red hat') != -1:
						distro       = 'red hat'
						install_type = 'yum'
					elif os_name.find('gentoo') != -1:
						distro       = 'gentoo'
						install_type = 'emerge'
					elif os_name.find('coreos') != -1:
						distro       = 'coreos'
						install_type = 'docker'
				elif self.send_and_get_output("uname -a | awk '{print $1}'") == 'Darwin':
					distro = 'osx'
					install_type = 'brew'
					if not self.command_available('brew'):
						self.fail('ShutiIt requires brew be installed. See http://brew.sh for details on installation.')
					for package in ('coreutils','findutils','gnu-tar','gnu-sed','gawk','gnutls','gnu-indent','gnu-getopt'):
						if self.send_and_get_output('brew list | grep -w ' + package) == '':
							self.send('brew install ' + package)
				if install_type == '' or distro == '':
					self.fail('Could not determine Linux distro information. ' + 
								'Please inform ShutIt maintainers.', child=child)
			# The call to self.package_installed with lsb-release above 
			# may fail if it doesn't know the install type, so
			# if we've determined that now
			if install_type == 'apt' and cfg['build']['delivery'] in ('docker','dockerfile'):
				self.send('apt-get update')
				cfg['build']['do_update'] = False
				if not self.command_available('lsb_release'):
					self.send('apt-get install -y -qq lsb-release')
				d = self.lsb_release()
				install_type   = d['install_type']
				distro         = d['distro']
				distro_version = d['distro_version']
			elif install_type == 'yum' and cfg['build']['delivery'] in ('docker','dockerfile'):
				self.send('yum update -y',exit_values=['0','1'])
				cfg['build']['do_update'] = False
				if self.file_exists('/etc/redhat-release'):
					output = self.send_and_get_output('cat /etc/redhat-release')
					if re.match('^centos.*$', output.lower()) or re.match('^red hat.*$', output.lower()) or re.match('^fedora.*$', output.lower()) or True:
						self.send_and_match_output('yum install -y -t redhat-lsb','Complete!')
				else:
					if not self.command_available('lsb_release'):
						self.send('yum install -y lsb-release')
				d = self.lsb_release()
				install_type   = d['install_type']
				distro         = d['distro']
				distro_version = d['distro_version']
			elif install_type == 'apk' and cfg['build']['delivery'] in ('docker','dockerfile'):
				cfg['build']['do_update'] = False
				self.send('apk update')
				self.send('apk install bash')
				install_type   = 'apk'
				distro         = 'alpine'
				distro_version = '1.0'
			elif install_type == 'emerge' and cfg['build']['delivery'] in ('docker','dockerfile'):
				self.send('emerge --sync')
				install_type = 'emerge'
				distro = 'gentoo'
				distro_version = '1.0'
		# We should have the distro info now, let's assign to target config 
		# if this is not a one-off.
		cfg['environment'][environment_id]['install_type']   = install_type
		cfg['environment'][environment_id]['distro']         = distro
		cfg['environment'][environment_id]['distro_version'] = distro_version
		return


	def lsb_release(self, child=None):
		"""Get distro information from lsb_release.
		"""
		child = child or self.get_default_child()
		cfg = self.cfg
		#          v the space is intentional, to avoid polluting bash history.
		self.send(' lsb_release -a',check_exit=False)
		dist_string = self.match_string(child.before,
			'^Distributor[\s]*ID:[\s]*(.*)$')
		version_string = self.match_string(child.before,
			'^Release:[\s*](.*)$')
		d = {}
		if dist_string:
			d['distro']         = dist_string.lower().strip()
			d['distro_version'] = version_string
			d['install_type'] = (
				cfg['build']['install_type_map'][dist_string.lower()])
		return d


	def set_password(self, password, user='', child=None, expect=None, note=None):
		"""Sets the password for the current user or passed-in user.

		As a side effect, installs the "password" package.

		@param user:        username to set the password for. Defaults to '' (i.e. current user)
		@param password:    password to set for the user
		@param expect:      See send()
		@param child:       See send()
		@param note:        See send()
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self._handle_note(note)
		self.install('passwd')
		cfg = self.cfg
		if cfg['environment'][cfg['build']['current_environment_id']]['install_type'] == 'apt':
			self.send('passwd ' + user,
					  expect='Enter new', child=child, check_exit=False)
			self.send(password, child=child, expect='Retype new',
					  check_exit=False, echo=False)
			self.send(password, child=child, expect=expect, echo=False)
		elif cfg['environment'][cfg['build']['current_environment_id']]['install_type'] == 'yum':
			self.send('passwd ' + user, child=child, expect='ew password',
					  check_exit=False)
			self.send(password, child=child, expect='ew password',
					  check_exit=False, echo=False)
			self.send(password, child=child, expect=expect, echo=False)
		else:
			self.send('passwd ' + user,
					  expect='Enter new', child=child, check_exit=False)
			self.send(password, child=child, expect='Retype new',
					  check_exit=False, echo=False)
			self.send(password, child=child, expect=expect, echo=False)


	def is_user_id_available(self, user_id, child=None, expect=None, note=None):
		"""Determine whether the specified user_id available.

		@param user_id:  User id to be checked.
		@param expect:   See send()
		@param child:    See send()
		@param note:     See send()

		@type user_id:   integer

		@rtype:          boolean
		@return:         True is the specified user id is not used yet,
		                 False if it's already been assigned to a user.
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self._handle_note(note)
		#          v the space is intentional, to avoid polluting bash history.
		self.send(' cut -d: -f3 /etc/paswd | grep -w ^' + user_id + '$ | wc -l',
				  child=child, expect=expect, check_exit=False)
		if self.match_string(child.before, '^([0-9]+)$') == '1':
			return False
		else:
			return True


	def push_repository(self,
	                    repository,
	                    docker_executable='docker',
	                    child=None,
	                    expect=None):
		"""Pushes the repository.

		@param repository:          Repository to push.
		@param docker_executable:   Defaults to 'docker'
		@param expect:              See send()
		@param child:               See send()

		@type repository:           string
		@type docker_executable:    string
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		cfg = self.cfg
		send = docker_executable + ' push ' + repository
		expect_list = ['Username', 'Password', 'Email', expect]
		timeout = 99999
		self.log('Running: ' + send, force_stdout=True, prefix=False)
		res = self.send(send, expect=expect_list, child=child, timeout=timeout,
		                check_exit=False, fail_on_empty_before=False)
		while True:
			if res == 3:
				break
			elif res == 0:
				res = self.send(cfg['repository']['user'], child=child,
				                expect=expect_list, timeout=timeout,
				                check_exit=False, fail_on_empty_before=False)
			elif res == 1:
				res = self.send(cfg['repository']['password'], child=child,
				                expect=expect_list, timeout=timeout,
				                check_exit=False, fail_on_empty_before=False)
			elif res == 2:
				res = self.send(cfg['repository']['email'], child=child,
				                expect=expect_list, timeout=timeout,
				                check_exit=False, fail_on_empty_before=False)


	def do_repository_work(self,
	                       repo_name,
	                       repo_tag=None,
	                       expect=None,
	                       docker_executable='docker',
	                       password=None,
	                       force=None):
		"""Commit, tag, push, tar a docker container based on the configuration we
		have.

		@param repo_name:           Name of the repository.
		@param expect:              See send()
		@param docker_executable:   Defaults to 'docker'
		@param password:
		@param force:

		@type repo_name:            string
		@type docker_executable:    string
		@type password:             string
		@type force:                boolean
		"""
		expect = expect or self.get_default_expect()
		cfg = self.cfg
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

		child     = self.pexpect_children['host_child']
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
			self.fail('Could not form valid repository name', child=child, throw_exception=False)
		if (export or save) and not repository_tar:
			self.fail('Could not form valid tar name', child=child, throw_exception=False)

		if server != '':
			repository = '%s/%s' % (server, repository)

		if cfg['build']['deps_only']:
			repo_tag = repo_tag + '_deps'

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
			self.fail("""repository name: '""" + repository +
				"""' too long to push. If using suffix_date consider shortening, or consider""" +
			    """ adding "-s repository push no" to your arguments to prevent pushing.""",
				child=child, throw_exception=False)

		if self.send('SHUTIT_TMP_VAR=$(' + docker_executable + ' commit ' +
					 cfg['target']['container_id'] + ')',
					 expect=[expect,'assword'], child=child, timeout=99999,
					 check_exit=False) == 1:
			self.send(cfg['host']['password'], expect=expect, check_exit=False,
					  record_command=False, child=child)
		# Tag image, force it by default
		cmd = docker_executable + ' tag -f $SHUTIT_TMP_VAR ' + repository_with_tag
		cfg['build']['report'] += '\nBuild tagged as: ' + repository_with_tag
		self.send(cmd, child=child, expect=expect, check_exit=False)
		if export or save:
			self.pause_point('We are now exporting the container to a ' + 
							 'bzipped tar file, as configured in ' +
							 '\n[repository]\ntar:yes', print_input=False,
							 child=child, level=3)
			if export:
				bzfile = (cfg['host']['artifacts_dir'] + '/' + 
						  repository_tar + 'export.tar.bz2')
				self.log('\nDepositing bzip2 of exported container into ' +
						 bzfile)
				if self.send(docker_executable + ' export ' +
							 cfg['target']['container_id'] +
							 ' | bzip2 - > ' + bzfile,
							 expect=[expect, 'assword'], timeout=99999,
							 child=child) == 1:
					self.send(password, expect=expect, child=child)
				self.log('\nDeposited bzip2 of exported container into ' +
						 bzfile, code='32')
				self.log('\nRun:\n\nbunzip2 -c ' + bzfile +
						 ' | sudo docker import -\n\n' +
						 'to get this imported into docker.', code='32')
				cfg['build']['report'] += ('\nDeposited bzip2 of exported' +
										  ' container into ' + bzfile)
				cfg['build']['report'] += ('\nRun:\n\nbunzip2 -c ' + bzfile +
										  ' | sudo docker import -\n\n' +
										  'to get this imported into docker.')
			if save:
				bzfile = (cfg['host']['artifacts_dir'] +
						  '/' + repository_tar + 'save.tar.bz2')
				self.log('\nDepositing bzip2 of exported container into ' +
						 bzfile)
				if self.send(docker_executable + ' save ' +
							 cfg['target']['container_id'] +
							 ' | bzip2 - > ' + bzfile,
							 expect=[expect, 'assword'],
							 timeout=99999, child=child) == 1:
					self.send(password, expect=expect, child=child)
				self.log('\nDeposited bzip2 of exported container into ' +
						 bzfile, code='32')
				self.log('\nRun:\n\nbunzip2 -c ' + bzfile +
						 ' | sudo docker import -\n\n' + 
						 'to get this imported into docker.',
						 code='32')
				cfg['build']['report'] += ('\nDeposited bzip2 of exported ' + 
										  'container into ' + bzfile)
				cfg['build']['report'] += ('\nRun:\n\nbunzip2 -c ' + bzfile +
										   ' | sudo docker import -\n\n' + 
										   'to get this imported into docker.')
		if cfg['repository']['push'] == True:
			# Pass the child explicitly as it's the host child.
			self.push_repository(repository,
		                         docker_executable=docker_executable,
		                         expect=expect,
		                         child=child)
			cfg['build']['report'] = (cfg['build']['report'] +
			                          '\nPushed repository: ' + repository)


	def get_input(self, msg, default='', valid=[], boolean=False, ispass=False):
		"""Gets input from the user, and returns the answer.

		@param msg:       message to send to user
		@param default:   default value if nothing entered
		@param valid:     valid input values (default == empty list == anything allowed)
		@param boolean:   whether return value should be boolean
		@param ispass:    True if this is a password (ie whether to not echo input)
		"""
		if boolean and valid == []:
			valid = ('yes','y','Y','1','true','no','n','N','0','false')
		answer = shutit_util.util_raw_input(prompt=shutit_util.colour('32',msg),ispass=ispass)
		if valid != []:
			while answer not in valid:
				print 'Answer must be one of: ' + str(valid)
				answer = shutit_util.util_raw_input(prompt=shutit_util.colour('32',msg),ispass=ispass)
		if boolean and answer in ('yes','y','Y','1','true'):
			return True
		if boolean and answer in ('no','n','N','0','false'):
			return False
		if answer == '':
			return default
		else:
			return answer




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
		cfg = self.cfg
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
			if forcenone != True:
				if cfg['build']['interactive'] > 0:
					if cfg['build']['accept_defaults'] == None:
						answer = None
						# util_raw_input may change the interactive level, so guard for this.
						while answer not in ('yes','no','') and cfg['build']['interactive'] > 1:
							answer = shutit_util.util_raw_input(shutit=self,prompt=shutit_util.colour('32',
							   'Do you want to accept the config option defaults? ' +
							   '(boolean - input "yes" or "no") (default: yes): \n'))
						# util_raw_input may change the interactive level, so guard for this.
						if answer == 'yes' or answer == '' or cfg['build']['interactive'] < 2:
							cfg['build']['accept_defaults'] = True
						else:
							cfg['build']['accept_defaults'] = False
					if cfg['build']['accept_defaults'] == True and default != None:
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
								answer =  shutit_util.util_raw_input(shutit=self,prompt=shutit_util.colour('32',prompt
								  + ' (boolean - input "yes" or "no"): \n'))
							if answer == 'yes':
								answer = True
							elif answer == 'no':
								answer = False
						else:
							if re.search('assw',option) == None:
								answer =  shutit_util.util_raw_input(shutit=self,prompt=shutit_util.colour('32',prompt) + ': \n')
							else:
								answer =  shutit_util.util_raw_input(shutit=self,ispass=True,prompt=shutit_util.colour('32',prompt) + ': \n')
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


	def get_ip_address(self, ip_family='4', ip_object='addr', command='ip', interface='eth0', note=None):
		"""Gets the ip address based on the args given. Assumes command exists.

		@param ip_family:   type of ip family, defaults to 4
		@param ip_object:   type of ip object, defaults to "addr"
		@param command:     defaults to "ip"
		@param interface:   defaults to "eth0"
		@param note:        See send()

		@type ip_family:    string
		@type ip_object:    string
		@type command:      string
		@type interface:    string
		"""
		self._handle_note(note)
		return self.send_and_get_output(command + ' -' + ip_family + ' -o ' + ip_object + ' | grep ' + interface)



	def record_config(self):
		""" Put the config in a file in the target.
		"""
		cfg = self.cfg
		# appears to break in dockerfile (cf TMM)
		if cfg['build']['delivery'] in ('docker','dockerfile'):
			self.send_file(cfg['build']['build_db_dir'] +
						   '/' + cfg['build']['build_id'] +
						   '/' + cfg['build']['build_id'] +
						   '.cfg', shutit_util.print_config(cfg))


	def get_emailer(self, cfg_section):
		"""Sends an email using the mailer
		"""
		from alerting import emailer
		return emailer.Emailer(cfg_section, self)


	
	def query_config(self, item):
		"""Consistent and back-compatible API for asking for config information.
		"""
		# Is the docker socket mounted?
		if item == 'mount_docker':
			return self.cfg['build']['mount_docker']
		else:
			self.fail('query_config: item "' + item + '" not handled')


def init():
	"""Initialize the shutit object. Called when imported.
	"""
	global pexpect_children
	global shutit_modules
	global shutit_main_dir
	global cfg
	global cwd
	global shutit_command_history
	global shutit_map

	pexpect_children       = {}
	shutit_map             = {}
	shutit_modules         = set()
	shutit_command_history = []
	# Store the root directory of this application.
	# http://stackoverflow.com/questions/5137497
	shutit_main_dir = os.path.abspath(os.path.dirname(__file__))
	cwd = os.getcwd()
	cfg = {}
	cfg['action']                         = {}
	cfg['build']                          = {}
	cfg['build']['interactive']           = 1 # Default to true until we know otherwise
	cfg['build']['build_log']             = None
	cfg['build']['build_log_file']        = None
	cfg['build']['report']                = ''
	cfg['build']['report_final_messages'] = ''
	cfg['build']['debug']                 = False
	cfg['build']['completed']             = False
	cfg['build']['mount_docker']          = False
	cfg['build']['do_update']             = True
	cfg['build']['distro_override']       = ''
	# Whether to honour 'walkthrough' requests
	cfg['build']['walkthrough']           = False
	cfg['target']                         = {}
	cfg['environment']                    = {}
	cfg['host']                           = {}
	cfg['host']['shutit_path']            = sys.path[0]
	cfg['repository']                     = {}
	cfg['expect_prompts']                 = {}
	cfg['users']                          = {}
	cfg['dockerfile']                     = {}
	cfg['list_modules']                   = {}
	cfg['list_configs']                   = {}
	cfg['list_deps']                      = {}
	cfg['build']['install_type_map'] = {'ubuntu':'apt',
	                                    'debian':'apt',
	                                    'steamos':'apt',
	                                    'red hat':'yum',
	                                    'oracleserver':'yum',
	                                    'centos':'yum',
	                                    'fedora':'yum',
	                                    'alpine':'apk',
	                                    'shutit':'src',
	                                    'coreos':'docker',
	                                    'gentoo':'emerge',
	                                    'osx':'brew'}

	# If no LOGNAME available,
	cfg['host']['username'] = os.environ.get('LOGNAME', '')
	if cfg['host']['username'] == '':
		try:
			if os.getlogin() != '':
				cfg['host']['username'] = os.getlogin()
		except Exception:
			import getpass
			cfg['host']['username'] = getpass.getuser()
		if cfg['host']['username'] == '':
			shutit_global.shutit.fail('LOGNAME not set in the environment, ' +
			                          'and login unavailable in python; ' +
			                          'please set to your username.', throw_exception=False)
	cfg['host']['real_user'] = os.environ.get('SUDO_USER',
											  cfg['host']['username'])
	cfg['build']['shutit_state_dir_base'] = '/tmp/shutit_' + cfg['host']['username']
	cfg['build']['build_id'] = (socket.gethostname() + '_' +
	                            cfg['host']['real_user'] + '_' +
	                            str(time.time()) + '.' +
	                            str(datetime.datetime.now().microsecond))
	cfg['build']['shutit_state_dir']           = cfg['build']['shutit_state_dir_base'] + '/' + cfg['build']['build_id']
	cfg['build']['build_db_dir']               = cfg['build']['shutit_state_dir'] + '/build_db'

	return ShutIt(
		pexpect_children=pexpect_children,
		shutit_modules=shutit_modules,
		shutit_main_dir=shutit_main_dir,
		cfg=cfg,
		cwd=cwd,
		shutit_command_history=shutit_command_history,
		shutit_map=shutit_map
	)

shutit = init()

