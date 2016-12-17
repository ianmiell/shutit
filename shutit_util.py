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

try:
	import ConfigParser
except ImportError:
	import configparser as ConfigParser
try:
	from StringIO import StringIO
except ImportError:
	from io import StringIO
import argparse
import base64
import binascii
import getpass
import glob
import hashlib
import imp
import json
import logging
import operator
import os
import random
import re
import readline
import stat
import string
import sys
import threading
import time
import pexpect
import texttable
import subprocess
import shutit_global
import shutit_main
import shutit_assets
import shutit_skeleton
import shutit_exam
from shutit_module import ShutItFailException
from shutit_module import ShutItModule

PY3 = (sys.version_info[0] >= 3)

allowed_delivery_methods = ['ssh','dockerfile','bash','docker']


class LayerConfigParser(ConfigParser.RawConfigParser):

	def __init__(self):
		ConfigParser.RawConfigParser.__init__(self)
		self.layers = []

	def read(self, filenames):
		if type(filenames) is not list:
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
			if cp.has_option(section, option):
				return filename
		raise ShutItFailException('[%s]/%s was never set' % (section, option))

	def get_config_set(self, section, option):
		"""Returns a set with each value per config file in it.
		"""
		values = set()
		for cp, filename, fp in self.layers:
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
			if fp is None:
				self.read(filename)
			else:
				self.readfp(fp, filename)

	def remove_section(self, *args, **kwargs):
		raise NotImplementedError('''Layer config parsers aren't directly mutable''')

	def remove_option(self, *args, **kwargs):
		raise NotImplementedError('''Layer config parsers aren't directly mutable''')

	def set(self, *args, **kwargs):
		raise NotImplementedError('''Layer config parsers aren\'t directly mutable''')

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
	if code == '' or code == None:
		return msg
	return '\033[%sm%s\033[0m' % (code, msg)


def get_configs(configs):
	"""Reads config files in, checking their security first
	(in case passwords/sensitive info is in them).
	"""
	shutit = shutit_global.shutit
	cp  = LayerConfigParser()
	fail_str = ''
	files    = []
	for config_file in configs:
		if type(config_file) is tuple:
			continue
		if not is_file_secure(config_file):
			fail_str = fail_str + '\nchmod 0600 ' + config_file
			files.append(config_file)
	if fail_str != '':
		if shutit.build['interactive'] > 1:
			fail_str = 'Files are not secure, mode should be 0600. Running the following commands to correct:\n' + fail_str + '\n'
			# Actually show this to the user before failing...
			shutit.log(fail_str)
			shutit.log('Do you want me to run this for you? (input y/n)')
			if shutit.build['interactive'] == 0 or util_raw_input(default='y') == 'y':
				for f in files:
					shutit.log('Correcting insecure file permissions on: ' + f)
					os.chmod(f,0o600)
				# recurse
				return get_configs(configs)
		else:
			for f in files:
				shutit.log('Correcting insecure file permissions on: ' + f)
				os.chmod(f,0o600)
			# recurse
			return get_configs(configs)
		shutit.fail(fail_str)
	for config in configs:
		if type(config) is tuple:
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

def find_asset(filename):
	shutit = shutit_global.shutit
	(head,filename) = os.path.split(filename)
	if head == '':
		dirs = ['/usr/share/dict',
		        sys.prefix,
		        os.path.join(sys.prefix,'local'),
		        shutit.shutit_main_dir,
		        os.path.join(shutit_global.shutit.shutit_main_dir,'../../..'),
		        shutit.host['shutit_path'],
		        '/usr/local'
		       ]
		dirs = dirs + sys.path
	else:
		dirs = ['/usr/share/dict' + '/' + head,
		        sys.prefix + '/' + head,
		        os.path.join(sys.prefix,'local') + '/' + head,
		        shutit.shutit_main_dir + '/' + head,
		        os.path.join(shutit_global.shutit.shutit_main_dir,'../../..') + '/' + head,
		        shutit.host['shutit_path'] + '/' + head,
		        '/usr/local' + '/' + head
		       ]
		dirs = dirs + sys.path
	for iter_dir in dirs:
		if os.access(os.path.join(iter_dir,filename),os.F_OK):
			return os.path.join(iter_dir,filename)
		if os.access(os.path.join(os.path.join(iter_dir,'assets'),filename),os.F_OK):
			return os.path.join(os.path.join(iter_dir,'assets'),filename)
		if os.access(os.path.join(os.path.join(iter_dir,'shutit_assets'),filename),os.F_OK):
			return os.path.join(os.path.join(iter_dir,'shutit_assets'),filename)
	return filename


# Set up logging
#
def setup_logging():
	shutit = shutit_global.shutit
	# If loglevel is an int, this has already been set up.
	if type(shutit.build['loglevel']) == int:
		return
	logformat='%(asctime)s %(levelname)s: %(message)s'
	if shutit.host['logfile'] == '':
		if not os.access(shutit.build['shutit_state_dir_base'],os.F_OK):
			os.mkdir(shutit.build['shutit_state_dir_base'])
		if not os.access(shutit.build['shutit_state_dir'],os.F_OK):
			os.mkdir(shutit.build['shutit_state_dir'])
		os.chmod(shutit.build['shutit_state_dir_base'],0o777)
		os.chmod(shutit.build['shutit_state_dir'],0o777)
		shutit.build['loglevel'] = shutit.build['loglevel'].upper()
		if string.upper(shutit.build['loglevel']) == 'DEBUG':
			logging.basicConfig(format=logformat,level=logging.DEBUG)
		elif string.upper(shutit.build['loglevel']) == 'ERROR':
			logging.basicConfig(format=logformat,level=logging.ERROR)
		elif string.upper(shutit.build['loglevel']) in ('WARN','WARNING'):
			logging.basicConfig(format=logformat,level=logging.WARNING)
		elif string.upper(shutit.build['loglevel']) == 'CRITICAL':
			logging.basicConfig(format=logformat,level=logging.CRITICAL)
		elif string.upper(shutit.build['loglevel']) == 'INFO':
			logging.basicConfig(format=logformat,level=logging.INFO)
		else:
			logging.basicConfig(format=logformat,level=logging.INFO)
	else:
		if string.upper(shutit.build['loglevel']) == 'DEBUG':
			logging.basicConfig(format=logformat,filename=shutit.host['logfile'],level=logging.DEBUG)
		elif string.upper(shutit.build['loglevel']) == 'ERROR':
			logging.basicConfig(format=logformat,filename=shutit.host['logfile'],level=logging.ERROR)
		elif string.upper(shutit.build['loglevel']) in ('WARN','WARNING'):
			logging.basicConfig(format=logformat,filename=shutit.host['logfile'],level=logging.WARNING)
		elif string.upper(shutit.build['loglevel']) == 'CRITICAL':
			logging.basicConfig(format=logformat,filename=shutit.host['logfile'],level=logging.CRITICAL)
		elif string.upper(shutit.build['loglevel']) == 'INFO':
			logging.basicConfig(format=logformat,filename=shutit.host['logfile'],level=logging.INFO)
		else:
			logging.basicConfig(format=logformat,filename=shutit.host['logfile'],level=logging.INFO)
	shutit.build['loglevel'] = logging.getLogger().getEffectiveLevel()


# Manage config settings, returning a dict representing the settings
# that have been sanity-checked.
def get_base_config(cfg_parser):
	"""Responsible for getting core configuration from config files.
	"""
	shutit = shutit_global.shutit
	shutit.config_parser = cp = cfg_parser
	# BEGIN Read from config files
	# build - details relating to the build
	shutit.build['privileged']                 = cp.getboolean('build', 'privileged')
	shutit.build['base_image']                 = cp.get('build', 'base_image')
	shutit.build['dotest']                     = cp.get('build', 'dotest')
	shutit.build['net']                        = cp.get('build', 'net')
	shutit.build['completed']                  = False
	shutit.build['step_through']               = False
	shutit.build['ctrlc_stop']                 = False
	shutit.build['ctrlc_passthrough']          = False
	shutit.build['have_read_config_file']      = False
	# Width of terminal to set up on login and assume for other cases.
	shutit.build['stty_cols']                  = 320
	# Signals are set here, which is useful for context-switching callbacks.
	shutit.shutit_signal['ID']                 = 0
	# Take a command-line arg if given, else default.
	if shutit.build['conn_module'] is None:
		shutit.build['conn_module']            = cp.get('build', 'conn_module')
	# Track logins in a stack and details in logins.
	shutit.build['login_stack']                = []
	shutit.build['logins']                     = {}
	# Whether to accept default configs
	shutit.build['accept_defaults']            = None
	# target - the target of the build, ie the container
	shutit.target['hostname']                  = cp.get('target', 'hostname')
	shutit.target['locale']                    = cp.get('target', 'locale')
	shutit.target['ports']                     = cp.get('target', 'ports')
	shutit.target['volumes']                   = cp.get('target', 'volumes')
	shutit.target['volumes_from']              = cp.get('target', 'volumes_from')
	shutit.target['name']                      = cp.get('target', 'name')
	shutit.target['rm']                        = cp.getboolean('target', 'rm')
	# host - the host on which the shutit script is run
	shutit.host['add_shutit_to_path']          = cp.getboolean('host', 'add_shutit_to_path')
	shutit.host['docker_executable']           = cp.get('host', 'docker_executable')
	shutit.host['dns']                         = cp.get('host', 'dns')
	shutit.host['password']                    = cp.get('host', 'password')
	shutit.host['logfile']                     = cp.get('host', 'logfile')
	shutit.host['shutit_module_path']          = cp.get('host', 'shutit_module_path').split(':')
	# repository - information relating to repository/registry
	shutit.repository['name']                  = cp.get('repository', 'name')
	shutit.repository['server']                = cp.get('repository', 'server')
	shutit.repository['push']                  = cp.getboolean('repository', 'push')
	shutit.repository['tag']                   = cp.getboolean('repository', 'tag')
	shutit.repository['export']                = cp.getboolean('repository', 'export')
	shutit.repository['save']                  = cp.getboolean('repository', 'save')
	shutit.repository['suffix_date']           = cp.getboolean('repository', 'suffix_date')
	shutit.repository['suffix_format']         = cp.get('repository', 'suffix_format')
	shutit.repository['user']                  = cp.get('repository', 'user')
	shutit.repository['password']              = cp.get('repository', 'password')
	shutit.repository['email']                 = cp.get('repository', 'email')
	shutit.repository['tag_name']              = cp.get('repository', 'tag_name')
	# END Read from config files

	# BEGIN Standard expects
	# It's important that these have '.*' in them at the start, so that the matched data is reliably 'after' in the
	# child object. Use these where possible to make things more consistent.
	# Attempt to capture any starting prompt (when starting) with this regexp.
	shutit.expect_prompts['base_prompt']       = '\r\n.*[@#$] '
	# END Standard expects

	if shutit.build['delivery'] in ('bash','ssh'):
		if shutit.target['docker_image'] != '':
			print('delivery method specified (' + shutit.build['delivery'] + ') and image_tag argument make no sense')
			handle_exit(exit_code=1)
	if shutit.target['docker_image'] == '':
		shutit.target['docker_image'] = shutit.build['base_image']
	# END tidy configs up

	# BEGIN warnings
	# FAILS begins
	# rm is incompatible with repository actions
	if shutit.target['rm'] and (shutit.repository['tag'] or shutit.repository['push'] or shutit.repository['save'] or shutit.repository['export']):
		print("Can't have [target]/rm and [repository]/(push/save/export) set to true")
		handle_exit(exit_code=1)
	if shutit.target['hostname'] != '' and shutit.build['net'] != '' and shutit.build['net'] != 'bridge':
		print('\n\ntarget/hostname or build/net configs must be blank\n\n')
		handle_exit(exit_code=1)
	# FAILS ends


# Returns the config dict
def parse_args():
	"""Responsible for parsing arguments.

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
	global allowed_delivery_methods
	shutit = shutit_global.shutit
	shutit.host['real_user_id'] = pexpect.run('id -u ' + shutit.host['real_user']).strip()

	# These are in order of their creation
	actions = ['build', 'run', 'list_configs', 'list_modules', 'list_deps', 'skeleton', 'version']

	# COMPAT 2014-05-15 - build is the default if there is no action specified
	# and we've not asked for help and we've called via 'shutit_main.py'
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
	sub_parsers['skeleton'].add_argument('--pattern', help='Pattern to use', default='')
	sub_parsers['skeleton'].add_argument('--delivery', help='Delivery method, aka target. "docker" container (default), configured "ssh" connection, "bash" session', default=None, choices=('docker','dockerfile','ssh','bash'))
	sub_parsers['skeleton'].add_argument('-a','--accept', help='Accept defaults', const=True, default=False, action='store_const')
	sub_parsers['skeleton'].add_argument('--log','-l', help='Log level (DEBUG, INFO (default), WARNING, ERROR, CRITICAL)', default='INFO')
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
		sub_parsers[action].add_argument('-l','--log',default='INFO', help='Log level (DEBUG, INFO (default), WARNING, ERROR, CRITICAL)',choices=('DEBUG','INFO','WARNING','ERROR','CRITICAL','debug','info','warning','error','critical'))
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
		print('ShutIt version: ' + shutit_main.shutit_version)
		handle_exit(exit_code=0)

	# What are we asking shutit to do?
	shutit.action['list_configs'] = args.action == 'list_configs'
	shutit.action['list_modules'] = args.action == 'list_modules'
	shutit.action['list_deps']    = args.action == 'list_deps'
	shutit.action['skeleton']     = args.action == 'skeleton'
	shutit.action['build']        = args.action == 'build'
	shutit.action['run']          = args.action == 'run'
	# Logging
	shutit.host['logfile']   = args.logfile
	shutit.build['loglevel'] = args.log
	shutit.build['exam']     = False
	setup_logging()

	# This mode is a bit special - it's the only one with different arguments
	if shutit.action['skeleton']:
		delivery_method = args.delivery
		accept_defaults = args.accept
		# Looks through the arguments given for valid shutitfiles, and adds their names to _new_shutitfiles.
		if args.shutitfiles and args.script:
			shutit.fail('Cannot have any two of script, -d/--shutitfiles <files> as arguments')
		_new_shutitfiles = None
		if args.shutitfiles:
			cwd = os.getcwd()
			_new_shutitfiles       = []
			_delivery_methods_seen = set()
			for shutitfile in args.shutitfiles:
				if shutitfile[0] != '/':
					shutitfile = cwd + '/' + shutitfile
				if os.path.isfile(shutitfile):
					candidate_shutitfile_fh = open(shutitfile,'r')
					candidate_shutitfile_contents = candidate_shutitfile_fh.read()
					candidate_shutitfile_fh.close()
					try:
						shutitfile_representation, ok = shutit_skeleton.process_shutitfile(candidate_shutitfile_contents)
						if not ok or candidate_shutitfile_contents.strip() == '':
							print('Ignoring file (failed to parse candidate shutitfile): ' + shutitfile)
						else:
							_new_shutitfiles.append(shutitfile)
							if len(shutitfile_representation['shutitfile']['delivery']) > 0:
								_delivery_methods_seen.add(shutitfile_representation['shutitfile']['delivery'][0][1])
					except Exception as e:
						print('')
						print(e)
						print('Ignoring file (failed to parse candidate shutitfile): ' + shutitfile)
				elif os.path.isdir(shutitfile):
					for root, subfolders, files in os.walk(shutitfile):
						subfolders.sort()
						files.sort()
						for fname in files:
							candidate_shutitfile = os.path.join(root, fname)
							try:
								if os.path.isfile(candidate_shutitfile):
									candidate_shutitfile_fh = open(candidate_shutitfile,'r')
									candidate_shutitfile_contents = candidate_shutitfile_fh.read()
									candidate_shutitfile_fh.close()
									shutitfile_representation, ok = shutit_skeleton.process_shutitfile(candidate_shutitfile_contents)
									if not ok or candidate_shutitfile_contents.strip() == '':
										print('Ignoring file (failed to parse candidate shutitfile): ' + candidate_shutitfile)
									else:
										_new_shutitfiles.append(candidate_shutitfile)
										if len(shutitfile_representation['shutitfile']['delivery']) > 0:
											_delivery_methods_seen.add(shutitfile_representation['shutitfile']['delivery'][0][1])
								else:
									print('Ignoring filename (not a normal file): ' + fname)
							except:
								print('Ignoring file (failed to parse candidate shutitfile): ' + candidate_shutitfile)
			if _new_shutitfiles:
				if len(_delivery_methods_seen) == 0 and delivery_method == None:
					delivery_method = 'bash'
				elif len(_delivery_methods_seen) == 0:
					pass
				elif len(_delivery_methods_seen) == 1 and delivery_method == None:
					delivery_method = _delivery_methods_seen.pop()
				elif len(_delivery_methods_seen) == 1:
					shutitfile_delivery_method = _delivery_methods_seen.pop()
					if delivery_method != shutitfile_delivery_method:
						print('Conflicting delivery methods passed in vs. from shutitfile.\nPassed-in: ' + delivery_method + '\nShutitfile: ' + shutitfile_delivery_method)
						handle_exit(exit_code=1)
				else:
					print('Too many delivery methods seen in shutitfiles: ' + str(_new_shutitfiles))
					print('Delivery methods: ' + str(_delivery_methods_seen))
					print('Delivery method passed in: ' + delivery_method)
					handle_exit(exit_code=1)
			else:
				print('ShutItFiles: ' + str(shutitfile) + ' appear to not exist.')
				handle_exit(exit_code=1)
		module_directory = args.name
		if module_directory == '':
			default_dir = shutit.host['calling_path'] + '/shutit_' + random_word()
			if accept_defaults:
				module_directory = default_dir
			else:
				module_directory = util_raw_input(prompt='# Input a name for this module.\n# Default: ' + default_dir + '\n', default=default_dir)
		if module_directory[0] != '/':
			module_directory = shutit.host['calling_path'] + '/' + module_directory
		module_name = module_directory.split('/')[-1].replace('-','_')
		if args.domain == '':
			default_domain_name = os.getcwd().split('/')[-1] + '.' + module_name
			#if accept_defaults:
			domain = default_domain_name
			#else:
			#	domain = util_raw_input(prompt='# Input a unique domain, eg (com.yourcorp).\n# Default: ' + default_domain_name + '\n', default=default_domain_name)
		else:
			domain = args.domain
		# Figure out defaults.
		# If no pattern supplied, then assume it's the same as delivery.
		default_pattern = 'bash'
		if args.pattern == '':
			if accept_defaults or _new_shutitfiles:
				if _new_shutitfiles:
					default_pattern = delivery_method
				pattern = default_pattern
			else:
				pattern = util_raw_input(prompt='''# Input a ShutIt pattern.
Default: ''' + default_pattern + '''

bash:              a shell script
docker:            a docker image build
vagrant:           a vagrant setup
docker_tutorial:   a docker-based tutorial
shutitfile:        a shutitfile-based project
''',default=default_pattern)
		else:
			pattern = args.pattern

		# Sort out delivery method.
		if delivery_method is None:
			take_this_default = False
			default_delivery = 'bash'
			if pattern in ('docker','docker_tutorial', 'shutitfile'):
				if pattern in ('docker','docker_tutorial'):
					take_this_default = True
				default_delivery = 'docker'
			elif pattern in ('vagrant','bash'):
				take_this_default = True
				default_delivery = 'bash'
			else:
				default_delivery = 'bash'
			if accept_defaults or take_this_default:
				delivery = default_delivery
			else:
				delivery = ''
				while delivery not in allowed_delivery_methods:
					delivery = util_raw_input(prompt='# Input a delivery method from: bash, docker.\n# Default: ' + default_delivery + '\n\ndocker = build within a docker image\nbash = run commands directly within bash\n', default=default_delivery)
		else:
			delivery = delivery_method
		shutit.cfg['skeleton'] = {
			'path':                  module_directory,
			'module_name':           module_name,
			'base_image':            args.base_image,
			'domain':                domain,
			'domain_hash':           str(get_hash(domain)),
			'depends':               args.depends,
			'script':                args.script,
			'shutitfiles':           _new_shutitfiles,
			'output_dir':            args.output_dir,
			'delivery':              delivery,
			'pattern':               pattern
		}
		# set defaults to allow config to work
		shutit.build['extra_configs']    = []
		shutit.build['config_overrides'] = []
		shutit.build['conn_module']      = None
		shutit.build['delivery']         = 'bash'
		shutit.target['docker_image']    = ''
	elif shutit.action['run']:
		module_name      = random_id(chars=string.ascii_letters)
		module_dir       = "/tmp/shutit_built/" + module_name
		module_build_dir = module_dir + '/built'
		module_domain    = module_name + '.' + module_name
		argv_new = [sys.argv[0],'skeleton','--shutitfile'] + args.shutitfiles + ['--name', module_dir,'--domain',module_domain,'--pattern','bash']
		retdir = os.getcwd()
		retval=subprocess.call(argv_new)
		os.chdir(module_dir)
		retval=subprocess.call('./run.sh')
		os.chdir(retdir)
		sys.exit(0)
	else:
		shutit_home = shutit.host['shutit_path'] = os.path.expanduser('~/.shutit')
		# We're not creating a skeleton, so make sure we have the infrastructure
		# in place for a user-level storage area
		if not os.path.isdir(shutit_home):
			os.mkdir(shutit_home, 0o700)
		if not os.path.isfile(os.path.join(shutit_home, 'config')):
			f = os.open(os.path.join(shutit_home, 'config'), os.O_WRONLY | os.O_CREAT, 0o600)
			if PY3:
				os.write(f,bytes(_default_cnf,'utf-8'))
			else:
				os.write(f,_default_cnf)
			os.close(f)

		# Default this to False as it's not always set (mostly for debug logging).
		shutit.list_configs['cfghistory']  = False
		shutit.list_modules['long']        = False
		shutit.list_modules['sort']        = None
		shutit.build['video']              = False
		shutit.build['training']           = False
		shutit.build['exam_object']        = None
		shutit.build['choose_config']      = False
		# Persistence- and build-related arguments.
		if shutit.action['build']:
			shutit.repository['push']       = args.push
			shutit.repository['export']     = args.export
			shutit.repository['save']       = args.save
			shutit.build['distro_override'] = args.distro
			shutit.build['mount_docker']    = args.mount_docker
			shutit.build['walkthrough']     = args.walkthrough
			shutit.build['training']        = args.training
			shutit.build['exam']            = args.exam
			shutit.build['choose_config']   = args.choose_config
			if shutit.build['exam'] and not shutit.build['training']:
				# We want it to be quiet
				#print('--exam implies --training, setting --training on!')
				print('Exam starting up')
				shutit.build['training'] = True
			if (shutit.build['exam'] or shutit.build['training']) and not shutit.build['walkthrough']:
				if not shutit.build['exam']:
					print('--training or --exam implies --walkthrough, setting --walkthrough on!')
				shutit.build['walkthrough'] = True
			if type(args.video) == list and args.video[0] >= 0:
				shutit.build['walkthrough']      = True
				shutit.build['walkthrough_wait'] = float(args.video[0])
				shutit.build['video']            = True
				if shutit.build['training']:
					print('--video and --training mode incompatible')
					handle_exit(exit_code=1)
				if shutit.build['exam']:
					print('--video and --exam mode incompatible')
					handle_exit(exit_code=1)
			# Create a test session object if needed.
			if shutit.build['exam']:
				shutit.build['exam_object'] = shutit_exam.ShutItExamSession()
		elif shutit.action['list_configs']:
			shutit.list_configs['cfghistory'] = args.history
		elif shutit.action['list_modules']:
			shutit.list_modules['long'] = args.long
			shutit.list_modules['sort'] = args.sort

		# What are we building on? Convert arg to conn_module we use.
		if args.delivery == 'docker' or args.delivery is None:
			shutit.build['conn_module'] = 'shutit.tk.conn_docker'
			shutit.build['delivery']    = 'docker'
		elif args.delivery == 'ssh':
			shutit.build['conn_module'] = 'shutit.tk.conn_ssh'
			shutit.build['delivery']    = 'ssh'
		elif args.delivery == 'bash' or args.delivery == 'dockerfile':
			shutit.build['conn_module'] = 'shutit.tk.conn_bash'
			shutit.build['delivery']    = args.delivery
		# If the image_tag has been set then ride roughshod over the ignoreimage value if not supplied
		if args.image_tag != '' and args.ignoreimage is None:
			args.ignoreimage = True
		# If ignoreimage is still not set, then default it to False
		if args.ignoreimage is None:
			args.ignoreimage = False

		# Get these early for this part of the build.
		# These should never be config arguments, since they are needed before config is passed in.
		if args.shutit_module_path is not None:
			module_paths = args.shutit_module_path.split(':')
			if '.' not in module_paths:
				module_paths.append('.')
			args.set.append(('host', 'shutit_module_path', ':'.join(module_paths)))
		shutit.build['trace']            = args.trace
		shutit.build['interactive']      = int(args.interactive)
		shutit.build['extra_configs']    = args.config
		shutit.build['config_overrides'] = args.set
		shutit.build['ignorestop']       = args.ignorestop
		shutit.build['ignoreimage']      = args.ignoreimage
		shutit.build['imageerrorok']     = args.imageerrorok
		shutit.build['tag_modules']      = args.tag_modules
		shutit.build['deps_only']        = args.deps_only
		shutit.build['always_echo']      = args.echo
		shutit.target['docker_image']    = args.image_tag
		# Finished parsing args.
		# Sort out config path
		if shutit.action['list_configs'] or shutit.action['list_modules'] or shutit.action['list_deps'] or shutit.build['loglevel'] == logging.DEBUG:
			shutit.build['log_config_path'] = shutit.build['shutit_state_dir'] + '/config/' + shutit.build['build_id']
			if os.path.exists(shutit.build['log_config_path']):
				print(shutit.build['log_config_path'] + ' exists. Please move and re-run.')
				handle_exit(exit_code=1)
			os.makedirs(shutit.build['log_config_path'])
			os.chmod(shutit.build['log_config_path'],0o777)
		else:
			shutit.build['log_config_path'] = None
		# Tutorial stuff. TODO: ditch tutorial mode
		#The config is read in the following order:
		#~/.shutit/config
		#	- Host- and username-specific config for this host.
		#/path/to/this/shutit/module/configs/build.cnf
		#	- Config specifying what should be built when this module is invoked.
		#/your/path/to/<configname>.cnf
		#	- Passed-in config (via --config, see --help)
		#command-line overrides, eg -s com.mycorp.mymodule.module name value
		# Set up trace as fast as possible.
		if shutit.build['trace']:
			def tracefunc(frame, event, arg, indent=[0]):
				if event == 'call':
					shutit.log('-> call function: ' + frame.f_code.co_name + ' ' + str(frame.f_code.co_varnames),level=logging.DEBUG)
				elif event == 'return':
					shutit.log('<- exit function: ' + frame.f_code.co_name,level=logging.DEBUG)
				return tracefunc
			sys.settrace(tracefunc)


def load_configs():
	"""Responsible for loading config files into ShutIt.
	Recurses down from configured shutit module paths.
	"""
	shutit = shutit_global.shutit
	# Get root default config.
	configs = [('defaults', StringIO(_default_cnf)), os.path.expanduser('~/.shutit/config'), os.path.join(shutit.host['shutit_path'], 'config'), 'configs/build.cnf']
	# Add the shutit global host- and user-specific config file.
	# Add the local build.cnf
	# Get passed-in config(s)
	for config_file_name in shutit.build['extra_configs']:
		run_config_file = os.path.expanduser(config_file_name)
		if not os.path.isfile(run_config_file):
			print('Did not recognise ' + run_config_file + ' as a file - do you need to touch ' + run_config_file + '?')
			handle_exit(exit_code=0)
		configs.append(run_config_file)
	# Image to use to start off. The script should be idempotent, so running it
	# on an already built image should be ok, and is advised to reduce diff space required.
	if shutit.action['list_configs'] or shutit.build['loglevel'] == logging.DEBUG:
		msg = ''
		for c in configs:
			if type(c) is tuple:
				c = c[0]
			msg = msg + '    \n' + c
			shutit.log('    ' + c,level=logging.DEBUG)
		if shutit.action['list_configs'] or shutit.build['loglevel'] <= logging.DEBUG:
			if shutit.build['log_config_path']:
				f = open(shutit.build['log_config_path'] + '/config_file_order.txt','w')
				f.write(msg)
				f.close()

	# Interpret any config overrides, write to a file and add them to the
	# list of configs to be interpreted
	if shutit.build['config_overrides']:
		# We don't need layers, this is a temporary configparser
		override_cp = ConfigParser.RawConfigParser()
		for o_sec, o_key, o_val in shutit.build['config_overrides']:
			if not override_cp.has_section(o_sec):
				override_cp.add_section(o_sec)
			override_cp.set(o_sec, o_key, o_val)
		override_fd = StringIO()
		override_cp.write(override_fd)
		override_fd.seek(0)
		configs.append(('overrides', override_fd))

	cfg_parser = get_configs(configs)
	get_base_config(cfg_parser)
	if shutit.build['loglevel'] <= logging.DEBUG:
		# Set up the manhole.
		try:
			import manhole
			manhole.install(
				verbose=True,
				patch_fork=True,
				activate_on=None,
				oneshot_on=None,
				sigmask=manhole.ALL_SIGNALS,
				socket_path=None,
				reinstall_delay=0.5,
				locals=None
			)
		except Exception:
			shutit.log('No manhole package available, skipping import',level=logging.DEBUG)
			pass



def load_shutit_modules():
	"""Responsible for loading the shutit modules based on the configured module
	paths.
	"""
	shutit = shutit_global.shutit
	if shutit.build['loglevel'] <= logging.DEBUG:
		shutit.log('ShutIt module paths now: ',level=logging.DEBUG)
		shutit.log(shutit.host['shutit_module_path'],level=logging.DEBUG)
	for shutit_module_path in shutit.host['shutit_module_path']:
		load_all_from_path(shutit_module_path)


def list_modules(long_output=None,sort_order=None):
	"""Display a list of loaded modules.

	Config items:
		- shutit.list_modules['long']
		  If set, also print each module's run order value

		- shutit.list_modules['sort']
		  Select the column by which the list is ordered:
			- id: sort the list by module id
			- run_order: sort the list by module run order

	The output is also saved to ['build']['log_config_path']/module_order.txt

	Dependencies: operator
	"""
	shutit = shutit_global.shutit
	cfg = shutit.cfg
	# list of module ids and other details
	# will also contain column headers
	table_list = []
	if long_output is None:
		long_output = shutit.list_modules['long']
	if sort_order is None:
		sort_order = shutit.list_modules['sort']
	if long_output:
		# --long table: sort modules by run order
		table_list.append(["Order","Module ID","Description","Run Order","Built","Compatible"])
		#table_list.append(["Order","Module ID","Description","Run Order","Built"])
	else:
		# "short" table ==> sort module by module_id
		#table_list.append(["Module ID","Description","Built"])
		table_list.append(["Module ID","Description","Built","Compatible"])

	if sort_order == 'run_order':
		a = {}
		for m in shutit.shutit_modules:
			a.update({m.module_id:m.run_order})
		# sort dict by run_order; see http://stackoverflow.com/questions/613183/sort-a-python-dictionary-by-value
		b = sorted(a.items(), key=operator.itemgetter(1))
		count = 0
		# now b is a list of tuples (module_id, run_order)
		for pair in b:
			# module_id is the first item of the tuple
			k = pair[0]
			for m in shutit.shutit_modules:
				if m.module_id == k:
					count += 1
					compatible = True
					if not cfg[m.module_id]['shutit.core.module.build']:
						cfg[m.module_id]['shutit.core.module.build'] = True
						if determine_compatibility(m.module_id) == 0:
							compatible = True
						else:
							compatible = False
						cfg[m.module_id]['shutit.core.module.build'] = False
					if long_output:
						table_list.append([str(count),m.module_id,m.description,str(m.run_order),str(cfg[m.module_id]['shutit.core.module.build']),str(compatible)])
						#table_list.append([str(count),m.module_id,m.description,str(m.run_order),str(cfg[m.module_id]['shutit.core.module.build'])])
					else:
						table_list.append([m.module_id,m.description,str(cfg[m.module_id]['shutit.core.module.build']),str(compatible)])
	elif sort_order == 'id':
		a = []
		for m in shutit.shutit_modules:
			a.append(m.module_id)
		a.sort()
		for k in a:
			for m in shutit.shutit_modules:
				if m.module_id == k:
					count = 1
					compatible = True
					if not cfg[m.module_id]['shutit.core.module.build']:
						cfg[m.module_id]['shutit.core.module.build'] = True
						if determine_compatibility(m.module_id) == 0:
							compatible = True
						else:
							compatible = False
					if long_output:
						table_list.append([str(count),m.module_id,m.description,str(m.run_order),str(cfg[m.module_id]['shutit.core.module.build']),str(compatible)])
						#table_list.append([str(count),m.module_id,m.description,str(m.run_order),str(cfg[m.module_id]['shutit.core.module.build'])])
					else:
						#table_list.append([m.module_id,m.description,str(cfg[m.module_id]['shutit.core.module.build'])])
						table_list.append([m.module_id,m.description,str(cfg[m.module_id]['shutit.core.module.build']),str(compatible)])

	# format table for display
	table = texttable.Texttable()
	table.add_rows(table_list)
	# Base length of table on length of strings
	colwidths = []
	for item in table_list:
		for n in range(0,len(item)):
			# default to 10 chars
			colwidths.append(10)
		break
	for item in table_list:
		for n in range(0,len(item)-1):
			if len(str(item[n])) > colwidths[n]:
				colwidths[n] = len(str(item[n]))
	table.set_cols_width(colwidths)
	msg = table.draw()
	print('\n' + msg)
	if shutit.build['log_config_path']:
		f = open(shutit.build['log_config_path'] + '/module_order.txt','w')
		f.write(msg)
		f.close()


# TODO: does this still work?
def print_config(cfg, hide_password=True, history=False, module_id=None):
	"""Returns a string representing the config of this ShutIt run.
	"""
	cp = shutit_global.shutit.config_parser
	s = ''
	keys1 = list(cfg.keys())
	if keys1:
		keys1.sort()
	for k in keys1:
		if module_id is not None and k != module_id:
			continue
		if type(k) == str and type(cfg[k]) == dict:
			s += '\n[' + k + ']\n'
			keys2 = list(cfg[k].keys())
			if keys2:
				keys2.sort()
			for k1 in keys2:
					line = ''
					line += k1 + ':'
					# If we want to hide passwords, we do so using a sha512
					# done an aritrary number of times (27).
					if hide_password and (k1 == 'password' or k1 == 'passphrase'):
						p = hashlib.sha512(cfg[k][k1]).hexdigest()
						i = 27
						while i > 0:
							i -= 1
							p = hashlib.sha512(s).hexdigest()
						line += p
					else:
						if type(cfg[k][k1] == bool):
							line += str(cfg[k][k1])
						elif type(cfg[k][k1] == str):
							line += cfg[k][k1]
					if history:
						try:
							line += (30-len(line)) * ' ' + ' # ' + cp.whereset(k, k1)
						except Exception:
							# Assume this is because it was never set by a config parser.
							line += (30-len(line)) * ' ' + ' # ' + "defaults in code"
					s += line + '\n'
	return s

def set_pexpect_child(key, child):
	"""Set a pexpect child in the global dictionary by key.
	"""
	shutit_global.shutit.shutit_pexpect_children.update({key:child})

def get_pexpect_child(key):
	"""Get a pexpect child in the global dictionary by key.
	"""
	return shutit_global.shutit.shutit_pexpect_children[key]

def load_all_from_path(path):
	"""Dynamically imports files within the same directory (in the end, the path).
	"""
	shutit = shutit_global.shutit
	#111: handle expanded paths
	path = os.path.abspath(path)
	#http://stackoverflow.com/questions/301134/dynamic-module-import-in-python
	if os.path.abspath(path) == shutit.shutit_main_dir:
		return
	if not os.path.exists(path):
		return
	if os.path.exists(path + '/STOPBUILD') and not shutit.shutit.build['ignorestop']:
		shutit.log('Ignoring directory: ' + path + ' as it has a STOPBUILD file in it. Pass --ignorestop to shutit run to override.',level=logging.DEBUG)
		return
	for sub in glob.glob(os.path.join(path, '*')):
		subpath = os.path.join(path, sub)
		if os.path.isfile(subpath):
			load_mod_from_file(subpath)
		elif os.path.isdir(subpath):
			load_all_from_path(subpath)


def load_mod_from_file(fpath):
	"""Loads modules from a .py file into ShutIt if there are no modules from
	this file already.
	We expect to have a callable 'module/0' which returns one or more module
	objects.
	If this doesn't exist we assume that the .py file works in the old style
	(automatically inserting the module into shutit_global) or it's not a shutit
	module.
	"""
	shutit = shutit_global.shutit
	fpath = os.path.abspath(fpath)
	file_ext = os.path.splitext(os.path.split(fpath)[-1])[-1]
	if file_ext.lower() != '.py':
		return
	with open(fpath) as f:
		content = f.read().splitlines()
	ok = False
	for line in content:
		if line.strip() == 'from shutit_module import ShutItModule':
			ok = True
			break
	if not ok:
		shutit.log('Rejected file: ' + fpath,level=logging.DEBUG)
		return
	# Note that this attribute will only be set for 'new style' module loading, # this should be ok because 'old style' loading checks for duplicate # existing modules.
	# TODO: this is quadratic complexity
	existingmodules = [
		m for m in shutit.shutit_modules
		if getattr(m, '__module_file', None) == fpath
	]
	if len(existingmodules) > 0:
		shutit.log('Module already seen: ' + fpath,level=logging.DEBUG)
		return
	# Looks like it's ok to load this file
	shutit.log('Loading source for: ' + fpath,level=logging.DEBUG)

	# Add this directory to the python path iff not already there.
	directory = os.path.dirname(fpath)
	if directory not in sys.path:
		sys.path.append(os.path.dirname(fpath))
	mod_name = base64.b32encode(fpath.encode()).decode().replace('=', '')
	pymod = imp.load_source(mod_name, fpath)

	# Got the python module, now time to pull the shutit module(s) out of it.
	targets = [
		('module', shutit.shutit_modules), ('conn_module', shutit.conn_modules)
	]
	shutit.build['source'] = {}
	for attr, target in targets:
		modulefunc = getattr(pymod, attr, None)
		# Old style or not a shutit module, nothing else to do
		if not callable(modulefunc):
			return
		modules = modulefunc()
		if type(modules) is not list:
			modules = [modules]
		for module in modules:
			setattr(module, '__module_file', fpath)
			ShutItModule.register(module.__class__)
			target.add(module)
			shutit.build['source'][fpath] = open(fpath).read()


# Build report
def build_report(msg=''):
	"""Resposible for constructing a report to be output as part of the build.
	Retrurns report as a string.
	"""
	shutit = shutit_global.shutit
	s = ''
	s += '################################################################################\n'
	s += '# COMMAND HISTORY BEGIN ' + shutit.build['build_id'] + '\n'
	s += get_commands()
	s += '# COMMAND HISTORY END ' + shutit.build['build_id'] + '\n'
	s += '################################################################################\n'
	s += '################################################################################\n'
	s += '# BUILD REPORT FOR BUILD BEGIN ' + shutit.build['build_id'] + '\n'
	s += '# ' + msg + '\n'
	if shutit.build['report'] != '':
		s += shutit.build['report'] + '\n'
	else:
		s += '# Nothing to report\n'

	if 'container_id' in shutit.target:
		s += '# CONTAINER_ID: ' + shutit.target['container_id'] + '\n'
	s += '# BUILD REPORT FOR BUILD END ' + shutit.build['build_id'] + '\n'
	s += '###############################################################################\n'
	return s

def get_commands():
	"""Gets command that have been run and have not been redacted.
	"""
	s = ''
	for c in shutit_global.shutit.build['shutit_command_history']:
		if type(c) == str:
			#Ignore commands with leading spaces
			if c and c[0] != ' ':
				s += c + '\n'
	return s


def get_hash(string_to_hash):
	"""Helper function to get preceding integer
	eg com.openbet == 1003189494
	>>> import binascii
	>>> abs(binascii.crc32(b'shutit.tk'))
	782914092

	Recommended means of determining run order integer part.
	"""
	return abs(binascii.crc32(string_to_hash.encode()))


def util_raw_input(prompt='', default=None, ispass=False, use_readline=True):
	"""Handles raw_input calls, and switches off interactivity if there is apparently
	no controlling terminal (or there are any other problems)
	"""
	if use_readline:
		try:
			readline.read_init_file('/etc/inputrc')
		except:
			pass
		readline.parse_and_bind('tab: complete')
	prompt = '\r\n' + prompt
	if ispass:
		prompt += '\r\nInput Secret: '
	sanitize_terminal()
	if shutit_global.shutit.build['interactive'] == 0:
		return default
	if not determine_interactive():
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
		except:
			msg = 'Problems getting raw input, assuming no controlling terminal.'
	if ispass:
		return getpass.getpass(prompt=prompt)
	else:
		resp = raw_input(prompt).strip()
		if resp == '':
			return default
		else:
			return resp
	set_noninteractive(msg=msg)
	return default


def determine_interactive():
	"""Determine whether we're in an interactive shell.
	Sets interactivity off if appropriate.
	cf http://stackoverflow.com/questions/24861351/how-to-detect-if-python-script-is-being-run-as-a-background-process
	"""
	shutit = shutit_global.shutit
	try:
		if not sys.stdout.isatty() or os.getpgrp() != os.tcgetpgrp(sys.stdout.fileno()):
			if shutit is not None:
				set_noninteractive()
			return False
	except Exception:
		if shutit is not None:
			set_noninteractive(msg='Problems determining interactivity, assuming not.')
		return False
	if shutit.build['interactive'] == 0:
		return False
	return True


def set_noninteractive(msg="setting non-interactive"):
	shutit = shutit_global.shutit
	shutit.log(msg,level=logging.DEBUG)
	shutit.build['interactive'] = 0


def print_stack_trace():
	shutit = shutit_global.shutit
	shutit.log('================================================================================',transient=True)
	shutit.log('Stack trace was:\n================================================================================',transient=True)
	import traceback
	(a,b,c) = sys.exc_info()
	traceback.print_tb(c)
	shutit.log('================================================================================',transient=True)


# get the ordinal for a given char, in a friendly way
def get_wide_hex(char):
	if len(char) != 2:
		return r'\x' + hex(ord(char))[2:]
	return r'\u' + hex(0x10000 + (ord(char[0]) - 0xD800) * 0x400 + (ord(char[1]) - 0xDC00))[2:]


# CTRL-\ HANDLING CODE STARTS
def ctrl_quit_signal_handler(_,frame):
	print('CRTL-\ caught, hard-exiting ShutIt')
	shutit_frame = get_shutit_frame(frame)
	if shutit_frame:
		shutit_main.do_finalize()
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
	global ctrl_c_calls
	ctrl_c_calls += 1
	if ctrl_c_calls > 10:
		handle_exit(exit_code=1)
	"""CTRL-c signal handler - enters a pause point if it can.
	"""
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
		print(colourise(31,"\rYou may need to wait for a command to complete before a pause point is available. Alternatively, CTRL-\ to quit."))
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


def module_ids(rev=False):
	"""Gets a list of module ids guaranteed to be sorted by run_order, ignoring conn modules
	(run order < 0).
	"""
	shutit = shutit_global.shutit
	ids = sorted(list(shutit.shutit_map.keys()),key=lambda module_id: shutit.shutit_map[module_id].run_order)
	if rev:
		return list(reversed(ids))
	else:
		return ids

def allowed_module_ids(rev=False):
	"""Gets a list of module ids that are allowed to be run, guaranteed to be sorted by run_order, ignoring conn modules (run order < 0).
	"""
	module_ids_list = module_ids(rev)
	_allowed_module_ids = []
	for module_id in module_ids_list:
		if allowed_image(module_id):
			_allowed_module_ids.append(module_id)
	return _allowed_module_ids


def print_modules():
	"""Returns a string table representing the modules in the ShutIt module map.
	"""
	shutit = shutit_global.shutit
	cfg = shutit.cfg
	module_string = ''
	module_string += 'Modules: \n'
	module_string += '    Run order    Build    Remove    Module ID\n'
	for module_id in module_ids():
		module_string += '    ' + str(shutit.shutit_map[module_id].run_order) + '        ' + str(
			cfg[module_id]['shutit.core.module.build']) + '    ' + str(
			cfg[module_id]['shutit.core.module.remove']) + '    ' + module_id + '\n'
	return module_string


def config_collection():
	"""Collect core config from config files for all seen modules.
	"""
	shutit = shutit_global.shutit
	shutit.log('In config_collection',level=logging.DEBUG)
	cfg = shutit.cfg
	for module_id in module_ids():
		# Default to None so we can interpret as ifneeded
		shutit.get_config(module_id, 'shutit.core.module.build', None, boolean=True, forcenone=True)
		shutit.get_config(module_id, 'shutit.core.module.remove', False, boolean=True)
		shutit.get_config(module_id, 'shutit.core.module.tag', False, boolean=True)
		# Default to allow any image
		shutit.get_config(module_id, 'shutit.core.module.allowed_images', [".*"])
		module = shutit.shutit_map[module_id]
		cfg_file = os.path.dirname(module.__module_file) + '/configs/build.cnf'
		if os.path.isfile(cfg_file):
			# use shutit.get_config, forcing the passed-in default
			config_parser = ConfigParser.ConfigParser()
			config_parser.read(cfg_file)
			for section in config_parser.sections():
				if section == module_id:
					for option in config_parser.options(section):
						if option == 'shutit.core.module.allowed_images':
							override = False
							for mod, opt, val in shutit.build['config_overrides']:
								# skip overrides
								if mod == module_id and opt == option:
									override = True
							if override:
								continue
							value = config_parser.get(section,option)
							if option == 'shutit.core.module.allowed_images':
								value = json.loads(value)
							shutit.get_config(module_id, option, value, forcedefault=True)
		# ifneeded will (by default) only take effect if 'build' is not
		# specified. It can, however, be forced to a value, but this
		# should be unusual.
		if cfg[module_id]['shutit.core.module.build'] is None:
			shutit.get_config(module_id, 'shutit.core.module.build_ifneeded', True, boolean=True)
			cfg[module_id]['shutit.core.module.build'] = False
		else:
			shutit.get_config(module_id, 'shutit.core.module.build_ifneeded', False, boolean=True)


def disallowed_module_ids(rev=False):
	"""Gets a list of disallowed module ids that are not allowed to be run, guaranteed to be sorted by run_order, ignoring conn modules (run order < 0).
	"""
	module_ids_list = module_ids(rev)
	_disallowed_module_ids = []
	for module_id in module_ids_list:
		if not allowed_image(module_id):
			_disallowed_module_ids.append(module_id)
	return _disallowed_module_ids


def is_to_be_built_or_is_installed(shutit_module_obj):
	"""Returns true if this module is configured to be built, or if it is already installed.
	"""
	cfg = shutit_global.shutit.cfg
	if cfg[shutit_module_obj.module_id]['shutit.core.module.build']:
		return True
	return is_installed(shutit_module_obj)


def config_collection_for_built(throw_error=True,silent=False):
	"""Collect configuration for modules that are being built.
	When this is called we should know what's being built (ie after
	dependency resolution).
	"""
	shutit = shutit_global.shutit
	shutit.log('In config_collection_for_built',level=logging.DEBUG)
	cfg = shutit.cfg
	for module_id in module_ids():
		# Get the config even if installed or building (may be needed in other hooks, eg test).
		if (is_to_be_built_or_is_installed( shutit.shutit_map[module_id]) and
			not shutit.shutit_map[module_id].get_config(shutit)):
				shutit.fail(module_id + ' failed on get_config')
		# Collect the build.cfg if we are building here.
		# If this file exists, process it.
		if cfg[module_id]['shutit.core.module.build'] and not shutit.build['have_read_config_file']:
			module = shutit.shutit_map[module_id]
			cfg_file = os.path.dirname(module.__module_file) + '/configs/build.cnf'
			if os.path.isfile(cfg_file):
				shutit.build['have_read_config_file'] = True
				# use shutit.get_config, forcing the passed-in default
				config_parser = ConfigParser.ConfigParser()
				config_parser.read(cfg_file)
				for section in config_parser.sections():
					if section == module_id:
						for option in config_parser.options(section):
							override = False
							for mod, opt, val in shutit.build['config_overrides']:
								# skip overrides
								if mod == module_id and opt == option:
									override = True
							if override:
								continue
							is_bool = (type(cfg[module_id][option]) == bool)
							if is_bool:
								value = config_parser.getboolean(section,option)
							else:
								value = config_parser.get(section,option)
							if option == 'shutit.core.module.allowed_images':
								value = json.loads(value)
							shutit.get_config(module_id, option, value, forcedefault=True)
	# Check the allowed_images against the base_image
	passed = True
	for module_id in module_ids():
		if (cfg[module_id]['shutit.core.module.build'] and
		   (cfg[module_id]['shutit.core.module.allowed_images'] and
		    shutit.target['docker_image'] not in cfg[module_id]['shutit.core.module.allowed_images'])):
			if not allowed_image(module_id):
				passed = False
				if not silent:
					print('\n\nWARNING!\n\nAllowed images for ' + module_id + ' are: ' + str(cfg[module_id]['shutit.core.module.allowed_images']) + ' but the configured image is: ' + shutit.target['docker_image'] + '\n\nIs your shutit_module_path set correctly?\n\nIf you want to ignore this, pass in the --ignoreimage flag to shutit.\n\n')
	if not passed:
		if not throw_error:
			return False
		if shutit.build['imageerrorok']:
			# useful for test scripts
			print('Exiting on allowed images error, with return status 0')
			handle_exit(exit_code=1)
		else:
			raise ShutItFailException('Allowed images checking failed')
	return True


def determine_compatibility(module_id):
	shutit = shutit_global.shutit
	cfg = shutit.cfg
	# Allowed images
	if (cfg[module_id]['shutit.core.module.allowed_images'] and shutit.target['docker_image'] not in cfg[module_id]['shutit.core.module.allowed_images']) and not allowed_image(module_id):
			return 1
	# Build methods
	if cfg[module_id]['shutit.core.module.build'] and shutit.build['delivery'] not in shutit.shutit_map[module_id].ok_delivery_methods:
		return 2
	return 0


def is_installed(shutit_module_obj):
	"""Returns true if this module is installed.
	Uses cache where possible.
	"""
	shutit = shutit_global.shutit
	# Cache first
	if shutit_module_obj.module_id in shutit.get_current_shutit_pexpect_session_environment().modules_installed:
		return True
	if shutit_module_obj.module_id in shutit.get_current_shutit_pexpect_session_environment().modules_not_installed:
		return False
	# Is it installed?
	if shutit_module_obj.is_installed(shutit):
		shutit.get_current_shutit_pexpect_session_environment().modules_installed.append(shutit_module_obj.module_id)
		return True
	# If not installed, and not in cache, add it.
	else:
		if shutit_module_obj.module_id not in shutit.get_current_shutit_pexpect_session_environment().modules_not_installed:
			shutit.get_current_shutit_pexpect_session_environment().modules_not_installed.append(shutit_module_obj.module_id)
		return False


def allowed_image(module_id):
	"""Given a module id, determine whether the image is allowed to be built.
	"""
	shutit = shutit_global.shutit
	shutit.log("In allowed_image: " + module_id,level=logging.DEBUG)
	cfg = shutit.cfg
	if shutit.build['ignoreimage']:
		shutit.log("ignoreimage == true, returning true" + module_id,level=logging.DEBUG)
		return True
	shutit.log(str(cfg[module_id]['shutit.core.module.allowed_images']),level=logging.DEBUG)
	if cfg[module_id]['shutit.core.module.allowed_images']:
		# Try allowed images as regexps
		for regexp in cfg[module_id]['shutit.core.module.allowed_images']:
			if not check_regexp(regexp):
				shutit.fail('Illegal regexp found in allowed_images: ' + regexp)
			if re.match('^' + regexp + '$', shutit.target['docker_image']):
				return True
	return False


def handle_exit(exit_code=0,loglevel=logging.DEBUG,msg=None):
	shutit = shutit_global.shutit
	if not msg:
		msg = '\nExiting with error code: ' + str(exit_code)
	if not shutit:
		if exit_code != 0:
			#print_stack_trace()
			print(msg)
			print('Resetting terminal')
	else:
		if exit_code != 0:
			shutit.log('Exiting with error code: ' + str(exit_code),level=loglevel)
			shutit.log('Resetting terminal',level=loglevel)
	sanitize_terminal()
	sys.exit(exit_code)


def sendline(child,
             line):
	"""Handles sending of line to pexpect object.
	"""
	child.sendline(line)

def sanitize_terminal():
	os.system('stty sane')


def match_string(string_to_match, regexp):
	"""Get regular expression from the first of the lines passed
	in in string that matched. Handles first group of regexp as
	a return value.

	@param string_to_match: String to match on
	@param regexp: Regexp to check (per-line) against string

	@type string_to_match: string
	@type regexp: string

	Returns None if none of the lines matched.

	Returns True if there are no groups selected in the regexp.
	else returns matching group (ie non-None)
	"""
	shutit = shutit_global.shutit
	if type(string_to_match) != str:
		return None
	lines = string_to_match.split('\r\n')
	# sometimes they're separated by just a carriage return...
	new_lines = []
	for line in lines:
		new_lines = new_lines + line.split('\r')
	# and sometimes they're separated by just a newline...
	for line in lines:
		new_lines = new_lines + line.split('\n')
	lines = new_lines
	if not check_regexp(regexp):
		shutit.fail('Illegal regexp found in match_string call: ' + regexp)
	for line in lines:
		match = re.match(regexp, line)
		if match is not None:
			if len(match.groups()) > 0:
				return match.group(1)
			else:
				return True
	return None
# alias for back-compatibility
get_re_from_child = match_string



def get_input(msg, default='', valid=[], boolean=False, ispass=False, colour='32'):
	"""Gets input from the user, and returns the answer.

	@param msg:       message to send to user
	@param default:   default value if nothing entered
	@param valid:     valid input values (default == empty list == anything allowed)
	@param boolean:   whether return value should be boolean
	@param ispass:    True if this is a password (ie whether to not echo input)
	"""
	shutit = shutit_global.shutit
	if boolean and valid == []:
		valid = ('yes','y','Y','1','true','no','n','N','0','false')
	answer = util_raw_input(prompt=colourise(colour,msg),ispass=ispass)
	if boolean and answer in ('', None) and default != '':
		return default
	if valid != []:
		while answer not in valid:
			shutit.log('Answer must be one of: ' + str(valid),transient=True)
			answer = util_raw_input(prompt=colourise(colour,msg),ispass=ispass)
	if boolean and answer in ('yes','y','Y','1','true','t','YES'):
		return True
	if boolean and answer in ('no','n','N','0','false','f','NO'):
		return False
	if answer in ('',None):
		return default
	else:
		return answer

def get_send_command(send):
	"""Internal helper function to get command that's really sent
	"""
	if send == None:
		return send
	cmd_arr = send.split()
	if len(cmd_arr) and cmd_arr[0] in ('md5sum','sed','head'):
		newcmd = get_command(cmd_arr[0])
		send = send.replace(cmd_arr[0],newcmd)
	return send


def get_command(command):
	"""Helper function for osx - return gnu utils rather than default for
	   eg head and md5sum where possible.
	"""
	shutit = shutit_global.shutit
	if command in ('head','md5sum'):
		if shutit.get_current_shutit_pexpect_session_environment().distro == 'osx':
			return '''PATH="/usr/local/opt/coreutils/libexec/gnubin:$PATH" ''' + command + ' '
		else:
			return command + ' '
	return command

def check_delivery_method(method):
	global allowed_delivery_methods
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
locale:en_US.UTF-8
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
