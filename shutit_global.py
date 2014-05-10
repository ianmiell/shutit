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

class ShutIt(object):

	_default_child = None
	_default_expect = None

	def __init__(self, **kwargs):
		self.pexpect_children = kwargs['pexpect_children']
		self.shutit_modules = kwargs['shutit_modules']
		self.shutit_main_dir = kwargs['shutit_main_dir']
		self.cfg = kwargs['cfg']
		self.cwd = kwargs['cwd']
		self.shutit_command_history = kwargs['shutit_command_history']
		self.shutit_map = kwargs['shutit_map']

	def set_default_child(self, child):
		self._default_child = child

	def set_default_expect(self, expect_str):
		self._default_expect = expect_str

	def log(self, msg, code=None, pause=0, prefix=True, force_stdout=False):
		if prefix:
			prefix = 'LOG: ' + time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
			msg = prefix + ' ' + str(msg)
		if code != None:
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
	def send_and_expect(self,send,expect=None,child=None,timeout=3600,check_exit=True,fail_on_empty_before=True,record_command=True,exit_values=['0']):
		if expect is None: expect = self._default_expect
		if child is None: child = self._default_child
		if expect is None or child is None:
			util.fail("Couldn't default expect/child: " + str((expect, child)))
		cfg = self.cfg
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
					util.handle_login(child,cfg,'reset_tmp_prompt')
					util.handle_revert_prompt(child,expect,'reset_tmp_prompt')
		if check_exit == True:
			child.sendline('echo EXIT_CODE:$?')
			child.expect(expect,timeout)
			res = util.get_re_from_child(child.before,'^EXIT_CODE:([0-9][0-9]?[0-9]?)$')
			#print 'RES', str(res), ' ', str(exit_values), ' ', str(res in exit_values)
			if res not in exit_values or res == None:
				if res == None:
					res = str(res)
				self.log(util.red('child.after: \n' + child.after + '\n'))
				self.log(util.red('Exit value from command+\n' + send + '\nwas:\n' + res))
				msg = '\nWARNING: command:\n' + send + '\nreturned unaccepted exit code: ' + res + '\nIf this is expected, pass in check_exit=False or an exit_values array into the send_and_expect function call.\nIf you want to error on these errors, set the config:\n[build]\naction_on_ret_code:error'
				cfg['build']['report'] = cfg['build']['report'] + msg
				if cfg['build']['action_on_ret_code'] == 'error':
					util.pause_point(child,msg + '\n\nPause point on exit_code != 0. CTRL-C to quit',force=True)
					#raise Exception('Exit value from command\n' + send + '\nwas:\n' + res)
		# If the command matches any 'password's then don't record
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
		return expect_res

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
	cfg['build']                = {}
	cfg['build']['interactive'] = True # Default to true until we know otherwise
	cfg['build']['build_log']   = None
	cfg['build']['report']      = ''
	cfg['container']            = {}
	#cfg['container']['docker_image_default'] = 'stackbrew/ubuntu' # Statically set up here as needed before general config setup made.
	cfg['container']['docker_image_default'] = 'ubuntu:12.04' # Statically set up here as needed before general config setup made.
	cfg['host']                 = {}
	cfg['repository']           = {}
	cfg['expect_prompts']       = {}
	cfg['users']                = {}

	username = os.environ['LOGNAME']
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
