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
import util
import random
import string
import re
import textwrap
import base64
import getpass
import package_map
import datetime
from shutit_module import ShutItFailException


def random_id(size=8, chars=string.ascii_letters + string.digits):
	"""Generates a random string of given size from the given chars.
	size    - size of random string
	chars   - constituent pool of characters to draw random characters from
	"""
	return ''.join(random.choice(chars) for _ in range(size))


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
		"""
		if self._default_child[-1] is None:
			shutit.fail("Couldn't get default child")
		return self._default_child[-1]


	def get_default_expect(self):
		"""Returns the currently-set default pexpect string (usually a prompt).
		"""
		if self._default_expect[-1] is None:
			shutit.fail("Couldn't get default expect")
		return self._default_expect[-1]


	def get_default_check_exit(self):
		"""Returns default value of check_exit. See send method.
		"""
		if self._default_check_exit[-1] is None:
			shutit.fail("Couldn't get default check exit")
		return self._default_check_exit[-1]


	def set_default_child(self, child):
		"""Sets the default pexpect child.
		"""
		self._default_child[-1] = child


	def set_default_expect(self, expect=None, check_exit=True):
		"""Sets the default pexpect string (usually a prompt).
		Defaults to the configured root_prompt if no
		argument is passed.
		"""
		if expect == None:
			expect = self.cfg['expect_prompts']['root_prompt']
		self._default_expect[-1] = expect
		self._default_check_exit[-1] = check_exit


	# TODO: Manage exits of builds on error
	def fail(self, msg, child=None, throw_exception=True):
		"""Handles a failure, pausing if a pexpect child object is passed in.
		"""
		# Note: we must not default to a child here
		if child is not None:
			self.pause_point('Pause point on fail: ' + msg, child=child)
		print >> sys.stderr, 'ERROR!'
		print >> sys.stderr
		if throw_exception:
			raise ShutItFailException(msg)
		else:
			# This is an "OK" failure, ie we don't need to throw an exception.
			# However, it's still a failure, so return 1
			print msg
			sys.exit(1)


	def log(self, msg, code=None, pause=0, prefix=True, force_stdout=False):
		"""Logging function.

		- code         - Colour code for logging. Ignored if we are in serve mode.
		- pause        - Length of time to pause after logging (default: 0)
		- prefix       - Whether to output logging prefix (LOG: <time>) (default: True)
		- force_stdout - If we are not in debug, put this in stdout anyway (default: False)
		"""
		if prefix:
			prefix = 'LOG: ' + time.strftime("%Y-%m-%d %H:%M:%S", 
				time.localtime())
			msg = prefix + ' ' + str(msg)
		# Don't colour message if we are in serve mode.
		if code != None and not self.cfg['action']['serve']:
			msg = util.colour(code, msg)
		if self.cfg['build']['debug'] or force_stdout:
			print >> sys.stdout, msg
			sys.stdout.flush()
		if self.cfg['build']['build_log']:
			print >> cfg['build']['build_log'], msg
			self.cfg['build']['build_log'].flush()
		time.sleep(pause)

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
	              echo=None):
		"""Multisend. Same as send, except it takes multiple sends and expects in a dict that are
		processed while waiting for the end "expect" argument supplied.

		Arguments as per send(), except:

		send_dict - dict of sends and expects, eg: {'interim prompt:','some input','other prompt','some other input'}
		expect - final expect we want to see. defaults to child.get_default_expect()
		"""
		expect = expect or self.get_default_expect()
		child = child or self.get_default_child()
		
		send_iteration = send
		expect_list = send_dict.keys()
		# Put breakout item in last.
		expect_list.append(expect)
		while True:
			# If it's the last item in the list, it's the breakout one.
			res = self.send(send_iteration, expect=expect_list, child=child, check_exit=check_exit, fail_on_empty_before=fail_on_empty_before, timeout=timeout, record_command=record_command, exit_values=exit_values, echo=echo)
			if res == len(expect_list) - 1:
				break
			else:
				send_iteration = send_dict[expect_list[res]]

  
	def send(self,
	         send,
	         expect=None,
	         child=None,
	         timeout=3600,
	         check_exit=None,
	         fail_on_empty_before=True,
	         record_command=True,
	         exit_values=None,
	         echo=False,
	         retry=3):
		"""Send string as a shell command, and wait until the expected output
		is seen (either a string or any from a list of strings) before
		returning. The expected string will default to the currently-set
		default expected string (see get_default_expect)

		Returns the pexpect return value (ie which expected string in the list
		matched)

		Arguments:

		- child                      - pexpect child to issue command to.
		- send                       - String to send, ie the command being
		                               issued. If set to None, we consume up to
		                               the expect string, which is useful if we
		                               just matched output that came before a
		                               standard command that returns to the
		                               prompt.
		- expect                     - String that we expect to see in the
		                               output. Usually a prompt. Defaults to
		                               currently-set expect string (see
		                               set_default_expect)
		- timeout                    - Timeout on response
		                               (default=3600 seconds).
		- check_exit                 - Whether to check the shell exit code of
		                               the passed-in command.  If the exit value
		                               was non-zero an error is thrown.
		                               (default=None, which takes the
		                               currently-configured check_exit value)
		                               See also fail_on_empty_before.
		- fail_on_empty_before       - If debug is set, fail on empty match
		                               output string (default=True)
		                               If this is set to False, then we don't
		                               check the exit value of the command.
		- record_command             - Whether to record the command for output
		                               at end (default=True). As a safety
		                               measure, if the command matches any
		                               'password's then we don't record it.
		- exit_values                - Array of acceptable exit values as strings
		                               (default ['0'])
		- echo                       - Whether to suppress any logging output
		                               from pexpect to the terminal or not.
		                               We don't record the command if this is
		                               set to False unless record_command is
		                               explicitly passed in as True.
		- retry                      - Number of times to retry the command if
		                               the first attempt doesn't work. Useful if
		                               going to the network.
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
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
							print self.shutit_command_history
							ok_to_record = False
							break
					if not ok_to_record:
						break
			if ok_to_record:
				self.shutit_command_history.append(send)
		if cfg['build']['debug'] and send != None:
			self.log('===================================================' + 
				'=============================')
			self.log('Sending>>>' + send + '<<<')
			self.log('Expecting>>>' + str(expect) + '<<<')
		# Don't echo if echo passed in as False
		while retry > 0:
			if echo == False:
				oldlog = child.logfile_send
				child.logfile_send = None
				child.sendline(send)
				expect_res = child.expect(expect, timeout)
				child.logfile_send = oldlog
			else:
				# If we're sending something, send it.
				if send != None:
					child.sendline(send)
				expect_res = child.expect(expect, timeout)
			if cfg['build']['debug']:
				self.log('child.before>>>' + child.before + '<<<')
				self.log('child.after>>>' + child.after + '<<<')
			if fail_on_empty_before == True:
				if child.before.strip() == '':
					shutit.fail('before empty after sending: ' + str(send) +
						'\n\nThis is expected after some commands that take a ' + 
						'password.\nIf so, add fail_on_empty_before=False to ' + 
						'the send call', child=child)
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
				if not self._check_exit(send, expect, child, timeout, exit_values):
					retry = retry - 1
					continue
			break
		if cfg['build']['step_through']:
			self.pause_point('pause point: stepping through')
		return expect_res
	# alias send to send_and_expect
	send_and_expect = send


	def _check_exit(self,
					send,
					expect=None,
					child=None,
					timeout=3600,
					exit_values=None,
	                retry=0):
		"""Internal function to check the exit value of the shell. Do not use.
		"""
		if cfg['build']['check_exit'] == False:
			self.log('check_exit configured off, returning')
			return
		expect = expect or self.get_default_expect()
		child = child or self.get_default_child()
		if exit_values is None:
			exit_values = ['0']
		# TODO: check that all values are strings.
		# Don't use send here (will mess up last_output)!
		# Space before "echo" here is sic - we don't need this to show up in bash history
		child.sendline(' echo EXIT_CODE:$?')
		child.expect(expect, timeout)
		res = self.get_re_from_child(child.before, 
			'^EXIT_CODE:([0-9][0-9]?[0-9]?)$')
		if res not in exit_values or res == None:
			if res == None:
				res = str(res)
			self.log('child.after: \n' + child.after + '\n')
			self.log('Exit value from command+\n' + str(send) + '\nwas:\n' + res)
			msg = ('\nWARNING: command:\n' + send + 
				  '\nreturned unaccepted exit code: ' + 
				  res + 
				  '\nIf this is expected, pass in check_exit=False or ' + 
				  'an exit_values array into the send function call.')
			cfg['build']['report'] = cfg['build']['report'] + msg
			if cfg['build']['interactive'] >= 1:
				# This is a failure, so we pass in level=0
				self.pause_point(msg + '\n\nPause point on exit_code != 0 (' +
					res + '). CTRL-C to quit', child=child, level=0)
			else:
				if retry > 0:
					shutit.fail('Exit value from command\n' + send +
						'\nwas:\n' + res)
				else:
					return False
		return True


	def run_script(self, script, expect=None, child=None, in_shell=True):
		"""Run the passed-in string as a script on the target's command line.

		- script   - String representing the script. It will be de-indented
					 and stripped before being run.
		- expect   - See send()
		- child    - See send()
		- in_shell - Indicate whether we are in a shell or not.
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
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
		if in_shell:
			script = ('set -o xtrace \n\n' + script + '\n\nset +o xtrace')
		self.send_file('/tmp/shutit_script.sh', script)
		self.send('chmod +x /tmp/shutit_script.sh', expect, child)
		self.shutit_command_history.append\
			('    ' + script.replace('\n', '\n    '))
		if in_shell:
			ret = self.send('. /tmp/shutit_script.sh', expect, child)
		else:
			ret = self.send('/tmp/shutit_script.sh', expect, child)
		self.send('rm /tmp/shutit_script.sh', expect, child)
		return ret


	def send_file(self, path, contents, expect=None, child=None, log=True):
		"""Sends the passed-in string as a file to the passed-in path on the
		target.

		- path     - Target location of file on target.
		- contents - Contents of file as a string. See log.
		- expect   - See send()
		- child    - See send()
		- log      - Log the file contents if in debug.
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		if cfg['build']['debug']:
			self.log('=====================================================' + 
				'===========================')
			self.log('Sending file to' + path)
			if log:
				self.log('contents >>>' + contents + '<<<')
		# Try and echo as little as possible
		oldlog = child.logfile_send
		child.logfile_send = None
		# Prepare to send the contents as base64 so we don't have to worry about
		# special shell characters
		# TODO: hide the gory details:
		# http://stackoverflow.com/questions/5633472
		#stty_orig=`stty -g`
		#stty $stty_orig && echo forcenewline
		contents64 = base64.standard_b64encode(contents)
		# if replace funny chars
		path = path.replace(' ', '\ ')
		child.sendline("base64 --decode > " + path)
		child.expect('\r\n')
		# We have to batch the file up to avoid hitting pipe buffer limit. This
		# is 4k on modern machines (it seems), but we choose 4000b for safety
		# https://github.com/pexpect/pexpect/issues/55
		batchsize = 4000
		for batch in range(0, len(contents64), batchsize):
			child.sendline(contents64[batch:batch + batchsize])
		# Make sure we've synced the prompt before we send EOF. I don't know why
		# this requires three sendlines to generate 2x'\r\n'.
		# Note: we can't rely on a '\r\n' from the batching because the file
		# being sent may validly be empty.
		child.sendline()
		child.sendline()
		child.sendline()
		child.expect('\r\n\r\n', timeout=999999)
		child.sendeof()
		# Done sending the file
		child.expect(expect)
		self._check_exit("#send file to " + path, expect, child)
		child.logfile_send = oldlog


	def send_host_file(self,
	                   path,
	                   hostfilepath,
	                   expect=None,
	                   child=None,
	                   log=True):
		"""Send file from host machine to given path

		- path         - Path to send file to.
		- hostfilepath - Path to file from host to send to target.
		- expect       - See send()
		- child        - See send()
		- log          - arg to pass to send_file (default True)
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		if os.path.isfile(hostfilepath):
			self.send_file(path, open(hostfilepath).read(), expect=expect, 
				child=child, log=log)
		elif os.path.isdir(hostfilepath):
			self.send_host_dir(path, hostfilepath, expect=expect,
				child=child, log=log)
		else:
			shutit.fail('send_host_file - file: ' + hostfilepath +
				' does not exist as file or dir. cwd is: ' + os.getcwd(),
				child=child, throw_exception=False)


	def send_host_dir(self,
					  path,
					  hostfilepath,
					  expect=None,
					  child=None,
					  log=True):
		"""Send directory and all contents recursively from host machine to
		given path.  It will automatically make directories on the target.

		- path         - Path to send directory to
		- hostfilepath - Path to file from host to send to target
		- expect       - See send()
		- child        - See send()
		- log          - Arg to pass to send_file (default True)
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self.log('entered send_host_dir in: ' + os.getcwd())
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
				self.log('send_host_dir sending file hostfullfname to ' + 
					'target file: ' + targetfname)
				self.send_file(targetfname, open(hostfullfname).read(), 
					expect=expect, child=child, log=log)


	def host_file_exists(self, filename, directory=False):
		"""Return True if file exists on the host, else false

		- filename     - Filename to determine the existence of.
		- directory    - Indicate that the file expected is a directory.
		"""

		if directory:
			return os.path.isdir(filename)
		else:
			return os.path.isfile(filename)



	def file_exists(self, filename, expect=None, child=None, directory=False):
		"""Return True if file exists on the target host, else False

		- filename     - Filename to determine the existence of.
		- expect       - See send()
		- child        - See send()
		- directory    - Indicate that the file is a directory.
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		#       v the space is intentional, to avoid polluting bash history.
		test = ' test %s %s' % ('-d' if directory is True else '-a', filename)
		self.send(test +
			' && echo FILEXIST-""FILFIN || echo FILNEXIST-""FILFIN',
			expect=expect, child=child, check_exit=False, record_command=False)
		res = self.get_re_from_child(child.before,
			'^(FILEXIST|FILNEXIST)-FILFIN$')
		ret = False
		if res == 'FILEXIST':
			ret = True
		elif res == 'FILNEXIST':
			pass
		else:
			# Change to log?
			print repr('before>>>>:%s<<<< after:>>>>%s<<<<' %
				(child.before, child.after))
			self.pause_point('Did not see FIL(N)?EXIST in before', child)
		return ret


	def get_file_perms(self, filename, expect=None, child=None):
		"""Returns the permissions of the file on the target as an octal
		string triplet.

		- filename  - Filename to get permissions of.
		- expect    - See send()
		- child     - See send()
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		cmd = 'stat -c %a ' + filename
		self.send(cmd, expect, child=child, check_exit=False)
		res = self.get_re_from_child(child.before, '([0-9][0-9][0-9])')
		return res



	def remove_line_from_file(self,
							  line,
							  filename,
							  expect=None,
							  child=None,
							  match_regexp=None,
							  literal=False):
		"""Removes line from file, if it exists.
		Must be exactly the line passed in to match.
		Returns True if there were no problems, False if there were.
	
		- line         - Line to add.
		- filename     - Filename to add it to.
		- expect       - See send()
		- child        - See send()
		- match_regexp - If supplied, a regexp to look for in the file
						 instead of the line itself,
						 handy if the line has awkward characters in it.
		- literal      - If true, then simply grep for the exact string without
						 bash interpretation.
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		# assume we're going to add it
		tmp_filename = '/tmp/' + random_id()
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
						 

	def add_line_to_file(self,
	                     line,
	                     filename, 
	                     expect=None,
	                     child=None,
	                     match_regexp=None,
	                     force=False,
	                     literal=False):
		"""Adds line to file if it doesn't exist (unless Force is set).
		Creates the file if it doesn't exist.
		Must be exactly the line passed in to match.
		Returns True if line added, False if not.
		If you have a lot of non-unique lines to add, it's a good idea to
		have a sentinel value to add first, and then if that returns true,
		force the remainder.
	
		- line         - Line to add.
		- filename     - Filename to add it to.
		- expect       - See send()
		- child        - See send()
		- match_regexp - If supplied, a regexp to look for in the file
		                 instead of the line itself,
		                 handy if the line has awkward characters in it.
		- force        - Always write the line to the file.
		- literal      - If true, then simply grep for the exact string without
		                 bash interpretation.
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		# assume we're going to add it
		res = '0'
		bad_chars    = '"'
		tmp_filename = '/tmp/' + random_id()
		if match_regexp == None and re.match('.*[' + bad_chars + '].*',
				line) != None:
			shutit.fail('Passed problematic character to add_line_to_file.\n' +
				'Please avoid using the following chars: ' + 
				bad_chars +
				'\nor supply a match_regexp argument.\nThe line was:\n' +
				line, child=child, throw_exception=False)
		if not self.file_exists(filename, expect=expect, child=child):
			# The above cat doesn't work so we touch the file if it
			# doesn't exist already.
			self.send('touch ' + filename, expect=expect, child=child,
				check_exit=False)
		elif not force:
			if literal:
				if match_regexp == None:
					#            v the space is intentional, to avoid polluting bash history.
					self.send(""" grep -w '^""" + 
							  line +
							  """$' """ +
							  filename +
							  ' > ' + 
							  tmp_filename, 
							  expect=expect,
							  child=child,
							  exit_values=['0', '1'])
				else:
					#            v the space is intentional, to avoid polluting bash history.
					self.send(""" grep -w '^""" + 
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
					self.send(' grep -w "^' +
							  line +
							  '$" ' +
							  filename +
							  ' > ' +
							  tmp_filename,
							  expect=expect,
							  child=child,
							  exit_values=['0', '1'])
				else:
					#          v the space is intentional, to avoid polluting bash history.
					self.send(' grep -w "^' +
							  match_regexp +
							  '$" ' +
							  filename +
							  ' > ' +
							  tmp_filename,
							  expect=expect,
							  child=child,
							  exit_values=['0', '1'])
			self.send('cat ' + tmp_filename + ' | wc -l',
					  expect=expect, child=child, exit_values=['0', '1'],
					  check_exit=False)
			res = self.get_re_from_child(child.before, '^([0-9]+)$')
		if res == '0' or force:
			self.send('cat >> ' + filename + """ <<< '""" + line + """'""",
				expect=expect, child=child, check_exit=False)
			self.send('rm -f ' + tmp_filename, expect=expect, child=child,
				exit_values=['0', '1'])
			return True
		else:
			self.send('rm -f ' + tmp_filename, expect=expect, child=child,
				exit_values=['0', '1'])
			return False


	def add_to_bashrc(self, line, expect=None, child=None, match_regexp=None):
		"""Takes care of adding a line to everyone's bashrc
		(/etc/bash.bashrc, /etc/profile).

		- line   - Line to add.
		- expect - See send()
		- child  - See send()
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self.add_line_to_file(line, '${HOME}/.bashrc', expect=expect, match_regexp=match_regexp) # This won't work for root - TODO
		self.add_line_to_file(line, '/etc/bash.bashrc', expect=expect, match_regexp=match_regexp)
		return self.add_line_to_file(line, '/etc/profile', expect=expect, match_regexp=match_regexp)


	def user_exists(self, user, expect=None, child=None):
		"""Returns true if the specified username exists.
		
		- user   - username to check for
		- expect - See send()
		- child  - See send()
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		exist = False
		if user == '': return exist
		ret = shutit.send(
			#v the space is intentional, to avoid polluting bash history.
			' id %s && echo E""XIST || echo N""XIST' % user,
			expect=['NXIST', 'EXIST'], child=child
		)
		if ret:
			exist = True
		# sync with the prompt
		child.expect(expect)
		return exist


	def package_installed(self, package, expect=None, child=None):
		"""Returns True if we can be sure the package is installed.

		- package - Package as a string, eg 'wget'.
		- expect  - See send()
		- child   - See send()
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		if self.cfg['target']['install_type'] == 'apt':
			#            v the space is intentional, to avoid polluting bash history.
			self.send(""" dpkg -l | awk '{print $2}' | grep "^""" +
				package + """$" | wc -l""", expect, check_exit=False)
		elif self.cfg['target']['install_type'] == 'yum':
			#            v the space is intentional, to avoid polluting bash history.
			self.send(""" yum list installed | awk '{print $1}' | grep "^""" +
				package + """$" | wc -l""", expect, check_exit=False)
		else:
			return False
		if self.get_re_from_child(child.before, '^([0-9]+)$') != '0':
			return True
		else:
			return False


	def ls(self, directory):
		"""Helper proc to list files in a directory

		Returns list of files.

		directory - directory to list
		"""
		# should this blow up?
		if not shutit.file_exists(directory,directory=True):
			shutit.fail('ls: directory\n\n' + directory + '\n\ndoes not exist',
			    throw_exception=False)
		files = shutit.send_and_get_output('ls ' + directory)
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
		"""mount a temporary file system as a workaround for the AUFS /tmp issues
			not necessary if running devicemapper
		"""
		shutit.send('mkdir -p /tmpbak') # Needed?
		shutit.send('touch /tmp/' + cfg['build']['build_id']) # Needed?
		shutit.send('cp -r /tmp/* /tmpbak') # Needed?
		shutit.send('mount -t tmpfs tmpfs /tmp')
		shutit.send('cp -r /tmpbak/* /tmp') # Needed?
		shutit.send('rm -rf /tmpbak') # Needed?
		shutit.send('rm -f /tmp/' + cfg['build']['build_id']) # Needed?


	def get_file(self,target_path,host_path):
		"""Copy a file from the target machine to the host machine, via the artifacts mount

		target_path - path to file in the target
		host_path      - path to file on the host machine (e.g. copy test)
		"""
		filename = os.path.basename(target_path)
		artifacts_dir = shutit.cfg['host']['artifacts_dir']
		if shutit.get_file_perms('/artifacts') != "777":
			user = shutit.send_and_get_output('whoami').strip()
			# revert to root to do attachments
			if user != 'root':
				shutit.logout()
			shutit.send('chmod 777 /artifacts')
			# we've done what we need to do as root, go home
			if user != 'root':
				shutit.login(user)
		shutit.send('cp ' + target_path + ' /artifacts')
		shutil.copyfile(os.path.join(artifacts_dir,filename),os.path.join(host_path,filename))
		shutit.send('rm -f /artifacts/' + filename)


	def prompt_cfg(self, msg, sec, name, ispass=False):
		"""Prompt for a config value, optionally saving it to the user-level
		cfg. Only runs if we are in an interactive mode.

		msg    - Message to display to user.
		sec    - Section of config to add to.
		name   - Config item name.
		ispass - Hide the input from the terminal.
		"""
		cfgstr        = '[%s]/%s' % (sec, name)
		config_parser = cfg['config_parser']
		usercfg       = os.path.join(cfg['shutit_home'], 'config')

		print util.colour('34', '\nPROMPTING FOR CONFIG: %s' % (cfgstr,))
		print util.colour('34', '\n' + msg + '\n')
		
		if not sys.stdout.isatty():
			shutit.fail('ShutIt is not in a terminal so cannot prompt ' +
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
			val = util.util_raw_input(shutit=self,prompt='>> ')
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
			if util.util_raw_input(shutit=self,prompt=util.colour('34',
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
		if (not sys.stdout.isatty() or not self.cfg['build']['interactive'] or 
			self.cfg['build']['interactive'] < level):
			return
		self.cfg['build']['step_through'] = value
		self.pause_point(msg, child=child, print_input=print_input, level=level, resize=False)


	def pause_point(self, msg='', child=None, print_input=True, level=1, resize=False):
		"""Inserts a pause in the build session, which allows the user to try
		things out before continuing. Ignored if we are not in an interactive
		mode, or the interactive level is less than the passed-in one.
		Designed to help debug the build, or drop to on failure so the
		situation can be debugged.

		- msg         - Message to display to user on pause point.
		- child       - See send()
		- print_input - Whether to take input at this point (ie interact), or
						simply pause pending any input.
		- level       - Minimum level to invoke the pause_point at
		"""
		child = child or self.get_default_child()
		if (not sys.stdout.isatty() or not self.cfg['build']['interactive'] or 
			self.cfg['build']['interactive'] < level):
			return
		if child and print_input:
			if resize:
				print (util.colour('31','\nPause point:\n' +
					'resize==True, so attempting to resize terminal.\n\n' +
					'If you are not at a shell prompt when calling pause_point, then pass in resize=False.'))
				shutit.send_host_file('/tmp/resize',self.shutit_main_dir+'/assets/resize', child=child, log=False)
				shutit.send(' chmod 755 /tmp/resize')
				child.sendline(' sleep 2 && /tmp/resize')
			print (util.colour('31', '\nPause point:\n') + 
				msg + util.colour('31','\nYou can now type in commands and ' +
				'alter the state of the target.\nHit return to see the ' +
				'prompt\nHit CTRL and ] at the same time to continue with ' +
				'build\n\nHit CTRL and u to save the state\n'))
			oldlog = child.logfile_send
			child.logfile_send = None
			try:
				child.interact(input_filter=self._pause_input_filter)
			except Exception as e:
				shutit.fail('Failed to interact, probably because this is run non-interactively.\n' + str(e))
			child.logfile_send = oldlog
		else:
			print msg
			print util.colour('31', '\n\n[Hit return to continue]\n')
			util.util_raw_input(shutit=self)


	def _pause_input_filter(self, input_string):
		"""Input filter for pause point to catch special keystrokes"""
		# Can get errors with eg up/down chars
		if len(input_string) == 1:
			# Picked CTRL-u as the rarest one accepted by terminals.
			if ord(input_string) == 21:
				self.log('\n\nCTRL and u caught, forcing a tag at least\n\n',
					force_stdout=True)
				self.do_repository_work('tagged_by_shutit',
					password=self.cfg['host']['password'],
					docker_executable=self.cfg['host']['docker_executable'],
					force=True)
				self.log('\n\nCommit and tag done\n\nCTRL-] to continue with' + 
					' build. Hit return for a promp.', force_stdout=True)
		return input_string


	def get_output(self, child=None):
		"""Helper function to get output from latest command run.
		Use with care - if you are expecting something other than 
		a prompt, this may not return what you might expect.

		- child       - See send()
		"""
		child = child or self.get_default_child()
		return self.cfg['build']['last_output']


	def get_re_from_child(self, string, regexp):
		"""Get regular expression from the first of the lines passed
		in in string that matched.

		Returns None if none of the lines matched.

		Returns True if there are no groups selected in the regexp.

		- string - string to search through lines of
		- regexp - regexp to search for per line
		"""
		if cfg['build']['debug']:
			self.log('get_re_from_child:')
			self.log(string)
			self.log(regexp)
		lines = string.split('\r\n')
		for line in lines:
			if cfg['build']['debug']:
				self.log('trying: ' + line + ' against regexp: ' + regexp)
			match = re.match(regexp, line)
			if match != None:
				if len(match.groups()) > 0:
					if cfg['build']['debug']:
						self.log('returning: ' + match.group(1))
					return match.group(1)
				else:
					return True
		return None


	def send_and_get_output(self, send, expect=None, child=None, retry=3):
		"""Returns the output of a command run.
		send() is called, and exit is not checked.

		- send   - See send()
		- expect - See send()
		- child  - See send()
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self.send(send, check_exit=False, retry=3)
		return shutit.get_default_child().before.strip(send)


	def install(self,
	            package,
	            child=None,
	            expect=None,
	            options=None,
	            timeout=3600,
	            force=False,
	            check_exit=True,
	            reinstall=False):
		"""Distro-independent install function.
		Takes a package name and runs the relevant install function.
		Returns true if all ok (ie it's installed), else false.

		- package    - Package to install, which is run through package_map
		- expect     - See send()
		- child      - See send()
		- timeout    - Timeout to wait for finish of install.
		- options    - Dictionary for specific options per install tool.
		               Overrides any arguments passed into this function.
		- force      - force if necessary
		- check_exit - If False, failure to install is ok (default True)
		- reinstall  - Advise a reinstall where possible (default False)
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		if options is None: options = {}
		# TODO: config of maps of packages
		install_type = self.cfg['target']['install_type']
		if install_type == 'src':
			# If this is a src build, we assume it's already installed.
			return True
		opts = ''
		if install_type == 'apt':
			cmd = 'apt-get install'
			if 'apt' in options:
				opts = options['apt']
			else:
				opts = '-y'
				if not self.cfg['build']['debug']:
					opts += ' -qq'
				if force:
					opts += ' --force-yes'
				if reinstall:
					opts += ' --reinstall'
		elif install_type == 'yum':
			cmd = 'yum install'
			if 'yum' in options:
				opts = options['yum']
			else:
				opts += ' -y'
			if reinstall:
				opts += ' reinstall'
		else:
			# Not handled
			return False
		# Get mapped package.
		package = package_map.map_package(package,
			self.cfg['target']['install_type'])
		# Let's be tolerant of failure eg due to network.
		# This is especially helpful with automated testing.
		if package != '':
			fails = 0
			while True:
				res = self.send('%s %s %s' % (cmd, opts, package),
					expect=['Unable to fetch some archives',expect],
					timeout=timeout, check_exit=check_exit)
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
			   timeout=3600):
		"""Distro-independent remove function.
		Takes a package name and runs relevant remove function.
		Returns true if all ok (ie it's installed now), else false.

		- package  - Package to install, which is run through package_map.
		- expect   - See send()
		- child    - See send()
		- options  - Dict of options to pass to the remove command,
		             mapped by install_type.
		- timeout  - See send()
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		if options is None: options = {}
		install_type = self.cfg['target']['install_type']
		if install_type == 'src':
			# If this is a src build, we assume it's already installed.
			return True
		if install_type == 'apt':
			cmd = 'apt-get purge'
			opts = options['apt'] if 'apt' in options else '-qq -y'
		elif install_type == 'yum':
			cmd = 'yum erase'
			opts = options['yum'] if 'yum' in options else '-y'
		else:
			# Not handled
			return False
		# Get mapped package.
		package = package_map.map_package(package,
			self.cfg['target']['install_type'])
		self.send('%s %s %s' % (cmd, opts, package), expect, timeout=timeout, exit_values=['0','100'])
		return True


	def exec_shell(self, command='bash', child=None, password=None):
		"""See login.

		This is the same, except it simply execs a shell, acting like a login.
		Useful eg if you've just ssh'd in and need to refresh the shell in a 
		simple exec_shell()/exit_shell() combo.

		user     - User to login with
		command  - Command to login with
		child    - See send()
		"""
		child = child or self.get_default_child()
		r_id = random_id()
		self.cfg['build']['login_stack'].append(r_id)
		self.send(command,expect=shutit.cfg['expect_prompts']['base_prompt'],check_exit=False)
		self.setup_prompt(r_id,child=child)


	def login(self, user='root', command='su -', child=None, password=None, prompt_prefix=None):
		"""Logs the user in with the passed-in password and command.
		Tracks the login. If used, used logout to log out again.
		Assumes you are root when logging in, so no password required.
		If not, override the default command for multi-level logins.
		If passwords are required, see setup_prompt() and revert_prompt()

		user      - User to login with
		command   - Command to login with
		child     - See send()
		prompt_prefix - Prefix to use in prompt setup
		"""
		child = child or self.get_default_child()
		r_id = random_id()
		self.cfg['build']['login_stack'].append(r_id)
		if command == 'su -' or command == 'login':
			send = command + ' ' + user
		else:
			send = command
		self.multisend(send,{'ontinue connecting':'yes','assword':password,'login:':password},expect=shutit.cfg['expect_prompts']['base_prompt'],check_exit=False)
		if prompt_prefix != None:
			self.setup_prompt(r_id,child=child,prefix=prompt_prefix)
		else:
			self.setup_prompt(r_id,child=child)



	def logout(self, child=None, expect=None):
		"""Logs the user out. Assumes that login has been called.
		If login has never been called, throw an error.

		- child              - See send()
		- expect             - override expect (eg for base_prompt)
		"""
		child = child or self.get_default_child()
		if len(self.cfg['build']['login_stack']):
			#print "LOGIN STACK TO BE POPPED"
			#print self.cfg['build']['login_stack']
			current_prompt_name = self.cfg['build']['login_stack'].pop()
			if len(self.cfg['build']['login_stack']):
				old_prompt_name     = self.cfg['build']['login_stack'][-1]
				self.set_default_expect(self.cfg['expect_prompts'][old_prompt_name])
			else:
				# If none are on the stack, we assume we're going to the root_prompt
				# set up in setup.py
				self.set_default_expect()
		else:
			self.fail('Logout called without corresponding login', throw_exception=False)
		# No point in checking exit here, the exit code will be
		# from the previous command from the logged in session
		self.send('exit', expect=expect, check_exit=False)
	# alias exit_shell to logout
	exit_shell = logout


	def setup_prompt(self,
	                 prompt_name,
	                 prefix='TMP',
	                 child=None,
	                 set_default_expect=True):
		"""Use this when you've opened a new shell to set the PS1 to something
		sane. By default, it sets up the default expect so you don't have to
		worry about it and can just call shutit.send('a command').

		If you want simple login and logout, please use login() and logout()
		within this module.

		Typically it would be used in this boilerplate pattern

		shutit.send('su - auser',
		            expect=shutit.cfg['expect_prompts']['base_prompt'],
		            check_exit=False)
		shutit.setup_prompt('tmp_prompt')
		shutit.send('some command')
		[...]
		shutit.set_default_expect()
		shutit.send('exit')

		- prompt_name        - Reference name for prompt.
		- prefix             - Prompt prefix.
		- child              - See send()
		- set_default_expect - Whether to set the default expect to the new prompt.
		"""
		child = child or self.get_default_child()
		local_prompt = 'SHUTIT_' + prefix + '#' + random_id() + '>'
		shutit.cfg['expect_prompts'][prompt_name] = local_prompt
		# Set up the PS1 value.
		# Unset the PROMPT_COMMAND as this can cause nasty surprises in the output.
		# Set the cols value, as unpleasant escapes are put in the output if the
		# input is > n chars wide.
		self.send(
			(" export SHUTIT_BACKUP_PS1_%s=$PS1 && PS1='%s' && unset PROMPT_COMMAND && stty cols " + str(shutit.cfg['target']['stty_cols'])) %
				(prompt_name, local_prompt),
				# The newline in the list is a hack. On my work laptop this line hangs
				# and times out very frequently. This workaround seems to work, but I
				# haven't figured out why yet - imiell.
				expect=['\r\n' + self.cfg['expect_prompts'][prompt_name]],
				fail_on_empty_before=False, timeout=5, child=child)
		if set_default_expect:
			shutit.log('Resetting default expect to: ' +
				shutit.cfg['expect_prompts'][prompt_name])
			self.set_default_expect(shutit.cfg['expect_prompts'][prompt_name])


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
			shutit.log('Resetting default expect to default')
			self.set_default_expect()


	def get_distro_info(self, child=None, container=True):
		"""Get information about which distro we are using.

		Fails if distro could not be determined.
		Should be called with the container is started up, and uses as core info
		as possible.

		- child              - See send()
		- container          - If True, we are in the container shell,
		                       otherwise we are gathering info about another
		                       shell
		"""
		child = child or self.get_default_child()
		install_type   = ''
		distro         = ''
		distro_version = ''
		if container:
			cfg['target']['install_type']      = ''
			cfg['target']['distro']            = ''
			cfg['target']['distro_version']    = ''
		# A list of OS Family members
		# RedHat    = RedHat, Fedora, CentOS, Scientific, SLC, Ascendos, CloudLinux, PSBM, OracleLinux, OVS, OEL, Amazon, XenServer 
		# Debian    = Ubuntu, Debian
		# Suse      = SLES, SLED, OpenSuSE, Suse
		# Gentoo    = Gentoo, Funtoo
		# Archlinux = Archlinux
		# Mandrake  = Mandriva, Mandrake
		# Solaris   = Solaris, Nexenta, OmniOS, OpenIndiana, SmartOS
		# AIX       = AIX
		# Alpine    = Alpine
		# Darwin    = MacOSX
		# FreeBSD   = FreeBSD
		# HP-UK     = HPUX

		#    OSDIST_DICT = { '/etc/redhat-release': 'RedHat',
		#                    '/etc/vmware-release': 'VMwareESX',
		#                    '/etc/openwrt_release': 'OpenWrt',
		#                    '/etc/system-release': 'OtherLinux',
		#                    '/etc/alpine-release': 'Alpine',
		#                    '/etc/release': 'Solaris',
		#                    '/etc/arch-release': 'Archlinux',
		#                    '/etc/SuSE-release': 'SuSE',
		#                    '/etc/gentoo-release': 'Gentoo',
		#                    '/etc/os-release': 'Debian' }
		#    SELINUX_MODE_DICT = { 1: 'enforcing', 0: 'permissive', -1: 'disabled' }
		#
		#    # A list of dicts.  If there is a platform with more than one
		#    # package manager, put the preferred one last.  If there is an
		#    # ansible module, use that as the value for the 'name' key.
		#    PKG_MGRS = [ { 'path' : '/usr/bin/yum',         'name' : 'yum' },
		#                 { 'path' : '/usr/bin/apt-get',     'name' : 'apt' },
		#                 { 'path' : '/usr/bin/zypper',      'name' : 'zypper' },
		#                 { 'path' : '/usr/sbin/urpmi',      'name' : 'urpmi' },
		#                 { 'path' : '/usr/bin/pacman',      'name' : 'pacman' },
		#                 { 'path' : '/bin/opkg',            'name' : 'opkg' },
		#                 { 'path' : '/opt/local/bin/pkgin', 'name' : 'pkgin' },
		#                 { 'path' : '/opt/local/bin/port',  'name' : 'macports' },
		#                 { 'path' : '/sbin/apk',            'name' : 'apk' },
		#                 { 'path' : '/usr/sbin/pkg',        'name' : 'pkgng' },
		#                 { 'path' : '/usr/sbin/swlist',     'name' : 'SD-UX' },
		#                 { 'path' : '/usr/bin/emerge',      'name' : 'portage' },
		#                 { 'path' : '/usr/sbin/pkgadd',     'name' : 'svr4pkg' },
		#                 { 'path' : '/usr/bin/pkg',         'name' : 'pkg' },
		#    ]
		if self.package_installed('lsb-release'):
			d = self.lsb_release()
			install_type   = d['install_type']
			distro         = d['distro']
			distro_version = d['distro_version']
		else:
			for key in cfg['build']['install_type_map'].keys():
			    #          v the space is intentional, to avoid polluting bash history.
				self.send(' cat /etc/issue | grep -i "' + key + '" | wc -l',
					check_exit=False)
				if self.get_re_from_child(child.before, '^([0-9]+)$') == '1':
					distro       = key
					install_type = cfg['build']['install_type_map'][key]
					break
			if (install_type == '' or distro == ''):
			    #          v the space is intentional, to avoid polluting bash history.
				self.send(' cat /etc/issue',check_exit=False)
				if self.get_re_from_child(child.before,'^Kernel .*r on an .*m$'):
					distro       = 'centos'
					install_type = 'yum'
			if (install_type == '' or distro == ''):
				shutit.fail('Could not determine Linux distro information. ' + 
							'Please inform ShutIt maintainers.', child=child)
			# The call to self.package_installed with lsb-release above 
			# may fail if it doesn't know the install type, so
			# if we've determined that now
			if install_type == 'apt':
				self.send('apt-get update')
				self.send('apt-get install -y -qq lsb-release')
				d = self.lsb_release()
				install_type   = d['install_type']
				distro         = d['distro']
				distro_version = d['distro_version']
		# We should have the distro info now, let's assign to target config 
		# if this is not a one-off.
		if container:
			cfg['target']['install_type']   = install_type
			cfg['target']['distro']         = distro
			cfg['target']['distro_version'] = distro_version
		return {'install_type':install_type,'distro':distro,'distro_version':distro_version}


	def lsb_release(self, child=None):
		child = child or self.get_default_child()
		#          v the space is intentional, to avoid polluting bash history.
		self.send(' lsb_release -a',check_exit=False)
		dist_string = self.get_re_from_child(child.before,
			'^Distributor[\s]*ID:[\s]*(.*)$')
		version_string = self.get_re_from_child(child.before,
			'^Release:[\s*](.*)$')
		d = {}
		if dist_string:
			d['distro']         = dist_string.lower()
			d['distro_version'] = version_string
			d['install_type'] = (
				cfg['build']['install_type_map'][dist_string.lower()])
		return d


	def set_password(self, password, user='', child=None, expect=None):
		"""Sets the password for the current user or passed-in user.

		- password - 
		- user     - 
		- expect   - See send()
		- child    - See send()
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self.install('passwd')
		if cfg['target']['install_type'] == 'apt':
			self.send('passwd ' + user,
					  expect='Enter new', child=child, check_exit=False)
			self.send(password, child=child, expect='Retype new',
					  check_exit=False, echo=False)
			self.send(password, child=child, expect=expect, echo=False)
			#Considered harmful as it broke builds due to keyring error
			#W: GPG error: http://ppa.launchpad.net precise Release: The following signatures couldn't be verified because the public key is not available: NO_PUBKEY B70731143DD9F856
			#W: Failed to fetch http://archive.ubuntu.com/ubuntu/dists/precise/main/source/Sources  Hash Sum mismatch
			# It seems that doing apt-utils before apt-get update is a problem
			#self.install('apt-utils')
		elif cfg['target']['install_type'] == 'yum':
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


	def is_user_id_available(self, user_id, child=None, expect=None):
		"""Determine whether a user_id for a user is available.

		- user_id  - 
		- expect   - See send()
		- child    - See send()
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		#          v the space is intentional, to avoid polluting bash history.
		self.send(' cut -d: -f3 /etc/paswd | grep -w ^' + user_id + '$ | wc -l',
				  child=child, expect=expect, check_exit=False)
		if self.get_re_from_child(child.before, '^([0-9]+)$') == '1':
			return False
		else:
			return True


	def push_repository(self,
	                    repository,
	                    docker_executable='docker.io',
	                    child=None,
	                    expect=None):
		"""Pushes the repository.

		- repository        - 
		- docker_executable -
		- expect            - See send()
		- child             - See send()
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
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
	                       docker_executable='docker.io',
	                       password=None,
	                       force=None):
		"""Commit, tag, push, tar a docker container based on the configuration we
		have.

		- repo_name         - 
		- expect            - See send()
		- docker_executable - 
		- password          - 
		- force             - 
		"""
		expect = expect or self.get_default_expect()
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
		expect    = cfg['expect_prompts']['real_user_prompt']
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
			shutit.fail('Could not form valid repository name', child=child, throw_exception=False)
		if (export or save) and not repository_tar:
			shutit.fail('Could not form valid tar name', child=child, throw_exception=False)

		if server != '':
			repository = '%s/%s' % (server, repository)

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
			shutit.fail("""repository name: '""" + repository +
				"""' too long. If using suffix_date consider shortening""",
				child=child, throw_exception=False)

		if self.send('SHUTIT_TMP_VAR=$(' + docker_executable + ' commit ' +
					 cfg['target']['container_id'] + ')',
					 expect=[expect,'assword'], child=child, timeout=99999,
					 check_exit=False) == 1:
			self.send(cfg['host']['password'], expect=expect, check_exit=False,
					  record_command=False, child=child)
		# Tag image
		cmd = docker_executable + ' tag $SHUTIT_TMP_VAR ' + repository_with_tag
		self.cfg['build']['report'] += '\nBuild tagged as: ' + repository_with_tag
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
						 bzfile, code='31')
				self.log('\nRun:\n\nbunzip2 -c ' + bzfile +
						 ' | sudo docker import -\n\n' +
						 'to get this imported into docker.', code='31')
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
						 bzfile, code='31')
				self.log('\nRun:\n\nbunzip2 -c ' + bzfile +
						 ' | sudo docker import -\n\n' + 
						 'to get this imported into docker.',
						 code='31')
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


	def get_config(self,
	               module_id,
	               option,
	               default=None,
	               boolean=False,
	               forcedefault=False,
	               forcenone=False):
		"""Gets a specific config from the config files, allowing for a default.

		Handles booleans vs strings appropriately.

		module_id    - module id this relates to, eg com.mycorp.mymodule.mymodule
		option       - config item to set
		default      - default value if not set in files
		boolean      - whether this is a boolean value or not (default False)
		forcedefault - if set to true, allows you to override any value already set (default False)
		forcenone    - if set to true, allows you to set the value to None (default False)
		"""
		if module_id not in self.cfg.keys():
			self.cfg[module_id] = {}
		if not cfg['config_parser'].has_section(module_id):
			self.cfg['config_parser'].add_section(module_id)
		if not forcedefault and self.cfg['config_parser'].has_option(module_id, option):
			if boolean:
				self.cfg[module_id][option] = self.cfg['config_parser'].getboolean(module_id, option)
			else:
				self.cfg[module_id][option] = self.cfg['config_parser'].get(module_id, option)
		else:
			if default == None and forcenone != True:
				self.fail('Config item: ' + option + ':\nin module:\n[' + module_id + ']\nmust be set!\n\nOften this is a deliberate requirement to place in your ~/.shutit/config file.', throw_exception=False)
			self.cfg[module_id][option] = default


	def record_config(self):
		""" Put the config in a file in the target.
		"""
		self.send_file(self.cfg['build']['build_db_dir'] +
					   '/' + self.cfg['build']['build_id'] +
					   '/' + self.cfg['build']['build_id'] +
					   '.cfg', util.print_config(self.cfg))


	def get_emailer(self, cfg_section):
		"""Sends an email using the mailer
		"""
		from alerting import emailer
		return emailer.Emailer(cfg_section, self)


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
	cfg['action']               = {}
	cfg['build']                = {}
	cfg['build']['interactive'] = 1 # Default to true until we know otherwise
	cfg['build']['build_log']   = None
	cfg['build']['report']      = ''
	cfg['build']['debug']       = False
	cfg['build']['completed']   = False
	cfg['target']            = {}
	cfg['host']                 = {}
	cfg['repository']           = {}
	cfg['expect_prompts']       = {}
	cfg['users']                = {}
	cfg['dockerfile']           = {}
	cfg['build']['install_type_map'] = {'ubuntu':'apt',
	                                    'debian':'apt',
	                                    'steamos':'apt',
	                                    'red hat':'yum',
	                                    'centos':'yum',
	                                    'fedora':'yum',
	                                    'shutit':'src'}

	# If no LOGNAME available,
	cfg['host']['username'] = os.environ.get('LOGNAME', '')
	if cfg['host']['username'] == '':
		try:
			if os.getlogin() != '':
				cfg['host']['username'] = os.getlogin()
		except:
			import getpass
			cfg['host']['username'] = getpass.getuser()
		if cfg['host']['username'] == '':
			shutit_global.shutit.fail('LOGNAME not set in the environment, ' +
			                          'and login unavailable in python; ' +
			                          'please set to your username.', throw_exception=False)
	cfg['host']['real_user'] = os.environ.get('SUDO_USER',
											  cfg['host']['username'])
	cfg['build']['build_id'] = (socket.gethostname() + '_' +
	                            cfg['host']['real_user'] + '_' +
	                            str(time.time()) + '.' +
	                            str(datetime.datetime.now().microsecond))

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

