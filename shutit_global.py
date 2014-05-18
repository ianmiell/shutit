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

def random_id(size=5, chars=string.ascii_letters + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

class ShutIt(object):

	_default_child      = [None]
	_default_expect     = [None]
	_default_check_exit = [None]

	def __init__(self, **kwargs):
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

	# These two get called automatically by the metaclass decorator in
	# shutit_module when a module method is called.
	# This allows setting defaults for the 'scope' of a method.
	def module_method_start(self):
		if self._default_child[-1] is not None:
			self._default_child.append(self._default_child[-1])
		if self._default_expect[-1] is not None:
			self._default_expect.append(self._default_expect[-1])
		if self._default_check_exit[-1] is not None:
			self._default_check_exit.append(self._default_check_exit[-1])
	def module_method_end(self):
		if len(self._default_child) != 1:
			self._default_child.pop()
		if len(self._default_expect) != 1:
			self._default_expect.pop()
		if len(self._default_check_exit) != 1:
			self._default_check_exit.pop()

	def get_default_child(self):
		if self._default_child[-1] is None:
			util.fail("Couldn't get default child")
		return self._default_child[-1]
	def get_default_expect(self):
		if self._default_expect[-1] is None:
			util.fail("Couldn't get default expect")
		return self._default_expect[-1]
	def get_default_check_exit(self):
		if self._default_check_exit[-1] is None:
			util.fail("Couldn't get default check exit")
		return self._default_check_exit[-1]
	def set_default_child(self, child):
		self._default_child[-1] = child
	def set_default_expect(self, expect, check_exit=True):
		self._default_expect[-1] = expect
		self._default_check_exit[-1] = check_exit

	def log(self, msg, code=None, pause=0, prefix=True, force_stdout=False):
		if prefix:
			prefix = 'LOG: ' + time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
			msg = prefix + ' ' + str(msg)
		# Don't colour message if we are in serve mode.
		if code != None and not self.cfg['action']['serve']:
			msg = util.colour(code, msg)
		if self.cfg['build']['debug'] or force_stdout:
			print >> sys.stdout, msg
		if self.cfg['build']['build_log']:
			print >> cfg['build']['build_log'], msg
			self.cfg['build']['build_log'].flush()
		time.sleep(pause)

	# Wrapper for send and expect where convenient.
	# Helpful for debugging.
	# Returns the expect return value
	#
	# child                      - pexpect child to issue command to.
	# send                       - String to send, ie the command being issued.
	# expect                     - String that we expect to see in the output. Usually a prompt.
	# timeout                    - Timeout on response (default=3600 seconds).
	# check_exit                 - Whether the check the shell exit code of the command. If the exit value was non-zero an error is thrown. (default=True)
	# fail_on_empty_before       - If debug is set, fail on empty before match (default=True)
	# record_command             - Whether to record the command for output at end (default=True)
	# exit_values                - Array of acceptable exit values (default [0])
	def send_and_expect(self,send,expect=None,child=None,timeout=3600,check_exit=None,fail_on_empty_before=True,record_command=True,exit_values=None):
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
				check_exit = True
		# If the command matches any 'password's then don't record
		ok_to_record = False
		if record_command:
			ok_to_record = True
			for i in cfg.keys():
				if isinstance(cfg[i],dict):
					for j in cfg[i].keys():
						if j == 'password' and cfg[i][j] == send:
							self.shutit_command_history.append('#redacted command, password')
							ok_to_record = False
							break
					if not ok_to_record:
						break
			if ok_to_record:
				self.shutit_command_history.append(send)
		else:
			self.shutit_command_history.append('#redacted command')
		if cfg['build']['debug']:
			self.log('================================================================================')
			self.log('Sending>>>' + send + '<<<')
			self.log('Expecting>>>' + str(expect) + '<<<')
		# Race conditions have been seen - might want to remove this
		time.sleep(cfg['build']['command_pause'])
		child.sendline(send)
		expect_res = child.expect(expect,timeout)
		if cfg['build']['debug']:
			self.log('child.before>>>' + child.before + '<<<')
			self.log('child.after>>>' + child.after + '<<<')
		if fail_on_empty_before == True:
			if child.before.strip() == '':
				util.fail('before empty after sending: ' + send + '\n\nThis is expected after some commands that take a password.\nIf so, add fail_on_empty_before=False to the send_and_expect call')
		elif fail_on_empty_before == False:
			# Don't check exit if fail_on_empty_before is False
			self.log('' + child.before + '<<<')
			check_exit = False
			for prompt in cfg['expect_prompts']:
				if prompt == expect:
					# Reset prompt
					self.handle_login('reset_tmp_prompt',child=child)
					self.handle_revert_prompt(child,expect,'reset_tmp_prompt')
		if check_exit == True:
			self._check_exit(send,expect,child,timeout,exit_values)
		return expect_res


	def _check_exit(self,send,expect=None,child=None,timeout=3600,exit_values=None):
		expect = expect or self.get_default_expect()
		child = child or self.get_default_child()
		if exit_values is None:
			exit_values = ['0']
		child.sendline('echo EXIT_CODE:$?')
		child.expect(expect,timeout)
		res = self.get_re_from_child(child.before,'^EXIT_CODE:([0-9][0-9]?[0-9]?)$')
		#print 'RES', str(res), ' ', str(exit_values), ' ', str(res in exit_values)
		if res not in exit_values or res == None:
			if res == None:
				res = str(res)
			self.log(util.red('child.after: \n' + child.after + '\n'))
			self.log(util.red('Exit value from command+\n' + send + '\nwas:\n' + res))
			msg = '\nWARNING: command:\n' + send + '\nreturned unaccepted exit code: ' + res + '\nIf this is expected, pass in check_exit=False or an exit_values array into the send_and_expect function call.\nIf you want to error on these errors, set the config:\n[build]\naction_on_ret_code:error'
			cfg['build']['report'] = cfg['build']['report'] + msg
			if cfg['build']['action_on_ret_code'] == 'error':
				util.fail(msg + '\n\nPause point on exit_code != 0. CTRL-C to quit',child=child)
				#raise Exception('Exit value from command\n' + send + '\nwas:\n' + res)

	def run_script(self,script,expect=None,child=None,is_bash=True):
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		lines = script.split('\n')
		while len(lines) > 0 and re.match('^[ \t]*$', lines[0]):
			lines = lines[1:]
		while len(lines) > 0 and re.match('^[ \t]*$', lines[-1]):
			lines = lines[:-1]
		if len(lines) == 0:
			return True
		script = '\n'.join(lines)
		script = textwrap.dedent(script)
		if is_bash:
			script = ('#!/bin/bash\nset -o verbose\nset -o errexit\n' +
				'set -o nounset\n\n' + script)
		self.send_file('/tmp/shutit_script.sh', script)
		self.send_and_expect('chmod +x /tmp/shutit_script.sh', expect, child)
		self.shutit_command_history.append('    ' + script.replace('\n', '\n    '))
		ret = self.send_and_expect('/tmp/shutit_script.sh', expect, child)
		self.send_and_expect('rm /tmp/shutit_script.sh', expect, child)
		return ret

	# TODO: Comments needed here, as well as example in template. And a test?
	def send_file(self,path,contents,expect=None,child=None,binary=False):
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		if cfg['build']['debug']:
			self.log('================================================================================')
			self.log('Sending file to' + path)
			if not binary:
				self.log('contents >>>' + contents + '<<<')
		contents64 = base64.standard_b64encode(contents)
		child.sendline('base64 --decode > ' + path)
		child.sendline(contents64)
		child.sendeof()
		child.expect(expect)
		self._check_exit("send file to " + path,expect,child)

	# Return True if file exists, else False
	def file_exists(self,filename,expect=None,child=None,directory=False):
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		test = 'test %s %s' % ('-d' if directory is True else '-a', filename)
		self.send_and_expect(test+' && echo FILEXIST-""FILFIN || echo FILNEXIST-""FILFIN','-FILFIN',child=child,check_exit=False,record_command=False)
		res = self.get_re_from_child(child.before,'^(FILEXIST|FILNEXIST)$')
		ret = False
		if res == 'FILEXIST':
			ret = True
		elif res == 'FILNEXIST':
			pass
		else:
			# Change to log?
			print repr('before>>>>:%s<<<< after:>>>>%s<<<<' % (child.before, child.after))
			self.pause_point('Did not see FIL(N)?EXIST in before',child)
		child.expect(expect)
		return ret

	# Returns the file permission as an octal
	def get_file_perms(self,filename,expect=None,child=None):
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		cmd = 'stat -c %a ' + filename + r" | sed 's/.\(.*\)/\1/g'"
		self.send_and_expect(cmd,expect,child=child,check_exit=False,record_command=False)
		res = self.get_re_from_child(child.before,'([0-9][0-9][0-9])')
		return res

	# Adds line to file if it doesn't exist (unless Force is set).
	# Creates the file if it doesn't exist (unless truncate is set).
	# Must be exactly the line passed in to match.
	# Returns True if line added, False if not.
	# If you have a lot of non-unique lines to add,
	# it's a good idea to have a sentinel value to
	# add first, and then if that returns true,
	# force the remainder.
	#
	# match_regexp - if supplied, a regexp to look for in the file instead of the line itself, handy if the line has awkward characters in it.
	# force        - always write the line to the file
	# truncate     - truncate or create the file before doing anything else
	# literal      - if true, then simply grep for the exact
	#                string without bash interpretation
	def add_line_to_file(self,line,filename,expect=None,child=None,match_regexp=None,truncate=False,force=False,literal=False):
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		# assume we're going to add it
		res = '0'
		bad_chars    = '"'
		tmp_filename = '/tmp/' + random_id()
		if match_regexp == None and re.match('.*[' + bad_chars + '].*',line) != None:
			util.fail('Passed problematic character to add_line_to_file.\nPlease avoid using the following chars: ' + bad_chars + '\nor supply a match_regexp argument.\nThe line was:\n' + line)
		# truncate file if requested, or if the file doesn't exist
		if truncate:
			self.send_and_expect('cat > ' + filename + ' <<< ""',expect,child=child,check_exit=False)
		elif not self.file_exists(filename,expect,child):
			# The above cat doesn't work so we touch the file if it doesn't exist already.
			self.send_and_expect('touch ' + filename,expect,child,check_exit=False)
		elif not force:
			if literal:
				if match_regexp == None:
					self.send_and_expect("""grep -w '^""" + line + """$' """ + filename + ' > ' + tmp_filename,expect,child=child,exit_values=['0','1'],record_command=False)
				else:
					self.send_and_expect("""grep -w '^""" + match_regexp + """$' """ + filename + ' > ' + tmp_filename,expect,child=child,exit_values=['0','1'],record_command=False)
			else:
				if match_regexp == None:
					self.send_and_expect('grep -w "^' + line + '$" ' + filename + ' > ' + tmp_filename,expect,child=child,exit_values=['0','1'],record_command=False)
				else:
					self.send_and_expect('grep -w "^' + match_regexp + '$" ' + filename + ' > ' + tmp_filename,expect,child=child,exit_values=['0','1'],record_command=False)
			self.send_and_expect('cat ' + tmp_filename + ' | wc -l',expect,child=child,exit_values=['0','1'],record_command=False,check_exit=False)
			res = self.get_re_from_child(child.before,'^([0-9]+)$')
		if res == '0' or force:
			self.send_and_expect('cat >> ' + filename + """ <<< '""" + line + """'""",expect,child=child,check_exit=False)
			self.send_and_expect('rm -f ' + tmp_filename,expect,child=child,exit_values=['0','1'],record_command=False)
			return True
		else:
			self.send_and_expect('rm -f ' + tmp_filename,expect,child=child,exit_values=['0','1'],record_command=False)
			return False

	# Takes care of adding a line to everyone's bashrc
	def add_to_bashrc(self,line,expect=None,child=None):
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self.add_line_to_file(line,'/etc/bash.bashrc',expect=expect)
		return self.add_line_to_file(line,'/etc/profile',expect=expect)

	# Return True if we can be sure the package is installed.
	def package_installed(self,package,expect=None,child=None):
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		if self.cfg['container']['install_type'] == 'apt':
			self.send_and_expect("""dpkg -l | awk '{print $2}' | grep "^""" + package + """$" | wc -l""",expect,check_exit=False,record_command=False)
		elif self.cfg['container']['install_type'] == 'yum':
			self.send_and_expect("""yum list installed | awk '{print $1}' | grep "^""" + package + """$" | wc -l""",expect,check_exit=False,record_command=False)
		else:
			return False
		if self.get_re_from_child(child.before,'^([0-9]+)$') != '0':
			return True
		else:
			return False



	# Inserts a pause in the expect session which allows the user to try things out
	def pause_point(self,msg,child=None,print_input=True,expect=''):
		child = child or self.get_default_child()
		cfg = self.cfg
		if not cfg['build']['interactive']:
			return
		# Sleep to try and make this the last thing we see before the prompt (not always the case)
		if child and print_input:
			print util.red('\n\nPause point:\n\n') + msg + util.red('\n\nYou can now type in commands and alter the state of the container.\nHit return to see the prompt\nHit CTRL and ] at the same time to continue with build\n\n')
			if print_input:
				if expect == '':
					expect = '@.*[#$]'
					print'\n\nexpect argument not supplied to pause_point, assuming "' + expect + '" is the regexp to expect\n\n'
			child.interact()
		else:
			print msg
			print util.red('\n\n[Hit return to continue]\n')
			raw_input('')

	# Get regular expression from lines
	# Returns None if none matched.
	def get_re_from_child(self, string, regexp):
		cfg = self.cfg
		if cfg['build']['debug']:
			self.log('get_re_from_child:')
			self.log(string)
			self.log(regexp)
		lines = string.split('\r\n')
		for l in lines:
			if cfg['build']['debug']:
				self.log('trying: ' + l)
			match = re.match(regexp,l)
			if match != None:
				if cfg['build']['debug']:
					self.log('returning: ' + match.group(1))
				return match.group(1)
		return None

	# Returns the output of a command
	def get_output(self,send,expect=None,child=None):
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self.send_and_expect(send,check_exit=False)
		return shutit.get_default_child().before.strip(send)


	# Distro-independent install function.
	# Takes a package name and runs
	# Returns true if all ok (ie it's installed now), else false
	def install(self,package,child=None,expect=None,options=None,timeout=3600):
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		if options is None: options = {}
		# TODO: maps of packages
		# TODO: config of maps of packages
		install_type = self.cfg['container']['install_type']
		if install_type == 'apt':
			cmd = 'apt-get install'
			opts = options['apt'] if 'apt' in options else '-qq -y'
		elif install_type == 'yum':
			cmd = 'yum install'
			opts = options['yum'] if 'yum' in options else '-y'
		else:
			# Not handled
			return False
		self.send_and_expect('%s %s %s' % (cmd,opts,package),expect,timeout=timeout)
		return True

	# Distro-independent remove function.
	# Takes a package name and runs
	# Returns true if all ok (ie it's installed now), else false
	def remove(self,package,child=None,expect=None,options=None,timeout=3600):
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
		self.send_and_expect('%s %s %s' % (cmd,opts,package),expect,timeout=timeout)
		return True

	def handle_login(self,prompt_name,child=None):
		child = child or self.get_default_child()
		local_prompt = 'SHUTIT_TMP_' + prompt_name + '#' + random_id() + '>'
		self.cfg['expect_prompts'][prompt_name] = '\r\n' + local_prompt
		self.send_and_expect(
			("SHUTIT_BACKUP_PS1_%s=$PS1 &&" +
			"export SHUTIT_PROMPT_COMMAND_BACKUP_%s=$PROMPT_COMMAND && " +
			"PS1='%s' && unset PROMPT_COMMAND") %
				(prompt_name, prompt_name, local_prompt),
			expect=self.cfg['expect_prompts'][prompt_name],
			record_command=False,fail_on_empty_before=False)

	def handle_revert_prompt(self,expect,prompt_name,child=None):
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self.send_and_expect(
			('PS1="${SHUTIT_BACKUP_PS1_%s}" && ' +
			'unset SHUTIT_PROMPT_COMMAND_BACKUP_%s && ' +
			'unset SHUTIT_BACKUP_PS1_%s') %
				(prompt_name, prompt_name, prompt_name),
			expect=expect,check_exit=False,record_command=False,fail_on_empty_before=False)

	# Fails if distro could not be determined.
	# Should be called with the container is started up.
	def get_distro_info(self,child=None,outer_expect=None):
		child = child or self.get_default_child()
		cfg = self.cfg
		outer_expect = outer_expect or self.get_default_expect()
		cfg['container']['install_type']      = ''
		cfg['container']['distro']            = ''
		cfg['container']['distro_version']    = ''
		install_type_map = {'ubuntu':'apt','debian':'apt','red hat':'yum','centos':'yum','fedora':'yum'}
		self.handle_login('tmp_prompt')
		self.set_default_expect(cfg['expect_prompts']['tmp_prompt'])
		for key in install_type_map.keys():
			child.sendline('cat /etc/issue | grep -i "' + key + '" | wc -l')
			child.expect(cfg['expect_prompts']['tmp_prompt'])
			if self.get_re_from_child(child.before,'^([0-9]+)$') == '1':
				cfg['container']['distro']       = key
				cfg['container']['install_type'] = install_type_map[key]
				break
		self.set_password(cfg['container']['password'],expect=cfg['expect_prompts']['tmp_prompt'])
		cfg['expect_prompts']['real_user_prompt'] = '\r\n.*?' + cfg['host']['real_user'] + '@.*:'
		if cfg['container']['install_type'] == '' or cfg['container']['distro'] == '':
			util.fail('Could not determine Linux distro information. Please inform maintainers.')
		self.handle_revert_prompt(outer_expect,'tmp_prompt')

	# Sets the password
	def set_password(self,password,child=None,expect=None):
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		cfg = self.cfg
		if cfg['container']['install_type'] == 'apt':
			self.send_and_expect('passwd',expect='Enter new',child=child,check_exit=False)
			self.send_and_expect(password,child=child,expect='Retype new',check_exit=False,record_command=False)
			self.send_and_expect(password,child=child,expect=expect,record_command=False)
		elif cfg['container']['install_type'] == 'yum':
			self.send_and_expect('passwd',child=child,expect='ew password',check_exit=False,record_command=False)
			self.send_and_expect(password,child=child,expect='ew password',check_exit=False,record_command=False)
			self.send_and_expect(password,child=child,expect=expect,record_command=False)


	# Determine whether a user_id for a user is available
	def is_user_id_available(self,user_id,child=None,expect=None):
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		self.send_and_expect('cut -d: -f3 /etc/paswd | grep -w ^' + user_id + '$ | wc -l',child=child,expect=expect,check_exit=False,record_command=False)
		if self.get_re_from_child(child.before,'^([0-9]+)$') == '1':
			return False
		else:
			return True

	# Sets up a base prompt
	def setup_prompt(self,prefix,prompt_name,child=None):
		child = child or self.get_default_child()
		cfg = self.cfg
		local_prompt = prefix + '#' + random_id() + '>'
		child.sendline('SHUTIT_BACKUP_PS1=$PS1 && unset PROMPT_COMMAND && PS1="' + local_prompt + '"')
		cfg['expect_prompts'][prompt_name] = '\r\n' + local_prompt
		child.expect(cfg['expect_prompts'][prompt_name])

	# expect must be a string
	def push_repository(self,repository,docker_executable,child=None,expect=None):
		child = child or self.get_default_child()
		expect = expect or self.get_default_expect()
		send = docker_executable + ' push ' + repository
		expect_list = ['Pushing','Buffering','Username:','Password:','Email:',expect]
		timeout=99999
		res = self.send_and_expect(send,expect=expect_list,child=child,timeout=timeout,check_exit=False)
		while True:
			if res == 5:
				break
			elif res == 2:
				res = self.send_and_expect(cfg['repository']['user'],child=child,expect=expect_list,timeout=timeout,check_exit=False)
			elif res == 3:
				res = self.send_and_expect(cfg['repository']['password'],child=child,expect=expect_list,timeout=timeout,check_exit=False)
			elif res == 4:
				res = self.send_and_expect(cfg['repository']['email'],child=child,expect=expect_list,timeout=timeout,check_exit=False)
			else:
				res = child.expect(expect_list,timeout=timeout)

	# Commit, tag, push, tar etc..
	# expect must be a string
	def do_repository_work(self,repo_name,expect=None,docker_executable='docker',password=None):
		expect = expect or self.get_default_expect()
		cfg = self.cfg
		if not cfg['repository']['do_repository_work']:
			return
		child = self.pexpect_children['host_child']
		server = cfg['repository']['server']
		user = cfg['repository']['user']

		if user and repo_name:
			repository = '%s/%s' % (user, repo_name)
			repository_tar = '%s_%s' % (user, repo_name)
		elif user:
			repository = repository_tar = user
		elif repo_name:
			repository = repository_tar = repo_name
		else:
			repository = repository_tar = ''

		if not repository:
			util.fail('Could not form valid repository name')
		if cfg['repository']['tar'] and not repository_tar:
			util.fail('Could not form valid tar name')

		if server:
			repository = '%s/%s' % (server, repository)

		if cfg['repository']['suffix_date']:
			suffix_date = time.strftime(cfg['repository']['suffix_format'])
			repository = '%s_%s' % (repository, suffix_date)
			repository_tar = '%s_%s' % (repository_tar, suffix_date)

		if server == '' and len(repository) > 30:
			util.fail("""repository name: '""" + repository + """' too long. If using suffix_date consider shortening""")

		# Only lower case accepted
		repository = repository.lower()
		# Slight pause due to race conditions seen.
		#time.sleep(0.3)
		res = self.send_and_expect('SHUTIT_TMP_VAR=`' + docker_executable + ' commit ' + cfg['container']['container_id'] + '`',expect=[expect,'assword'],child=child,timeout=99999,check_exit=False)
		if res == 1:
			self.send_and_expect(cfg['host']['password'],expect=expect,check_exit=False,record_command=False,child=child)
		self.send_and_expect('echo $SHUTIT_TMP_VAR && unset SHUTIT_TMP_VAR',expect=expect,check_exit=False,record_command=False,child=child)
		image_id = child.after.split('\r\n')[1]

		if not image_id:
			util.fail('failed to commit to ' + repository + ', could not determine image id')

		cmd = docker_executable + ' tag ' + image_id + ' ' + repository
		self.send_and_expect(cmd,child=child,expect=expect,check_exit=False)
		if cfg['repository']['tar']:
			if cfg['build']['tutorial']:
				self.pause_point('We are now exporting the container to a bzipped tar file, as configured in \n[repository]\ntar:yes',print_input=False,child=child)
			bzfile = cfg['host']['resources_dir'] + '/' + repository_tar + '.tar.bz2'
			self.log('\nDepositing bzip2 of exported container into ' + bzfile)
			res = self.send_and_expect(docker_executable + ' export ' + cfg['container']['container_id'] + ' | bzip2 - > ' + bzfile,expect=[expect,'assword'],timeout=99999,child=child)
			self.log('\nDeposited bzip2 of exported container into ' + bzfile,code='31')
			self.log('\nRun:\n\nbunzip2 -c ' + bzfile + ' | sudo docker import -\n\nto get this imported into docker.',code='31')
			cfg['build']['report'] = cfg['build']['report'] + '\nDeposited bzip2 of exported container into ' + bzfile
			cfg['build']['report'] = cfg['build']['report'] + '\nRun:\n\nbunzip2 -c ' + bzfile + ' | sudo docker import -\n\nto get this imported into docker.'
			if res == 1:
				self.send_and_expect(password,expect=expect,child=child,record_command=False)
		if cfg['repository']['push'] == True:
			self.push_repository(repository,docker_executable,expect=expect)
			cfg['build']['report'] = cfg['build']['report'] + 'Pushed repository: ' + repository


def init():
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
	cfg['build']['interactive'] = True # Default to true until we know otherwise
	cfg['build']['build_log']   = None
	cfg['build']['report']      = ''
	cfg['container']            = {}
	cfg['container']['docker_image_default'] = 'ubuntu:12.04' # Statically set up here as needed before general config setup made.
	cfg['host']                 = {}
	cfg['repository']           = {}
	cfg['expect_prompts']       = {}
	cfg['users']                = {}

	# If no LOGNAME available,
	username = os.environ.get('LOGNAME','')
	if username == '':
		util.fail('LOGNAME not set in the environment, please set to your username.')
	if username == 'root':
		util.fail('You cannot be root to run this script')
	# Get the real username
	cfg['host']['real_user'] = os.environ.get('SUDO_USER', username)
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
