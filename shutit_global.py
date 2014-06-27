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
from shutit_module import ShutItFailException

def random_id(size=5, chars=string.ascii_letters + string.digits):
	"""Generates a random string of given size from the given chars.
	"""
	return ''.join(random.choice(chars) for _ in range(size))

class ShutIt(object):
	"""ShutIt build class.
	Represents an instance of a ShutIt build with associated config.
	"""

	def __init__(self, **kwargs):
		"""Constructor.
		Sets up:

		- pexpect_children   - 
		- shutit_modules     - 
		- shutit_main_dir    - directory in which shutit is located
		- cfg                - dictionary of configuration of build
		- cwd                - working directory of build
		- shutit_map         - 
		"""
		# These used to be in shutit_global, so we pass them in as args so
		# the original reference can be put in shutit_global
		self.pexpect_children = kwargs['pexpect_children']
		self.shutit_modules = kwargs['shutit_modules']
		self.shutit_main_dir = kwargs['shutit_main_dir']
		self.cfg = kwargs['cfg']
		self.cwd = kwargs['cwd']
		self.shutit_command_history = kwargs['shutit_command_history']
		self.shutit_map = kwargs['shutit_map']
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
		if len(self._default_check_exit) != 1:
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
		"""Returns default value of check_exit. See send_and_expect method.
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
                Defaults to the configured root_prompt.
		"""
		if expect == None:
			expect = self.cfg['expect_prompts']['root_prompt']
		self._default_expect[-1] = expect
		self._default_check_exit[-1] = check_exit

	# TODO: Manage exits of containers on error
	def fail(self, msg, child=None):
		"""Handles a failure, pausing if a pexpect child object is passed in.
		"""
		# Note: we must not default to a child here
		if child is not None:
			self.pause_point('Pause point on fail: ' + msg, child=child)
		print >> sys.stderr, 'ERROR!'
		print >> sys.stderr
		raise ShutItFailException(msg)

	def log(self, msg, code=None, pause=0, prefix=True, force_stdout=False):
		"""Logging function.

		code         - Colour code for logging. Ignored if we are in serve mode.
		pause        - Length of time to pause after logging (default: 0)
		prefix       - Whether to output logging prefix (LOG: <time>) (default: True)
		force_stdout - If we are not in debug, put this in stdout anyway (default: False)
		"""
		if prefix:
			prefix = 'LOG: ' + time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
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

	def send_and_expect(self,send,expect=None,child=None,timeout=3600,check_exit=None,fail_on_empty_before=True,record_command=None,exit_values=None,echo=None):
		"""Send string to the container, and wait until the expected string is seen before returning.

		Returns the pexpect return value
		
		child                      - pexpect child to issue command to.
		send                       - String to send, ie the command being issued.
		expect                     - String that we expect to see in the output. Usually a prompt.
		                             Defaults to currently-set expect string (see set_default_expect)
		timeout                    - Timeout on response (default=3600 seconds).
		check_exit                 - Whether to check the shell exit code of the passed-in command.
		                             If the exit value was non-zero an error is thrown.
					     (default=None, which takes the currently-configured check_exit value)
					     See also fail_on_empty_before.
		fail_on_empty_before       - If debug is set, fail on empty match output string (default=True)
		                             If this is set to False, then we don't check the exit value of the 
					     command.
		record_command             - Whether to record the command for output at end (default=True)
		                             As a safety measure, if the command matches any 'password's then we 
					     don't record it.
		exit_values                - Array of acceptable exit values (default [0])
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		cfg = self.cfg
		# If check_exit is not passed in
		# - if the expect matches the default, use the default check exit
		# - otherwise, default to doing the check
		if check_exit == None:
			if expect == self.get_default_expect():
				check_exit = self.get_default_check_exit()
			else:
				# If expect given doesn't match the defaults and no argument was passed in
				# (ie check_exit was passed in as None), set check_exit to true iff it
				# matches a prompt.
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
				if isinstance(cfg[i],dict):
					for j in cfg[i].keys():
						if (j == 'password' or j == 'passphrase') and cfg[i][j] == send:
							self.shutit_command_history.append('#redacted command, password')
							ok_to_record = False
							break
					if not ok_to_record:
						break
			if ok_to_record:
				self.shutit_command_history.append(send)
		if cfg['build']['debug']:
			self.log('================================================================================')
			self.log('Sending>>>' + send + '<<<')
			self.log('Expecting>>>' + str(expect) + '<<<')
		# Don't echo if echo passed in as False
		if echo == False:
			oldlog = child.logfile_send
			child.logfile_send = None
			child.sendline(send)
			expect_res = child.expect(expect,timeout)
			child.logfile_send = oldlog
		else:
			child.sendline(send)
			expect_res = child.expect(expect,timeout)
		if cfg['build']['debug']:
			self.log('child.before>>>' + child.before + '<<<')
			self.log('child.after>>>' + child.after + '<<<')
		if fail_on_empty_before == True:
			if child.before.strip() == '':
				shutit.fail('before empty after sending: ' + send + '\n\nThis is expected after some commands that take a password.\nIf so, add fail_on_empty_before=False to the send_and_expect call')
		elif fail_on_empty_before == False:
			# Don't check exit if fail_on_empty_before is False
			self.log('' + child.before + '<<<')
			check_exit = False
			for prompt in cfg['expect_prompts']:
				if prompt == expect:
					# Reset prompt
					self.setup_prompt('reset_tmp_prompt',child=child)
					self.revert_prompt('reset_tmp_prompt',expect,child=child)
		cfg['build']['last_output'] = child.before
		if check_exit == True:
			# store the output
			self._check_exit(send,expect,child,timeout,exit_values)
		return expect_res


	def _check_exit(self,send,expect=None,child=None,timeout=3600,exit_values=None):
		"""Internal function to check the exit value of the shell.
		"""
		expect = expect or self.get_default_expect()
		child = child or self.get_default_child()
		if exit_values is None:
			exit_values = ['0']
		# Don't use send_and_expect here (will mess up last_output)!
		child.sendline('echo EXIT_CODE:$?')
		child.expect(expect,timeout)
		res = self.get_re_from_child(child.before,'^EXIT_CODE:([0-9][0-9]?[0-9]?)$')
		#print 'RES', str(res), ' ', str(exit_values), ' ', str(res in exit_values)
		if res not in exit_values or res == None:
			if res == None:
				res = str(res)
			self.log('child.after: \n' + child.after + '\n')
			self.log('Exit value from command+\n' + send + '\nwas:\n' + res)
			msg = '\nWARNING: command:\n' + send + '\nreturned unaccepted exit code: ' + res + '\nIf this is expected, pass in check_exit=False or an exit_values array into the send_and_expect function call.'
			cfg['build']['report'] = cfg['build']['report'] + msg
			if cfg['build']['interactive'] >= 1:
				shutit.fail(msg + '\n\nPause point on exit_code != 0 (' + res + '). CTRL-C to quit',child=child)
			else:
				raise Exception('Exit value from command\n' + send + '\nwas:\n' + res)

	def run_script(self,script,expect=None,child=None,in_shell=True):
		"""Run the passed-in string 

		- script   - 
		- expect   - 
		- child    - 
		- in_shell - 
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
		self.send_and_expect('chmod +x /tmp/shutit_script.sh', expect, child)
		self.shutit_command_history.append('    ' + script.replace('\n', '\n    '))
		if in_shell:
			ret = self.send_and_expect('. /tmp/shutit_script.sh', expect, child)
		else:
			ret = self.send_and_expect('/tmp/shutit_script.sh', expect, child)
		self.send_and_expect('rm /tmp/shutit_script.sh', expect, child)
		return ret

	# TODO: test for this
	def send_file(self,path,contents,expect=None,child=None,binary=False):
		"""Sends the passed-in string as a file to the passed-in path on the container.

		- path     - Target location of file in container.
		- contents - Contents of file as a string. See binary.
		- expect   - 
		- child    - 
		- binary   - Don't log the file contents.
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		if cfg['build']['debug']:
			self.log('================================================================================')
			self.log('Sending file to' + path)
			if not binary:
				self.log('contents >>>' + contents + '<<<')
		# Prepare to send the contents as base64 so we don't have to worry about
		# special shell characters
		contents64 = base64.standard_b64encode(contents)
		child.sendline('base64 --decode > ' + path)
		child.expect('\r\n')
		# We have to batch the file up to avoid hitting pipe buffer limit. This
		# is 4k on modern machines (it seems), but we choose 1k for safety
		# https://github.com/pexpect/pexpect/issues/55
		batchsize = 1024
		for l in range(0, len(contents64), batchsize):
			child.sendline(contents64[l:l + batchsize])
		# Make sure we've synced the prompt before we send EOF. I don't know why
		# this requires three sendlines to generate 2x'\r\n'.
		# Note: we can't rely on a '\r\n' from the batching because the file
		# being sent may validly be empty.
		child.sendline()
		child.sendline()
		child.sendline()
		child.expect('\r\n\r\n')
		child.sendeof()
		# Done sending the file
		child.expect(expect)
		self._check_exit("send file to " + path,expect,child)

	def file_exists(self,filename,expect=None,child=None,directory=False):
		"""Return True if file exists, else False
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		test = 'test %s %s' % ('-d' if directory is True else '-a', filename)
		self.send_and_expect(test + ' && echo FILEXIST-""FILFIN || echo FILNEXIST-""FILFIN',expect=expect,child=child,check_exit=False,record_command=False)
		res = self.get_re_from_child(child.before,'^(FILEXIST|FILNEXIST)-FILFIN$')
		ret = False
		if res == 'FILEXIST':
			ret = True
		elif res == 'FILNEXIST':
			pass
		else:
			# Change to log?
			print repr('before>>>>:%s<<<< after:>>>>%s<<<<' % (child.before, child.after))
			self.pause_point('Did not see FIL(N)?EXIST in before',child)
		return ret

	def get_file_perms(self,filename,expect=None,child=None):
		"""Returns the file permission as an octal string.
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		cmd = 'stat -c %a ' + filename + r" | sed 's/.\(.*\)/\1/g'"
		self.send_and_expect(cmd,expect,child=child,check_exit=False)
		res = self.get_re_from_child(child.before,'([0-9][0-9][0-9])')
		return res

	def add_line_to_file(self,line,filename,expect=None,child=None,match_regexp=None,truncate=False,force=False,literal=False):
		"""Adds line to file if it doesn't exist (unless Force is set).
		Creates the file if it doesn't exist (unless truncate is set).
		Must be exactly the line passed in to match.
		Returns True if line added, False if not.
		If you have a lot of non-unique lines to add, it's a good idea to have a sentinel value to
		add first, and then if that returns true, force the remainder.
	
		- line         - Line to add.
		- filename     - Filename to add it to.
		- match_regexp - If supplied, a regexp to look for in the file instead of the line itself, handy if the line has awkward characters in it.
		- truncate     - Truncate or create the file before doing anything else
		- force        - Always write the line to the file
		- literal      - If true, then simply grep for the exact string without bash interpretation
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		# assume we're going to add it
		res = '0'
		bad_chars    = '"'
		tmp_filename = '/tmp/' + random_id()
		if match_regexp == None and re.match('.*[' + bad_chars + '].*',line) != None:
			shutit.fail('Passed problematic character to add_line_to_file.\nPlease avoid using the following chars: ' + bad_chars + '\nor supply a match_regexp argument.\nThe line was:\n' + line)
		# truncate file if requested, or if the file doesn't exist
		if truncate:
			self.send_and_expect('cat > ' + filename + ' <<< ""',expect=expect,child=child,check_exit=False)
		elif not self.file_exists(filename,expect=expect,child=child):
			# The above cat doesn't work so we touch the file if it doesn't exist already.
			self.send_and_expect('touch ' + filename,expect=expect,child=child,check_exit=False)
		elif not force:
			if literal:
				if match_regexp == None:
					self.send_and_expect("""grep -w '^""" + line + """$' """ + filename + ' > ' + tmp_filename,expect=expect,child=child,exit_values=['0','1'])
				else:
					self.send_and_expect("""grep -w '^""" + match_regexp + """$' """ + filename + ' > ' + tmp_filename,expect=expect,child=child,exit_values=['0','1'])
			else:
				if match_regexp == None:
					self.send_and_expect('grep -w "^' + line + '$" ' + filename + ' > ' + tmp_filename,expect=expect,child=child,exit_values=['0','1'])
				else:
					self.send_and_expect('grep -w "^' + match_regexp + '$" ' + filename + ' > ' + tmp_filename,expect=expect,child=child,exit_values=['0','1'])
			self.send_and_expect('cat ' + tmp_filename + ' | wc -l',expect=expect,child=child,exit_values=['0','1'],check_exit=False)
			res = self.get_re_from_child(child.before,'^([0-9]+)$')
		if res == '0' or force:
			self.send_and_expect('cat >> ' + filename + """ <<< '""" + line + """'""",expect=expect,child=child,check_exit=False)
			self.send_and_expect('rm -f ' + tmp_filename,expect=expect,child=child,exit_values=['0','1'])
			return True
		else:
			self.send_and_expect('rm -f ' + tmp_filename,expect=expect,child=child,exit_values=['0','1'])
			return False

	def add_to_bashrc(self,line,expect=None,child=None):
		"""Takes care of adding a line to everyone's bashrc.
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self.add_line_to_file(line,'/etc/bash.bashrc',expect=expect)
		return self.add_line_to_file(line,'/etc/profile',expect=expect)

	def user_exists(self,user,expect=None,child=None):
		"""Returns true if the specified username exists"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		exist = False
		if user == '': return exist
		ret = shutit.send_and_expect(
			'id %s && echo E""XIST || echo N""XIST' % user,
			expect=['NXIST','EXIST'], child=child
		)
		if ret:
			exist = True
		# sync with the prompt
		child.expect(expect)
		return exist

	def package_installed(self,package,expect=None,child=None):
		"""Returns True if we can be sure the package is installed.
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		if self.cfg['container']['install_type'] == 'apt':
			self.send_and_expect("""dpkg -l | awk '{print $2}' | grep "^""" + package + """$" | wc -l""",expect,check_exit=False)
		elif self.cfg['container']['install_type'] == 'yum':
			self.send_and_expect("""yum list installed | awk '{print $1}' | grep "^""" + package + """$" | wc -l""",expect,check_exit=False)
		else:
			return False
		if self.get_re_from_child(child.before,'^([0-9]+)$') != '0':
			return True
		else:
			return False

	def prompt_cfg(self,msg,sec,name,ispass=False):
		"""Prompt for a config value, possibly saving it to the user-level cfg
		"""
		cfg = self.cfg
		cfgstr = '[%s]/%s' % (sec, name)
		cp = cfg['config_parser']
		usercfg = os.path.join(cfg['shutit_home'], 'config')

		if not cfg['build']['interactive']:
			shutit.fail('ShutIt is not in interactive mode so cannnot prompt ' +
				'for values.')

		print util.colour('34', '\nPROMPTING FOR CONFIG: %s' % (cfgstr,))
		print util.colour('34', '\n' + msg + '\n')

		if cp.has_option(sec, name):
			whereset = cp.whereset(sec, name)
			if usercfg == whereset:
				self.fail(cfgstr + ' has already been set in the user ' +
					'config, edit ' + usercfg + ' directly to change it')
			for subcp, filename, fp in reversed(cp.layers):
				# Is the config file loaded after the user config file?
				if filename == whereset:
					self.fail(cfgstr + ' is being set in ' + filename + ', ' +
						'unable to override on a user config level')
				elif filename == usercfg:
					break
		else:
			# The item is not currently set so we're fine to do so
			pass
		if ispass:
			val = getpass.getpass('>> ')
		else:
			val = raw_input('>> ')
		is_excluded = (
			cp.has_option('save_exclude', sec) and
			name in cp.get('save_exclude', sec).split()
		)
		# TODO: ideally we would remember the prompted config item for this
		# invocation of shutit
		if not is_excluded:
			usercp = [
				subcp for subcp, filename, fp in cp.layers
				if filename == usercfg
			][0]
			if raw_input(util.colour('34',
					'Do you want to save this to your user settings? y/n: ')) == 'y':
				sec_toset, name_toset, val_toset = sec, name, val
			else:
				# Never save it
				if cp.has_option('save_exclude', sec):
					excluded = cp.get('save_exclude', sec).split()
				else:
					excluded = []
				excluded.append(name)
				excluded = ' '.join(excluded)
				sec_toset, name_toset, val_toset = 'save_exclude', sec, excluded
			if not usercp.has_section(sec_toset):
				usercp.add_section(sec_toset)
			usercp.set(sec_toset, name_toset, val_toset)
			usercp.write(open(usercfg, 'w'))
			cp.reload()
		return val

	def pause_point(self,msg,child=None,print_input=True,expect='',level=1):
		"""Inserts a pause in the build session which allows the user to try things out before continuing.
		"""
		child = child or self.get_default_child()
		cfg = self.cfg
		if not cfg['build']['interactive'] or cfg['build']['interactive'] < level:
			return
		# Sleep to try and make this the last thing we see before the prompt (not always the case)
		if child and print_input:
			print util.colour('31','\n\nPause point:\n\n') + msg + util.colour('31','\n\nYou can now type in commands and alter the state of the container.\nHit return to see the prompt\nHit CTRL and ] at the same time to continue with build\n\n')
			if print_input:
				if expect == '':
					expect = '@.*[#$]'
					print'\n\nexpect argument not supplied to pause_point, assuming "' + expect + '" is the regexp to expect\n\n'
			oldlog = child.logfile_send
			child.logfile_send = None
			child.interact()
			child.logfile_send = oldlog
		else:
			print msg
			print util.colour('31','\n\n[Hit return to continue]\n')
			raw_input('')

	def get_output(self,child=None):
		"""Helper function to get latest output."""
		child = child or self.get_default_child()
		return self.cfg['build']['last_output']


	def get_re_from_child(self, string, regexp):
		"""Get regular expression from the first of the lines passed in in string that matched.
		Returns None if none of the lines matched.
		"""
		cfg = self.cfg
		if cfg['build']['debug']:
			self.log('get_re_from_child:')
			self.log(string)
			self.log(regexp)
		lines = string.split('\r\n')
		for l in lines:
			if cfg['build']['debug']:
				self.log('trying: ' + l + ' against regexp: ' + regexp)
			match = re.match(regexp,l)
			if match != None:
				if cfg['build']['debug']:
					self.log('returning: ' + match.group(1))
				return match.group(1)
		return None

	def send_and_get_output(self,send,expect=None,child=None):
		"""Returns the output of a command run.
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self.send_and_expect(send,check_exit=False)
		return shutit.get_default_child().before.strip(send)


	def install(self,package,child=None,expect=None,options=None,timeout=3600):
		"""Distro-independent install function.
		Takes a package name and runs the relevant install function.
		Returns true if all ok (ie it's installed), else false
		"""
		#TODO: Temporary failure resolving
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		if options is None: options = {}
		# TODO: maps of packages
		# TODO: config of maps of packages
		install_type = self.cfg['container']['install_type']
		if install_type == 'apt':
			cmd = 'apt-get install'
			if self.cfg['build']['debug']:
				opts = options['apt'] if 'apt' in options else '-y'
			else:
				opts = options['apt'] if 'apt' in options else '-qq -y'
		elif install_type == 'yum':
			cmd = 'yum install'
			opts = options['yum'] if 'yum' in options else '-y'
		else:
			# Not handled
			return False
		# Get mapped package.
		package = package_map.map_package(package,self.cfg['container']['install_type'])
		self.send_and_expect('%s %s %s' % (cmd,opts,package),expect,timeout=timeout)
		return True

	def remove(self,package,child=None,expect=None,options=None,timeout=3600):
		"""Distro-independent remove function.
		Takes a package name and runs relevant remove function.
		Returns true if all ok (ie it's installed now), else false
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		if options is None: options = {}
		# TODO: maps of packages
		# TODO: config of maps of packages
		install_type = self.cfg['container']['install_type']
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
		package = package_map.map_package(package,self.cfg['container']['install_type'])
		self.send_and_expect('%s %s %s' % (cmd,opts,package),expect,timeout=timeout)
		return True


	def setup_prompt(self,prompt_name,prefix='TMP',child=None,set_default_expect=True):
		"""Use this when you've opened a new shell to set the PS1 to something sane.
		"""
		child = child or self.get_default_child()
		local_prompt = 'SHUTIT_' + prefix + '#' + random_id() + '>'
		shutit.cfg['expect_prompts'][prompt_name] = '\r\n' + local_prompt
		self.send_and_expect(
			("SHUTIT_BACKUP_PS1_%s=$PS1 && PS1='%s' && unset PROMPT_COMMAND") %
				(prompt_name, local_prompt),
			expect=self.cfg['expect_prompts'][prompt_name],
			fail_on_empty_before=False,timeout=5)
		if set_default_expect:
			shutit.log('Resetting default expect to: ' + shutit.cfg['expect_prompts'][prompt_name])
			self.set_default_expect(shutit.cfg['expect_prompts'][prompt_name])

	def handle_revert_prompt(self,expect,prompt_name,child=None):
		"""Deprecated. Do not use.
		"""
		self.revert_prompt(prompt_name,new_expect=expect,child=child)

	def revert_prompt(self,old_prompt_name,new_expect=None,child=None):
		"""Reverts the prompt to the previous value (passed-in).

		It should be fairly rare to need this. Most of the time you would just
		exit a subshell rather than resetting the prompt.
		"""
		child = child or self.get_default_child()
		expect = new_expect or self.get_default_expect()
		self.send_and_expect(
			('PS1="${SHUTIT_BACKUP_PS1_%s}" && unset SHUTIT_BACKUP_PS1_%s') %
				(old_prompt_name, old_prompt_name),
			expect=expect,check_exit=False,fail_on_empty_before=False)

	def get_distro_info(self,child=None):
		"""Get information about which distro we are using.

		Fails if distro could not be determined.
		Should be called with the container is started up, and uses as core info as possible.
		"""
		child = child or self.get_default_child()
		cfg = self.cfg
		cfg['container']['install_type']      = ''
		cfg['container']['distro']            = ''
		cfg['container']['distro_version']    = ''
		install_type_map = {'ubuntu':'apt','debian':'apt','red hat':'yum','centos':'yum','fedora':'yum'}
		if self.package_installed('lsb_release'):
			self.send_and_expect('lsb_release -a')
			s = self.get_re_from_child(child.before,'^Distributor ID:[\s]*\(.*)$')
			if s:
				cfg['container']['distro']       = s.lower()
				cfg['container']['install_type'] = install_type_map[s.lower()]
			# TODO: version
			#version = self.get_re_from_child(child.before,'^Release:[\s]*(.*)$')
		else:
			for key in install_type_map.keys():
				self.send_and_expect('cat /etc/issue | grep -i "' + key + '" | wc -l', check_exit=False)
				if self.get_re_from_child(child.before,'^([0-9]+)$') == '1':
					cfg['container']['distro']       = key
					cfg['container']['install_type'] = install_type_map[key]
					break
		if cfg['container']['install_type'] == '' or cfg['container']['distro'] == '':
			shutit.fail('Could not determine Linux distro information. Please inform maintainers.')

	def set_password(self,password,child=None,expect=None):
		"""Sets the password for the current user.
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		cfg = self.cfg
		self.install('passwd')
		if cfg['container']['install_type'] == 'apt':
			self.send_and_expect('passwd',expect='Enter new',child=child,check_exit=False)
			self.send_and_expect(password,child=child,expect='Retype new',check_exit=False,echo=False)
			self.send_and_expect(password,child=child,expect=expect,echo=False)
		elif cfg['container']['install_type'] == 'yum':
			self.send_and_expect('passwd',child=child,expect='ew password',check_exit=False)
			self.send_and_expect(password,child=child,expect='ew password',check_exit=False,echo=False)
			self.send_and_expect(password,child=child,expect=expect,echo=False)


	def is_user_id_available(self,user_id,child=None,expect=None):
		"""Determine whether a user_id for a user is available.
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self.send_and_expect('cut -d: -f3 /etc/paswd | grep -w ^' + user_id + '$ | wc -l',child=child,expect=expect,check_exit=False)
		if self.get_re_from_child(child.before,'^([0-9]+)$') == '1':
			return False
		else:
			return True

	def push_repository(self,repository,docker_executable='docker.io',child=None,expect=None):
		"""Pushes the repository.

		- repository        - 
		- docker_executable -
		"""
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		send = docker_executable + ' push ' + repository
		expect_list = ['Username','Password','Email',expect]
		timeout=99999
		self.log('Running: ' + send,force_stdout=True,prefix=False)
		res = self.send_and_expect(send,expect=expect_list,child=child,timeout=timeout,check_exit=False,fail_on_empty_before=False)
		while True:
			if res == 3:
				break
			elif res == 0:
				res = self.send_and_expect(cfg['repository']['user'],child=child,expect=expect_list,timeout=timeout,check_exit=False,fail_on_empty_before=False)
			elif res == 1:
				res = self.send_and_expect(cfg['repository']['password'],child=child,expect=expect_list,timeout=timeout,check_exit=False,fail_on_empty_before=False)
			elif res == 2:
				res = self.send_and_expect(cfg['repository']['email'],child=child,expect=expect_list,timeout=timeout,check_exit=False,fail_on_empty_before=False)

	def do_repository_work(self,repo_name,expect=None,docker_executable='docker',password=None,force=None):
		"""Commit, tag, push, tar the container based on the configuration we have.
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

		child  = self.pexpect_children['host_child']
		expect = cfg['expect_prompts']['real_user_prompt']
		server = cfg['repository']['server']
		repo_user   = cfg['repository']['user']

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
			shutit.fail('Could not form valid repository name')
		if (export or save) and not repository_tar:
			shutit.fail('Could not form valid tar name')

		if server:
			repository = '%s/%s' % (server, repository)

		if cfg['repository']['suffix_date']:
			suffix_date = time.strftime(cfg['repository']['suffix_format'])
			repository = '%s%s' % (repository, suffix_date)
			repository_tar = '%s%s' % (repository_tar, suffix_date)

		if server == '' and len(repository) > 30 and push:
			shutit.fail("""repository name: '""" + repository + """' too long. If using suffix_date consider shortening""")

		# Commit image
		# Only lower case accepted
		repository = repository.lower()
		if self.send_and_expect('SHUTIT_TMP_VAR=`' + docker_executable + ' commit ' + cfg['container']['container_id'] + '`',expect=[expect,'assword'],child=child,timeout=99999,check_exit=False) == 1:
			self.send_and_expect(cfg['host']['password'],expect=expect,check_exit=False,record_command=False,child=child)
		self.send_and_expect('echo $SHUTIT_TMP_VAR && unset SHUTIT_TMP_VAR',expect=expect,check_exit=False,child=child)
		image_id = child.before.split('\r\n')[1]
		if not image_id:
			shutit.fail('failed to commit to ' + repository + ', could not determine image id')

		# Tag image
		cmd = docker_executable + ' tag ' + image_id + ' ' + repository
		self.send_and_expect(cmd,child=child,expect=expect,check_exit=False)
		if export or save:
			self.pause_point('We are now exporting the container to a bzipped tar file, as configured in \n[repository]\ntar:yes',print_input=False,child=child,level=3)
			self.log('\nDepositing bzip2 of exported container into ' + bzfile)
			if export:
				bzfile = cfg['host']['resources_dir'] + '/' + repository_tar + 'export.tar.bz2'
				if self.send_and_expect(docker_executable + ' export ' + cfg['container']['container_id'] + ' | bzip2 - > ' + bzfile,expect=[expect,'assword'],timeout=99999,child=child) == 1:
					self.send_and_expect(password,expect=expect,child=child)
				self.log('\nDeposited bzip2 of exported container into ' + bzfile,code='31')
				self.log('\nRun:\n\nbunzip2 -c ' + bzfile + ' | sudo docker import -\n\nto get this imported into docker.',code='31')
				cfg['build']['report'] = cfg['build']['report'] + '\nDeposited bzip2 of exported container into ' + bzfile
				cfg['build']['report'] = cfg['build']['report'] + '\nRun:\n\nbunzip2 -c ' + bzfile + ' | sudo docker import -\n\nto get this imported into docker.'
			if save:
				bzfile = cfg['host']['resources_dir'] + '/' + repository_tar + 'save.tar.bz2'
				if self.send_and_expect(docker_executable + ' save ' + cfg['container']['container_id'] + ' | bzip2 - > ' + bzfile,expect=[expect,'assword'],timeout=99999,child=child) == 1:
					self.send_and_expect(password,expect=expect,child=child)
				self.log('\nDeposited bzip2 of exported container into ' + bzfile,code='31')
				self.log('\nRun:\n\nbunzip2 -c ' + bzfile + ' | sudo docker import -\n\nto get this imported into docker.',code='31')
				cfg['build']['report'] = cfg['build']['report'] + '\nDeposited bzip2 of exported container into ' + bzfile
				cfg['build']['report'] = cfg['build']['report'] + '\nRun:\n\nbunzip2 -c ' + bzfile + ' | sudo docker import -\n\nto get this imported into docker.'
		if cfg['repository']['push'] == True:
			# Pass the child explicitly as it's the host child.
			self.push_repository(repository,docker_executable=docker_executable,expect=expect,child=child)
			cfg['build']['report'] = cfg['build']['report'] + 'Pushed repository: ' + repository

	# Pass-through function for convenience
	def get_config(self,module_id,option,default,boolean=False):
		util.get_config(self.cfg,module_id,option,default,boolean)

	# Put the config in a file in the container.
	def record_config(self):
		self.send_file(self.cfg['build']['build_db_dir'] + '/' + self.cfg['build']['build_id'] + '/' + self.cfg['build']['build_id'] + '.cfg',util.print_config(self.cfg))

	def handle_login(self,prompt_name,child=None):
		"""Deprecated. Do not use.
		"""
		self.setup_prompt(prompt_name, child=child)
	


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

	pexpect_children = {}
	shutit_map = {}
	shutit_modules   = set()
	shutit_command_history = []
	# Store the root directory of this application.
	# http://stackoverflow.com/questions/5137497/find-current-directory-and-files-directory
	shutit_main_dir = os.path.abspath(os.path.dirname(__file__))
	cwd = os.getcwd()
	cfg = {}
	cfg['action']               = {}
	cfg['build']                = {}
	cfg['build']['interactive'] = 1 # Default to true until we know otherwise
	cfg['build']['build_log']   = None
	cfg['build']['report']      = ''
	cfg['container']            = {}
	cfg['host']                 = {}
	cfg['repository']           = {}
	cfg['expect_prompts']       = {}
	cfg['users']                = {}

	# If no LOGNAME available,
	cfg['host']['username'] = os.environ.get('LOGNAME','')
	if cfg['host']['username'] == '':
		shutit_global.shutit.fail('LOGNAME not set in the environment, please set to your username.')
	cfg['host']['real_user'] = os.environ.get('SUDO_USER', cfg['host']['username'])
	cfg['build']['build_id'] = socket.gethostname() + '_' + cfg['host']['real_user'] + '_' + str(time.time())

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

