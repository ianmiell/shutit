#!/usr/bin/env pythen

"""ShutIt utility functions.
"""

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

from __future__ import print_function
import binascii
import getpass
import logging
import os
import random
import re
import readline
import stat
import string
import sys
import threading
import time
import shutit_assets
import shutit_class
import shutit_global

PY3 = (sys.version_info[0] >= 3)


def is_file_secure(file_name):
	"""Returns false if file is considered insecure, true if secure.
	If file doesn't exist, it's considered secure!
	"""
	if not os.path.isfile(file_name):
		return True
	file_mode = os.stat(file_name).st_mode
	if file_mode & (stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH):
		return False
	return True


def colourise(code, msg):
	"""Colourize the given string for a terminal.
	"""
	if code == '' or code is None:
		return msg # pragma: no cover
	return '\033[%sm%s\033[0m' % (code, msg)




def random_id(size=8, chars=string.ascii_letters + string.digits):
	"""Generates a random string of given size from the given chars.

	@param size:  The size of the random string.
	@param chars: Constituent pool of characters to draw random characters from.
	@type size:   number
	@type chars:  string
	@rtype:       string
	@return:      The string of random characters.
	"""
	return ''.join(random.choice(chars) for _ in range(size))


def random_word(size=6):
	"""Returns a random word in lower case.
	"""
	words = shutit_assets.get_words().splitlines()
	word = ''
	while len(word) != size or word.find("'") > -1:
		word = words[int(random.random() * (len(words) - 1))]
	return word.lower()







def get_hash(string_to_hash):
	"""Helper function to get preceding integer
	eg com.openbet == 1003189494
	>>> import binascii
	>>> abs(binascii.crc32(b'shutit.tk'))
	782914092

	Recommended means of determining run order integer part.
	"""
	return abs(binascii.crc32(string_to_hash.encode()))


# get the ordinal for a given char, in a friendly way
def get_wide_hex(char):
	if len(char) != 2:
		return r'\x' + hex(ord(char))[2:]
	return r'\u' + hex(0x10000 + (ord(char[0]) - 0xD800) * 0x400 + (ord(char[1]) - 0xDC00))[2:]


# CTRL-\ HANDLING CODE STARTS
def ctrl_quit_signal_handler(_,frame):
	print(r'CRTL-\ caught, hard-exiting ShutIt')
	shutit_frame = get_shutit_frame(frame)
	if shutit_frame:
		shutit_class.do_finalize()
	shutit_global.shutit_global_object.handle_exit(exit_code=1)
# CTRL-\ HANDLING CODE ENDS


# CTRL-C HANDLING CODE STARTS
in_ctrlc = False
def ctrlc_background():
	global ctrl_c_calls
	global in_ctrlc
	ctrl_c_calls += 1
	if ctrl_c_calls > 10:
		shutit_global.shutit_global_object.handle_exit(exit_code=1)
	in_ctrlc = True
	time.sleep(1)
	in_ctrlc = False


def ctrl_c_signal_handler(_,frame):
	"""CTRL-c signal handler - enters a pause point if it can.
	"""
	global ctrl_c_calls
	ctrl_c_calls += 1
	if ctrl_c_calls > 10:
		shutit_global.shutit_global_object.handle_exit(exit_code=1)
	shutit_frame = get_shutit_frame(frame)
	if in_ctrlc:
		msg = 'CTRL-C hit twice, quitting'
		if shutit_frame:
			print('\n')
			shutit = shutit_frame.f_locals['shutit']
			shutit.log(msg,level=logging.CRITICAL)
		else:
			print(msg)
		shutit_global.shutit_global_object.handle_exit(exit_code=1)
	if shutit_frame:
		shutit = shutit_frame.f_locals['shutit']
		if shutit.build['ctrlc_passthrough']:
			shutit.self.get_current_shutit_pexpect_session().pexpect_child.sendline(r'')
			return
		print(colourise(31,"\r" + r"You may need to wait for a command to complete before a pause point is available. Alternatively, CTRL-\ to quit."))
		shutit.build['ctrlc_stop'] = True
		t = threading.Thread(target=ctrlc_background)
		t.daemon = True
		t.start()
		# Reset the ctrl-c calls
		ctrl_c_calls = 0
		return
	print(colourise(31,'\n' + '*' * 80))
	print(colourise(31,"CTRL-c caught, CTRL-c twice to quit."))
	print(colourise(31,'*' * 80))
	t = threading.Thread(target=ctrlc_background)
	t.daemon = True
	t.start()
	# Reset the ctrl-c calls
	ctrl_c_calls = 0


def get_shutit_frame(frame):
	global ctrl_c_calls
	ctrl_c_calls += 1
	if ctrl_c_calls > 10:
		shutit_global.shutit_global_object.handle_exit(exit_code=1)
	if not frame.f_back:
		return None
	else:
		if 'shutit' in frame.f_locals:
			return frame
		return get_shutit_frame(frame.f_back)
ctrl_c_calls = 0
# CTRL-C HANDLING CODE ENDS


def print_frame_recurse(frame):
	if not frame.f_back:
		return
	else:
		print('=============================================================================')
		print(frame.f_locals)
		print_frame_recurse(frame.f_back)


def check_regexp(regex):
	if regex is None:
		# Is this ok?
		return True
	try:
		re.compile(regex)
		result = True
	except re.error:
		result = False
	return result


def sendline(child,
             line):
	"""Handles sending of line to pexpect object.
	"""
	child.sendline(line)


def sanitize_terminal():
	os.system('stty sane')


def util_raw_input(prompt='', default=None, ispass=False, use_readline=True):
	"""Handles raw_input calls, and switches off interactivity if there is apparently
	no controlling terminal (or there are any other problems)
	"""
	if use_readline:
		try:
			readline.read_init_file('/etc/inputrc')
		except IOError:
			pass
		readline.parse_and_bind('tab: complete')
	prompt = '\r\n' + prompt
	if ispass:
		prompt += '\r\nInput Secret: '
	sanitize_terminal()
	if shutit_global.shutit_global_object.interactive == 0:
		return default
	if not shutit_global.shutit_global_object.determine_interactive():
		return default
	while True:
		try:
			if ispass:
				return getpass.getpass(prompt=prompt)
			else:
				resp = raw_input(prompt).strip()
				if resp == '':
					return default
				else:
					return resp
		except KeyboardInterrupt:
			continue
		except IOError:
			msg = 'Problems getting raw input, assuming no controlling terminal.'
	if ispass:
		return getpass.getpass(prompt=prompt)
	else:
		resp = raw_input(prompt).strip()
		if resp == '':
			return default
		else:
			return resp
	shutit_global.shutit_global_object.set_noninteractive(msg=msg)
	return default


def get_input(msg, default='', valid=None, boolean=False, ispass=False, colour='32'):
	"""Gets input from the user, and returns the answer.

	@param msg:       message to send to user
	@param default:   default value if nothing entered
	@param valid:     valid input values (default == empty list == anything allowed)
	@param boolean:   whether return value should be boolean
	@param ispass:    True if this is a password (ie whether to not echo input)
	"""
	if boolean and valid is None:
		valid = ('yes','y','Y','1','true','no','n','N','0','false')
	answer = util_raw_input(prompt=colourise(colour,msg),ispass=ispass)
	if boolean and answer in ('', None) and default != '':
		return default
	if valid is not None:
		while answer not in valid:
			shutit_global.shutit_global_object.log('Answer must be one of: ' + str(valid),transient=True)
			answer = util_raw_input(prompt=colourise(colour,msg),ispass=ispass)
	if boolean and answer in ('yes','y','Y','1','true','t','YES'):
		return True
	if boolean and answer in ('no','n','N','0','false','f','NO'):
		return False
	if answer in ('',None):
		return default
	else:
		return answer
