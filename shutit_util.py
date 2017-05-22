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
import logging
import os
import random
import re
import stat
import string
import sys
import threading
import time
import shutit
import shutit_assets

PY3 = (sys.version_info[0] >= 3)

allowed_delivery_methods = ['ssh','dockerfile','bash','docker','vagrant']


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
	handle_exit(exit_code=1)
# CTRL-\ HANDLING CODE ENDS


# CTRL-C HANDLING CODE STARTS
in_ctrlc = False
def ctrlc_background():
	global ctrl_c_calls
	global in_ctrlc
	ctrl_c_calls += 1
	if ctrl_c_calls > 10:
		handle_exit(exit_code=1)
	in_ctrlc = True
	time.sleep(1)
	in_ctrlc = False


def ctrl_c_signal_handler(_,frame):
	"""CTRL-c signal handler - enters a pause point if it can.
	"""
	global ctrl_c_calls
	ctrl_c_calls += 1
	if ctrl_c_calls > 10:
		handle_exit(exit_code=1)
	shutit_frame = get_shutit_frame(frame)
	if in_ctrlc:
		msg = 'CTRL-C hit twice, quitting'
		if shutit_frame:
			print('\n')
			shutit = shutit_frame.f_locals['shutit']
			shutit.log(msg,level=logging.CRITICAL)
		else:
			print(msg)
		handle_exit(exit_code=1)
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
		handle_exit(exit_code=1)
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


def handle_exit(exit_code=0,msg=None):
	if not msg:
		msg = '\nExiting with error code: ' + str(exit_code)
	if exit_code != 0:
		#shutit_global.shutit_global_object.print_stack_trace()
		print(msg)
		print('Resetting terminal')
	sanitize_terminal()
	sys.exit(exit_code)


def sendline(child,
             line):
	"""Handles sending of line to pexpect object.
	"""
	child.sendline(line)


def sanitize_terminal():
	os.system('stty sane')


def check_delivery_method(method):
	if method in allowed_delivery_methods:
		return True
	return False


# Static strings
_default_repo_name = 'my_module'
default_cnf = '''
################################################################################
# Default core config file for ShutIt.
################################################################################

# Details relating to the target you are building to (container, ssh or bash)
[target]
# Root password for the target - replace with your chosen password
# If left blank, you will be prompted for a password
password:
# Hostname for the target - replace with your chosen target hostname
# (where applicable, eg docker container)
hostname:
# space separated list of ports to expose
# e.g. "ports:2222:22 8080:80" would expose container ports 22 and 80 as the
# host's 2222 and 8080 (where applicable)
ports:
# volume arguments, eg /tmp/postgres:/var/lib/postgres:ro
volumes:
# volumes-from arguments
volumes_from:
# Name to give the docker container (where applicable).
# Empty means "let docker default a name".
name:
# Whether to remove the docker container when finished (where applicable).
rm:no

# Information specific to the host on which the build runs.
[host]
# Ask the user if they want shutit on their path
add_shutit_to_path: yes
# Docker executable on your host machine
docker_executable:docker
# space separated list of dns servers to use
dns:
# Password for the username above on the host (only needed if sudo is needed)
password:
# Log file - will be set to 0600 perms, and defaults to /tmp/<YOUR_USERNAME>_shutit_log_<timestamp>
# A timestamp will be added to the end of the filename.
logfile:
# ShutIt paths to look up modules in separated by ":", eg /path1/here:/opt/path2/there
shutit_module_path:.

# Repository information
[repository]
# Whether to tag
tag:yes
# Whether to suffix the date to the tag
suffix_date:no
# Suffix format (default is epoch seconds (%s), but %Y%m%d_%H%M%S is an option if the length is ok with the index)
suffix_format:%s
# tag name
name:''' + _default_repo_name + '''
# Whether to tar up the docker image exported
export:no
# Whether to tar up the docker image saved
save:no
# Whether to push to the server
push:no
# User on registry to namespace repo - can be set to blank if not docker.io
user:
#Must be set if push is true/yes and user is not blank
password:YOUR_INDEX_PASSWORD_OR_BLANK
#Must be set if push is true/yes and user is not blank
email:YOUR_INDEX_EMAIL_OR_BLANK
# repository server
# make blank if you want this to be sent to the main docker index on docker.io
server:
# tag suffix, defaults to "latest", eg registry/username/repository:latest.
# empty is also "latest"
tag_name:latest

# Root setup script
# Each module should set these in a config
[shutit.tk.setup]
shutit.core.module.build:yes

[shutit.tk.conn_bash]
# None

[shutit.tk.conn_ssh]
# Required
ssh_host:
# All other configs are optional
ssh_port:
ssh_user:
password:
ssh_key:
# (what to execute on the target to get a root shell)
ssh_cmd:

# Aspects of build process
[build]
# How to connect to target
conn_module:shutit.tk.conn_docker
# Run any docker container in privileged mode
privileged:no
# Base image can be over-ridden by --image_tag defaults to this.
base_image:ubuntu:14.04
# Whether to perform tests.
dotest:yes
# --net argument to docker, eg "bridge", "none", "container:<name|id>" or "host". Empty means use default (bridge).
net:
'''

_build_section = '''
		# Some useful API calls for reference. See shutit's docs for more info and options:
		#
		# ISSUING BASH COMMANDS
		# shutit.send(send,expect=<default>) - Send a command, wait for expect (string or compiled regexp)
		#                                      to be seen before continuing. By default this is managed
		#                                      by ShutIt with shell prompts.
		# shutit.multisend(send,send_dict)   - Send a command, dict contains {expect1:response1,expect2:response2,...}
		# shutit.send_and_get_output(send)   - Returns the output of the sent command
		# shutit.send_and_match_output(send, matches)
		#                                    - Returns True if any lines in output match any of
		#                                      the regexp strings in the matches list
		# shutit.send_until(send,regexps)    - Send command over and over until one of the regexps seen in the output.
		# shutit.run_script(script)          - Run the passed-in string as a script
		# shutit.install(package)            - Install a package
		# shutit.remove(package)             - Remove a package
		# shutit.login(user='root', command='su -')
		#                                    - Log user in with given command, and set up prompt and expects.
		#                                      Use this if your env (or more specifically, prompt) changes at all,
		#                                      eg reboot, bash, ssh
		# shutit.logout(command='exit')      - Clean up from a login.
		#
		# COMMAND HELPER FUNCTIONS
		# shutit.add_to_bashrc(line)         - Add a line to bashrc
		# shutit.get_url(fname, locations)   - Get a file via url from locations specified in a list
		# shutit.command_available(command)  - Returns true if the command is available to run
		#
		# LOGGING AND DEBUG
		# shutit.log(msg,add_final_message=False) -
		#                                      Send a message to the log. add_final_message adds message to
		#                                      output at end of build
		# shutit.pause_point(msg='')         - Give control of the terminal to the user
		# shutit.step_through(msg='')        - Give control to the user and allow them to step through commands
		#
		# SENDING FILES/TEXT
		# shutit.send_file(path, contents)   - Send file to path on target with given contents as a string
		# shutit.send_host_file(path, hostfilepath)
		#                                    - Send file from host machine to path on the target
		# shutit.send_host_dir(path, hostfilepath)
		#                                    - Send directory and contents to path on the target
		# shutit.insert_text(text, fname, pattern)
		#                                    - Insert text into file fname after the first occurrence of
		#                                      regexp pattern.
		# shutit.delete_text(text, fname, pattern)
		#                                    - Delete text from file fname after the first occurrence of
		#                                      regexp pattern.
		# shutit.replace_text(text, fname, pattern)
		#                                    - Replace text from file fname after the first occurrence of
		#                                      regexp pattern.
		# ENVIRONMENT QUERYING
		# shutit.file_exists(filename, directory=False)
		#                                    - Returns True if file exists on target
		# shutit.user_exists(user)           - Returns True if the user exists on the target
		# shutit.package_installed(package)  - Returns True if the package exists on the target
		# shutit.set_password(password, user='')
		#                                    - Set password for a given user on target
		#
		# USER INTERACTION
		# shutit.get_input(msg,default,valid[],boolean?,ispass?)
		#                                    - Get input from user and return output
		# shutit.fail(msg)                   - Fail the program and exit with status 1
		#
		# TUTORIALS
		# shutit.challenge(task_desk,hints[],expect_type,challenge_type,follow_on_context{})
		#                                    - Issue challenge to the user. See shutit_global.py
		#'''
