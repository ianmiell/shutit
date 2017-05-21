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
import argparse
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
try:
	import ConfigParser
except ImportError: # pragma: no cover
	import configparser as ConfigParser
import pexpect
import shutit
import shutit_assets
import shutit_class
import shutit_global
from shutit_module import ShutItFailException

PY3 = (sys.version_info[0] >= 3)

allowed_delivery_methods = ['ssh','dockerfile','bash','docker','vagrant']


class LayerConfigParser(ConfigParser.RawConfigParser):

	def __init__(self):
		ConfigParser.RawConfigParser.__init__(self)
		self.layers = []

	def read(self, filenames):
		if not isinstance(filenames, list):
			filenames = [filenames]
		for filename in filenames:
			cp = ConfigParser.RawConfigParser()
			cp.read(filename)
			self.layers.append((cp, filename, None))
		return ConfigParser.RawConfigParser.read(self, filenames)

	def readfp(self, fp, filename=None):
		cp = ConfigParser.RawConfigParser()
		fp.seek(0)
		cp.readfp(fp, filename)
		self.layers.append((cp, filename, fp))
		fp.seek(0)
		ret = ConfigParser.RawConfigParser.readfp(self, fp, filename)
		return ret

	def whereset(self, section, option):
		for cp, filename, fp in reversed(self.layers):
			fp = fp # pylint
			if cp.has_option(section, option):
				return filename
		raise ShutItFailException('[%s]/%s was never set' % (section, option)) # pragma: no cover

	def get_config_set(self, section, option):
		"""Returns a set with each value per config file in it.
		"""
		values = set()
		for cp, filename, fp in self.layers:
			filename = filename # pylint
			fp = fp # pylint
			if cp.has_option(section, option):
				values.add(cp.get(section, option))
		return values

	def reload(self):
		"""
		Re-reads all layers again. In theory this should overwrite all the old
		values with any newer ones.
		It assumes we never delete a config item before reload.
		"""
		oldlayers = self.layers
		self.layers = []
		for cp, filename, fp in oldlayers:
			cp = cp # pylint
			if fp is None:
				self.read(filename)
			else:
				self.readfp(fp, filename)

	def remove_section(self, *args, **kwargs):
		raise NotImplementedError('''Layer config parsers aren't directly mutable''') # pragma: no cover

	def remove_option(self, *args, **kwargs):
		raise NotImplementedError('''Layer config parsers aren't directly mutable''') # pragma: no cover

	def set(self, *args, **kwargs):
		raise NotImplementedError('''Layer config parsers aren\'t directly mutable''') # pragma: no cover


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


def get_configs(shutit, configs):
	"""Reads config files in, checking their security first
	(in case passwords/sensitive info is in them).
	"""
	cp  = LayerConfigParser()
	fail_str = ''
	files    = []
	for config_file in configs:
		if isinstance(config_file, tuple):
			continue
		if not is_file_secure(config_file):
			fail_str = fail_str + '\nchmod 0600 ' + config_file
			files.append(config_file)
	if fail_str != '':
		if shutit_global.shutit_global_object.interactive > 1:
			fail_str = 'Files are not secure, mode should be 0600. Running the following commands to correct:\n' + fail_str + '\n'
			# Actually show this to the user before failing...
			shutit.log(fail_str)
			shutit.log('Do you want me to run this for you? (input y/n)')
			if shutit_global.shutit_global_object.interactive == 0 or shutit.util_raw_input(default='y') == 'y':
				for f in files:
					shutit.log('Correcting insecure file permissions on: ' + f)
					os.chmod(f,0o600)
				# recurse
				return get_configs(shutit, configs)
		else:
			for f in files:
				shutit.log('Correcting insecure file permissions on: ' + f)
				os.chmod(f,0o600)
			# recurse
			return get_configs(shutit, configs)
		shutit.fail(fail_str) # pragma: no cover
	for config in configs:
		if isinstance(config, tuple):
			cp.readfp(config[1], filename=config[0])
		else:
			cp.read(config)
	# Treat allowed_images as a special, additive case
	shutit.build['shutit.core.module.allowed_images'] = cp.get_config_set('build', 'shutit.core.module.allowed_images')
	return cp


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



# Returns the config dict
def parse_args(shutit):
	r"""Responsible for parsing arguments.

	Environment variables:
	SHUTIT_OPTIONS:
	Loads command line options from the environment (if set).
	Behaves like GREP_OPTIONS:
		- space separated list of arguments
		- backslash before a space escapes the space separation
		- backslash before a backslash is interpreted as a single backslash
		- all other backslashes are treated literally
	eg ' a\ b c\\ \\d \\\e\' becomes '', 'a b', 'c\', '\d', '\\e\'
	SHUTIT_OPTIONS is ignored if we are creating a skeleton
	"""
	shutit_global.shutit_global_object.real_user_id = pexpect.run('id -u ' + shutit_global.shutit_global_object.real_user)

	# These are in order of their creation
	actions = ['build', 'run', 'list_configs', 'list_modules', 'list_deps', 'skeleton', 'version']

	# COMPAT 2014-05-15 - build is the default if there is no action specified
	# and we've not asked for help and we've called via 'shutit.py'
	if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] not in actions
			and '-h' not in sys.argv and '--help' not in sys.argv):
		sys.argv.insert(1, 'build')

	parser = argparse.ArgumentParser(description='ShutIt - a tool for managing complex Docker deployments.\n\nTo view help for a specific subcommand, type ./shutit <subcommand> -h',prog="ShutIt")
	subparsers = parser.add_subparsers(dest='action', help='''Action to perform - build=deploy to target, skeleton=construct a skeleton module, list_configs=show configuration as read in, list_modules=show modules available, list_deps=show dep graph ready for graphviz. Defaults to 'build'.''')


	sub_parsers = dict()
	for action in actions:
		sub_parsers[action] = subparsers.add_parser(action)

	sub_parsers['run'].add_argument('shutitfiles', nargs='*', default=['ShutItFile','Shutitfile','ShutItfile','ShutitFile','shutitfile'])

	sub_parsers['skeleton'].add_argument('--name', help='Absolute path to new directory for module. Last part of path is taken as the module name.',default='')
	sub_parsers['skeleton'].add_argument('--domain', help='Arbitrary but unique domain for namespacing your module, eg com.mycorp',default='')
	sub_parsers['skeleton'].add_argument('--depends', help='Module id to depend on, default shutit.tk.setup (optional)', default='shutit.tk.setup')
	sub_parsers['skeleton'].add_argument('--base_image', help='FROM image, default ubuntu:16.04 (optional)', default='ubuntu:16.04')
	sub_parsers['skeleton'].add_argument('--script', help='Pre-existing shell script to integrate into module (optional)', nargs='?', default=None)
	sub_parsers['skeleton'].add_argument('--output_dir', help='Just output the created directory', default=False, const=True, action='store_const')
	sub_parsers['skeleton'].add_argument('--shutitfiles', nargs='+', default=None)
	sub_parsers['skeleton'].add_argument('--vagrant_num_machines', default=None)
	sub_parsers['skeleton'].add_argument('--vagrant_ssh_access', default=False, const=True, action='store_const')
	sub_parsers['skeleton'].add_argument('--vagrant_machine_prefix', default=None)
	sub_parsers['skeleton'].add_argument('--vagrant_docker', default=None, const=True, action='store_const')
	sub_parsers['skeleton'].add_argument('--pattern', help='Pattern to use', default='')
	sub_parsers['skeleton'].add_argument('--delivery', help='Delivery method, aka target. "docker" container (default), configured "ssh" connection, "bash" session', default=None, choices=('docker','dockerfile','ssh','bash'))
	sub_parsers['skeleton'].add_argument('-a','--accept', help='Accept defaults', const=True, default=False, action='store_const')
	sub_parsers['skeleton'].add_argument('--log','-l', help='Log level (DEBUG, INFO (default), WARNING, ERROR, CRITICAL)', default='')
	sub_parsers['skeleton'].add_argument('-o','--logfile', help='Log output to this file', default='')

	sub_parsers['build'].add_argument('--export', help='Perform docker export to a tar file', const=True, default=False, action='store_const')
	sub_parsers['build'].add_argument('--save', help='Perform docker save to a tar file', const=True, default=False, action='store_const')
	sub_parsers['build'].add_argument('--push', help='Push to a repo', const=True, default=False, action='store_const')
	sub_parsers['build'].add_argument('--distro', help='Specify the distro type', default='', choices=('ubuntu','debian','alpine','steamos','red hat','centos','fedora','shutit'))
	sub_parsers['build'].add_argument('--mount_docker', help='Mount the docker socket', default=False, action='store_const', const=True)
	sub_parsers['build'].add_argument('-w','--walkthrough', help='Run in walkthrough mode', default=False, action='store_const', const=True)
	sub_parsers['build'].add_argument('-c','--choose_config', help='Choose configuration interactively', default=False, action='store_const', const=True)
	sub_parsers['build'].add_argument('--video', help='Run in video mode. Same as walkthrough, but waits n seconds rather than for input', nargs=1, default=-1)
	sub_parsers['build'].add_argument('--training', help='Run in "training" mode, where correct input is required at key points', default=False, action='store_const', const=True)
	sub_parsers['build'].add_argument('--exam', help='Run in "exam" mode, where correct input is required at key points and progress is tracked', default=False, action='store_const', const=True)

	sub_parsers['list_configs'].add_argument('--history', help='Show config with history', const=True, default=False, action='store_const')
	sub_parsers['list_modules'].add_argument('--long', help='Show extended module info, including ordering', const=True, default=False, action='store_const')
	sub_parsers['list_modules'].add_argument('--sort', help='Order the modules seen, default to module id', default='id', choices=('id','run_order'))

	for action in ['build', 'list_configs', 'list_modules', 'list_deps','run']:
		sub_parsers[action].add_argument('-o','--logfile',default='', help='Log output to this file')
		sub_parsers[action].add_argument('-l','--log',default='', help='Log level (DEBUG, INFO (default), WARNING, ERROR, CRITICAL)',choices=('DEBUG','INFO','WARNING','ERROR','CRITICAL','debug','info','warning','error','critical'))
		if action != 'run':
			sub_parsers[action].add_argument('-d','--delivery', help='Delivery method, aka target. "docker" container (default), configured "ssh" connection, "bash" session', default=None, choices=('docker','dockerfile','ssh','bash'))
			sub_parsers[action].add_argument('--config', help='Config file for setup config. Must be with perms 0600. Multiple arguments allowed; config files considered in order.', default=[], action='append')
			sub_parsers[action].add_argument('-s', '--set', help='Override a config item, e.g. "-s target rm no". Can be specified multiple times.', default=[], action='append', nargs=3, metavar=('SEC', 'KEY', 'VAL'))
			sub_parsers[action].add_argument('--image_tag', help='Build container from specified image - if there is a symbolic reference, please use that, eg localhost.localdomain:5000/myref', default='')
			sub_parsers[action].add_argument('--tag_modules', help='''Tag each module after it's successfully built regardless of the module config and based on the repository config.''', default=False, const=True, action='store_const')
			sub_parsers[action].add_argument('-m', '--shutit_module_path', default=None, help='List of shutit module paths, separated by colons. ShutIt registers modules by running all .py files in these directories.')
			sub_parsers[action].add_argument('--trace', help='Trace function calls', const=True, default=False, action='store_const')
			sub_parsers[action].add_argument('--interactive', help='Level of interactive. 0 = none, 1 = honour pause points and config prompting, 2 = query user on each module, 3 = tutorial mode', default='1')
			sub_parsers[action].add_argument('--ignorestop', help='Ignore STOP files', const=True, default=False, action='store_const')
			sub_parsers[action].add_argument('--ignoreimage', help='Ignore disallowed images', const=True, default=None, action='store_const')
			sub_parsers[action].add_argument('--imageerrorok', help='Exit without error if allowed images fails (used for test scripts)', const=True, default=False, action='store_const')
			sub_parsers[action].add_argument('--deps_only', help='build deps only, tag with suffix "_deps"', const=True, default=False, action='store_const')
			sub_parsers[action].add_argument('--echo', help='Always echo output', const=True, default=False, action='store_const')

	args_list = sys.argv[1:]
	if os.environ.get('SHUTIT_OPTIONS', None) and args_list[0] != 'skeleton':
		env_args = os.environ['SHUTIT_OPTIONS'].strip()
		# Split escaped backslashes
		env_args_split = re.split(r'(\\\\)', env_args)
		# Split non-escaped spaces
		env_args_split = [re.split(r'(?<!\\)( )', item) for item in env_args_split]
		# Flatten
		env_args_split = [item for sublist in env_args_split for item in sublist]
		# Split escaped spaces
		env_args_split = [re.split(r'(\\ )', item) for item in env_args_split]
		# Flatten
		env_args_split = [item for sublist in env_args_split for item in sublist]
		# Trim empty strings
		env_args_split = [item for item in env_args_split if item != '']
		# We know we don't have to deal with an empty env argument string
		env_args_list = ['']
		# Interpret all of the escape sequences
		for item in env_args_split:
			if item == ' ':
				env_args_list.append('')
			elif item == '\\ ':
				env_args_list[-1] += ' '
			elif item == '\\\\':
				env_args_list[-1] += '\\'
			else:
				env_args_list[-1] += item
		args_list[1:1] = env_args_list
	args = parser.parse_args(args_list)
	if args.action == 'version':
		shutit.process_args(shutit_class.ShutItInit(args.action,
		                                            logfile=args.logfile,
		                                            log=args.log))
	elif args.action == 'skeleton':
		shutit.process_args(shutit_class.ShutItInit(args.action,
		                                            logfile=args.logfile,
		                                            log=args.log,
		                                            accept=args.accept,
		                                            shutitfiles=args.shutitfiles,
		                                            script=args.script,
		                                            base_image=args.base_image,
		                                            depends=args.depends,
		                                            name=args.name,
		                                            domain=args.domain,
		                                            pattern=args.pattern,
		                                            output_dir=args.output_dir,
		                                            vagrant_ssh_access=args.vagrant_ssh_access,
		                                            vagrant_num_machines=args.vagrant_num_machines,
		                                            vagrant_machine_prefix=args.vagrant_machine_prefix,
		                                            vagrant_docker=args.vagrant_docker))
	elif args.action == 'run':
		shutit.process_args(shutit_class.ShutItInit(args.action,
		                                            logfile=args.logfile,
		                                            log=args.log,
		                                            shutitfiles=args.shutitfiles,
		                                            delivery = args.delivery))
	elif args.action == 'build':
		shutit.process_args(shutit_class.ShutItInit(args.action,
		                                            logfile=args.logfile,
		                                            log=args.log,
		                                            push=args.push,
		                                            export=args.export,
		                                            save=args.save,
		                                            distro=args.distro,
		                                            mount_docker=args.mount_docker,
		                                            walkthrough=args.walkthrough,
		                                            training=args.training,
		                                            choose_config=args.choose_config,
	                                                config = args.config,
	                                                set = args.set,
	                                                ignorestop = args.ignorestop,
	                                                ignoreimage = args.ignoreimage,
	                                                imageerrorok = args.imageerrorok,
	                                                tag_modules = args.tag_modules,
	                                                image_tag = args.image_tag,
	                                                video = args.video,
	                                                deps_only = args.deps_only,
	                                                echo = args.echo,
	                                                delivery = args.delivery,
	                                                interactive = args.interactive,
	                                                trace = args.trace,
	                                                shutit_module_path = args.shutit_module_path,
		                                            exam=args.exam))
	elif args.action == 'list_configs':
		shutit.process_args(shutit_class.ShutItInit(args.action,
		                                            logfile=args.logfile,
		                                            log=args.log,
		                                            history=args.history))
	elif args.action == 'list_modules':
		shutit.process_args(shutit_class.ShutItInit(args.action,
		                                            logfile=args.logfile,
		                                            log=args.log,
		                                            sort=args.sort,
		                                            long=args.long))




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
		shutit.do_finalize()
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
_default_cnf = '''
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
