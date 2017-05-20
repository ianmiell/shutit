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
try:
	from StringIO import StringIO
except ImportError: # pragma: no cover
	from io import StringIO
import argparse
import base64
import binascii
import glob
import hashlib
import imp
import json
import logging
import operator
import os
import random
import re
import stat
import string
import sys
import threading
import time
import subprocess
import textwrap
from distutils.dir_util import mkpath
import texttable
try:
	import ConfigParser
except ImportError: # pragma: no cover
	import configparser as ConfigParser
import pexpect
import shutit
import shutit_assets
import shutit_skeleton
import shutit_exam
import shutit_global
from shutit_module import ShutItFailException
from shutit_module import ShutItModule

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

# TODO: move to shutit_class.py?
def find_asset(shutit, filename):
	(head,filename) = os.path.split(filename)
	if head == '':
		dirs = ['/usr/share/dict',
				sys.prefix,
				os.path.join(sys.prefix,'local'),
				shutit.shutit_main_dir,
				os.path.join(shutit.shutit_main_dir,'../../..'),
				shutit.host['shutit_path'],
				'/usr/local'
			   ]
		dirs = dirs + sys.path
	else:
		dirs = ['/usr/share/dict' + '/' + head,
				sys.prefix + '/' + head,
				os.path.join(sys.prefix,'local') + '/' + head,
				shutit.shutit_main_dir + '/' + head,
				os.path.join(shutit.shutit_main_dir,'../../..') + '/' + head,
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



# Manage config settings, returning a dict representing the settings
# that have been sanity-checked.
def get_base_config(shutit, cfg_parser):
	"""Responsible for getting core configuration from config files.
	"""
	shutit.config_parser = cp = cfg_parser
	# BEGIN Read from config files
	# build - details relating to the build
	shutit.build['privileged']                 = cp.getboolean('build', 'privileged')
	shutit.build['base_image']                 = cp.get('build', 'base_image')
	shutit.build['dotest']                     = cp.get('build', 'dotest')
	shutit.build['net']                        = cp.get('build', 'net')
	shutit.build['step_through']               = False
	shutit.build['ctrlc_stop']                 = False
	shutit.build['ctrlc_passthrough']          = False
	shutit.build['have_read_config_file']      = False
	# Width of terminal to set up on login and assume for other cases.
	shutit.build['vagrant_run_dir']            = None
	shutit.build['this_vagrant_run_dir']       = None
	# Take a command-line arg if given, else default.
	if shutit.build['conn_module'] is None:
		shutit.build['conn_module']            = cp.get('build', 'conn_module')
	# Whether to accept default configs
	shutit.build['accept_defaults']            = None
	# target - the target of the build, ie the container
	shutit.target['hostname']                  = cp.get('target', 'hostname')
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
	if isinstance(shutit.host['password'],str):
		shutit_global.shutit_global_object.secret_words_set.add(shutit.host['password'])
	shutit_global.shutit_global_object.logfile = cp.get('host', 'logfile')
	shutit.host['shutit_module_path']          = cp.get('host', 'shutit_module_path').split(':')

	# repository - information relating to docker repository/registry
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
	if isinstance(shutit.repository['password'],str):
		shutit_global.shutit_global_object.secret_words_set.add(shutit.repository['password'])
	shutit.repository['email']                 = cp.get('repository', 'email')
	shutit.repository['tag_name']              = cp.get('repository', 'tag_name')
	# END Read from config files

	# BEGIN Standard expects
	# It's important that these have '.*' in them at the start, so that the matched data is reliably 'after' in the
	# child object. Use these where possible to make things more consistent.
	# Attempt to capture any starting prompt (when starting) with this regexp.
	shutit.expect_prompts['base_prompt']       = '\r\n.*[@#$] '
	# END Standard expects

	if shutit.target['docker_image'] == '':
		shutit.target['docker_image'] = shutit.build['base_image']
	# END tidy configs up

	# BEGIN warnings
	# FAILS begins
	# rm is incompatible with repository actions
	if shutit.target['rm'] and (shutit.repository['tag'] or shutit.repository['push'] or shutit.repository['save'] or shutit.repository['export']): # pragma: no cover
		print("Can't have [target]/rm and [repository]/(push/save/export) set to true")
		handle_exit(shutit=shutit, exit_code=1)
	if shutit.target['hostname'] != '' and shutit.build['net'] != '' and shutit.build['net'] != 'bridge': # pragma: no cover
		print('\n\ntarget/hostname or build/net configs must be blank\n\n')
		handle_exit(shutit=shutit, exit_code=1)
	# FAILS ends


# Returns the config dict
def parse_args(shutit, set_loglevel=None):
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
	process_args(shutit, convert_args(args))


# Turns args returned from parser.parse_args into a ShutitArgs object
def convert_args(args):
	assert args.action is not None
	assert isinstance(args.action,str)
	if args.action == 'skeleton':
		assert args.delivery is not None or args.delivery is None  # Does it exist?
		assert args.accept in (True,False,None)
		assert not (args.shutitfiles and args.script),'Cannot have any two of script, -d/--shutitfiles <files> as arguments'
		assert isinstance(args.base_image,str)
		assert isinstance(args.depends,str)
		assert isinstance(args.shutitfiles,list)
		assert isinstance(args.name,str)
		assert isinstance(args.domain,str)
		assert isinstance(args.pattern,str)
	return args



def process_args(shutit, args):
	"""Process the args we have.
	"""
	if args.action == 'version':
		print('ShutIt version: ' + shutit.shutit_version)
		handle_exit(shutit=shutit, exit_code=0)

	# What are we asking shutit to do?
	shutit.action['list_configs'] = args.action == 'list_configs'   # TODO: abstract away to shutitconfig object
	shutit.action['list_modules'] = args.action == 'list_modules'   # TODO: abstract away to shutitconfig object
	shutit.action['list_deps']    = args.action == 'list_deps'   # TODO: abstract away to shutitconfig object
	shutit.action['skeleton']     = args.action == 'skeleton'   # TODO: abstract away to shutitconfig object
	shutit.action['build']        = args.action == 'build'   # TODO: abstract away to shutitconfig object
	shutit.action['run']          = args.action == 'run'   # TODO: abstract away to shutitconfig object
	# Logging
	shutit_global.shutit_global_object.logfile   = args.logfile # TODO: place in global
	shutit.build['exam']     = False # TODO: place in global

	shutit_global.shutit_global_object.loglevel = args.log # TODO: place in global
	if shutit_global.shutit_global_object.loglevel in ('', None): # TODO: place in global
		shutit_global.shutit_global_object.loglevel = 'INFO' # TODO: place in global
	shutit_global.shutit_global_object.setup_logging() # TODO: place in global

	# This mode is a bit special - it's the only one with different arguments
	# TODO: abstract away to separate function in global
	if shutit.action['skeleton']:
		delivery_method = args.delivery # TODO: abstract away to shutitconfig object
		accept_defaults = args.accept # TODO: abstract away to shutitconfig object
		# Looks through the arguments given for valid shutitfiles, and adds their names to _new_shutitfiles.
		_new_shutitfiles = None
		if args.shutitfiles: # TODO: abstract away to shutitconfig object
			cwd = os.getcwd()
			_new_shutitfiles       = []
			_delivery_methods_seen = set()
			for shutitfile in args.shutitfiles: # TODO: abstract away to shutitconfig object
				if shutitfile[0] != '/':
					shutitfile = cwd + '/' + shutitfile
				if os.path.isfile(shutitfile):
					candidate_shutitfile_fh = open(shutitfile,'r')
					candidate_shutitfile_contents = candidate_shutitfile_fh.read()
					candidate_shutitfile_fh.close()
					try:
						shutitfile_representation, ok = shutit_skeleton.process_shutitfile(shutit, candidate_shutitfile_contents)
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
									shutitfile_representation, ok = shutit_skeleton.process_shutitfile(shutit, candidate_shutitfile_contents)
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
				if len(_delivery_methods_seen) == 0 and delivery_method is None:
					delivery_method = 'bash'
				elif len(_delivery_methods_seen) == 0:
					pass
				elif len(_delivery_methods_seen) == 1 and delivery_method is None:
					delivery_method = _delivery_methods_seen.pop()
				elif len(_delivery_methods_seen) == 1:
					shutitfile_delivery_method = _delivery_methods_seen.pop()
					if delivery_method != shutitfile_delivery_method:
						print('Conflicting delivery methods passed in vs. from shutitfile.\nPassed-in: ' + delivery_method + '\nShutitfile: ' + shutitfile_delivery_method)
						handle_exit(shutit=shutit, exit_code=1)
				else:
					print('Too many delivery methods seen in shutitfiles: ' + str(_new_shutitfiles))
					print('Delivery methods: ' + str(_delivery_methods_seen))
					print('Delivery method passed in: ' + delivery_method)
					handle_exit(shutit=shutit, exit_code=1)
			else:
				print('ShutItFiles: ' + str(_new_shutitfiles) + ' appear to not exist.')
				handle_exit(shutit=shutit, exit_code=1)
		module_directory = args.name # TODO: abstract away to shutitconfig object
		if module_directory == '':
			default_dir = shutit.host['calling_path'] + '/shutit_' + random_word()
			if accept_defaults:
				module_directory = default_dir
			else:
				module_directory = shutit.util_raw_input(prompt='# Input a name for this module.\n# Default: ' + default_dir + '\n', default=default_dir)
		if module_directory[0] != '/':
			module_directory = shutit.host['calling_path'] + '/' + module_directory
		module_name = module_directory.split('/')[-1].replace('-','_')
		if args.domain == '': # TODO: abstract away to shutitconfig object
			default_domain_name = os.getcwd().split('/')[-1] + '.' + module_name
			#if accept_defaults:
			domain = default_domain_name
			#else:
			#	domain = shutit.util_raw_input(prompt='# Input a unique domain, eg (com.yourcorp).\n# Default: ' + default_domain_name + '\n', default=default_domain_name)
		else:
			domain = args.domain # TODO: abstract away to shutitconfig object
		# Figure out defaults.
		# If no pattern supplied, then assume it's the same as delivery.
		default_pattern = 'bash'
		if args.pattern == '': # TODO: abstract away to shutitconfig object
			if accept_defaults or _new_shutitfiles:
				if _new_shutitfiles:
					default_pattern = delivery_method
				pattern = default_pattern
			else:
				pattern = shutit.util_raw_input(prompt='''# Input a ShutIt pattern.
Default: ''' + default_pattern + '''

bash:              a shell script
docker:            a docker image build
vagrant:           a vagrant setup
docker_tutorial:   a docker-based tutorial
shutitfile:        a shutitfile-based project (can be docker, bash, vagrant)

''',default=default_pattern)
		else:
			pattern = args.pattern # TODO: abstract away to shutitconfig object

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
					delivery = shutit.util_raw_input(prompt=textwrap.dedent('''
						# Input a delivery method from: bash, docker, vagrant.
						# Default: ' + default_delivery + '

						docker:      build within a docker image
						bash:        run commands directly within bash
						vagrant:     build an n-node vagrant cluster

						'''), default=default_delivery)
		else:
			delivery = delivery_method

		shutit.cfg['skeleton'] = {
			'path':                   module_directory,
			'module_name':            module_name,
			'base_image':             args.base_image, # TODO: abstract away to shutitconfig object
			'domain':                 domain,
			'domain_hash':            str(get_hash(domain)),
			'depends':                args.depends, # TODO: abstract away to shutitconfig object
			'script':                 args.script, # TODO: abstract away to shutitconfig object
			'shutitfiles':            _new_shutitfiles,
			'output_dir':             args.output_dir, # TODO: abstract away to shutitconfig object
			'delivery':               delivery,
			'pattern':                pattern,
			'vagrant_num_machines':   args.vagrant_num_machines, # TODO: abstract away to shutitconfig object
			'vagrant_ssh_access':     args.vagrant_ssh_access, # TODO: abstract away to shutitconfig object
			'vagrant_machine_prefix': args.vagrant_machine_prefix, # TODO: abstract away to shutitconfig object
			'vagrant_docker':         args.vagrant_docker # TODO: abstract away to shutitconfig object
		}
		# set defaults to allow config to work
		shutit.build['extra_configs']    = []
		shutit.build['config_overrides'] = []
		shutit.build['conn_module']      = None
		shutit.build['delivery']         = 'bash'
		shutit.target['docker_image']    = ''
	# TODO: abstract away to separate function in global
	elif shutit.action['run']:
		module_name      = random_id(chars=string.ascii_letters)
		module_dir       = "/tmp/shutit_built/" + module_name
		module_domain    = module_name + '.' + module_name
		argv_new = [sys.argv[0],'skeleton','--shutitfile'] + args.shutitfiles + ['--name', module_dir,'--domain',module_domain,'--pattern','bash'] # TODO: abstract away to shutitconfig object
		retdir = os.getcwd()
		subprocess.call(argv_new)
		os.chdir(module_dir)
		subprocess.call('./run.sh')
		os.chdir(retdir)
		sys.exit(0)
	# TODO: process
	else:
		shutit_home = shutit.host['shutit_path'] = os.path.expanduser('~/.shutit')
		# We're not creating a skeleton, so make sure we have the infrastructure
		# in place for a user-level storage area
		if not os.path.isdir(shutit_home):
			mkpath(shutit_home, 0o700)
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
			shutit.repository['push']       = args.push  # TODO: abstract away to shutitconfig object
			shutit.repository['export']     = args.export # TODO: abstract away to shutitconfig object
			shutit.repository['save']       = args.save # TODO: abstract away to shutitconfig object
			shutit.build['distro_override'] = args.distro # TODO: abstract away to shutitconfig object
			shutit.build['mount_docker']    = args.mount_docker# TODO: abstract away to shutitconfig object
			shutit.build['walkthrough']     = args.walkthrough# TODO: abstract away to shutitconfig object
			shutit.build['training']        = args.training# TODO: abstract away to shutitconfig object
			shutit.build['exam']            = args.exam# TODO: abstract away to shutitconfig object
			shutit.build['choose_config']   = args.choose_config# TODO: abstract away to shutitconfig object
			if shutit.build['exam'] and not shutit.build['training']:
				# We want it to be quiet
				#print('--exam implies --training, setting --training on!')
				print('Exam starting up')
				shutit.build['training'] = True
			if (shutit.build['exam'] or shutit.build['training']) and not shutit.build['walkthrough']:
				if not shutit.build['exam']:
					print('--training or --exam implies --walkthrough, setting --walkthrough on!')
				shutit.build['walkthrough'] = True
			if isinstance(args.video, list) and args.video[0] >= 0:# TODO: abstract away to shutitconfig object
				shutit.build['walkthrough']      = True
				shutit.build['walkthrough_wait'] = float(args.video[0])# TODO: abstract away to shutitconfig object
				shutit.build['video']            = True
				if shutit.build['training']:
					print('--video and --training mode incompatible')
					handle_exit(shutit=shutit, exit_code=1)
				if shutit.build['exam']:
					print('--video and --exam mode incompatible')
					handle_exit(shutit=shutit, exit_code=1)
			# Create a test session object if needed.
			if shutit.build['exam']:
				shutit.build['exam_object'] = shutit_exam.ShutItExamSession(shutit)
		elif shutit.action['list_configs']:
			shutit.list_configs['cfghistory'] = args.history# TODO: abstract away to shutitconfig object
		elif shutit.action['list_modules']:
			shutit.list_modules['long'] = args.long# TODO: abstract away to shutitconfig object
			shutit.list_modules['sort'] = args.sort# TODO: abstract away to shutitconfig object

		# What are we building on? Convert arg to conn_module we use.
		if args.delivery == 'docker' or args.delivery is None:# TODO: abstract away to shutitconfig object
			shutit.build['conn_module'] = 'shutit.tk.conn_docker'
			shutit.build['delivery']    = 'docker'
		elif args.delivery == 'ssh':# TODO: abstract away to shutitconfig object
			shutit.build['conn_module'] = 'shutit.tk.conn_ssh'
			shutit.build['delivery']    = 'ssh'
		elif args.delivery == 'bash' or args.delivery == 'dockerfile':# TODO: abstract away to shutitconfig object
			shutit.build['conn_module'] = 'shutit.tk.conn_bash'
			shutit.build['delivery']    = args.delivery# TODO: abstract away to shutitconfig object
		# If the image_tag has been set then ride roughshod over the ignoreimage value if not supplied
		if args.image_tag != '' and args.ignoreimage is None:# TODO: abstract away to shutitconfig object
			args.ignoreimage = True# TODO: abstract away to shutitconfig object
		# If ignoreimage is still not set, then default it to False
		if args.ignoreimage is None:# TODO: abstract away to shutitconfig object
			args.ignoreimage = False# TODO: abstract away to shutitconfig object

		# Get these early for this part of the build.
		# These should never be config arguments, since they are needed before config is passed in.
		if args.shutit_module_path is not None:# TODO: abstract away to shutitconfig object
			module_paths = args.shutit_module_path.split(':')# TODO: abstract away to shutitconfig object
			if '.' not in module_paths:
				module_paths.append('.')
			args.set.append(('host', 'shutit_module_path', ':'.join(module_paths)))# TODO: abstract away to shutitconfig object
		shutit_global.shutit_global_object.interactive      = int(args.interactive)# TODO: abstract away to shutitconfig object
		shutit.build['extra_configs']    = args.config# TODO: abstract away to shutitconfig object
		shutit.build['config_overrides'] = args.set# TODO: abstract away to shutitconfig object
		shutit.build['ignorestop']       = args.ignorestop# TODO: abstract away to shutitconfig object
		shutit.build['ignoreimage']      = args.ignoreimage# TODO: abstract away to shutitconfig object
		shutit.build['imageerrorok']     = args.imageerrorok# TODO: abstract away to shutitconfig object
		shutit.build['tag_modules']      = args.tag_modules# TODO: abstract away to shutitconfig object
		shutit.build['deps_only']        = args.deps_only# TODO: abstract away to shutitconfig object
		shutit.build['always_echo']      = args.echo# TODO: abstract away to shutitconfig object
		shutit.target['docker_image']    = args.image_tag# TODO: abstract away to shutitconfig object

		if shutit.build['delivery'] in ('bash','ssh'):
			if shutit.target['docker_image'] != '': # pragma: no cover
				print('delivery method specified (' + shutit.build['delivery'] + ') and image_tag argument make no sense')
				handle_exit(shutit=shutit, exit_code=1)
		# Finished parsing args.
		# Sort out config path
		if shutit.action['list_configs'] or shutit.action['list_modules'] or shutit.action['list_deps'] or shutit_global.shutit_global_object.loglevel == logging.DEBUG:
			shutit.build['log_config_path'] = shutit_global.shutit_global_object.shutit_state_dir + '/config'
			if not os.path.exists(shutit.build['log_config_path']):
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
		if args.trace:# TODO: abstract away to shutitconfig object into global
			def tracefunc(frame, event, arg, indent=[0]):
				indent = indent # pylint
				arg = arg # pylint
				if event == 'call':
					shutit.log('-> call function: ' + frame.f_code.co_name + ' ' + str(frame.f_code.co_varnames),level=logging.DEBUG)
				elif event == 'return':
					shutit.log('<- exit function: ' + frame.f_code.co_name,level=logging.DEBUG)
				return tracefunc
			sys.settrace(tracefunc)


def load_configs(shutit):
	"""Responsible for loading config files into ShutIt.
	Recurses down from configured shutit module paths.
	"""
	# Get root default config.
	configs = [('defaults', StringIO(_default_cnf)), os.path.expanduser('~/.shutit/config'), os.path.join(shutit.host['shutit_path'], 'config'), 'configs/build.cnf']
	# Add the shutit global host- and user-specific config file.
	# Add the local build.cnf
	# Get passed-in config(s)
	for config_file_name in shutit.build['extra_configs']:
		run_config_file = os.path.expanduser(config_file_name)
		if not os.path.isfile(run_config_file):
			print('Did not recognise ' + run_config_file + ' as a file - do you need to touch ' + run_config_file + '?')
			handle_exit(shutit=shutit, exit_code=0)
		configs.append(run_config_file)
	# Image to use to start off. The script should be idempotent, so running it
	# on an already built image should be ok, and is advised to reduce diff space required.
	if shutit.action['list_configs'] or shutit_global.shutit_global_object.loglevel <= logging.DEBUG:
		msg = ''
		for c in configs:
			if isinstance(c, tuple):
				c = c[0]
			msg = msg + '    \n' + c
			shutit.log('    ' + c,level=logging.DEBUG)

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

	shutit.cfg_parser = get_configs(shutit, configs)
	get_base_config(shutit, shutit.cfg_parser)



def list_modules(shutit, long_output=None,sort_order=None):
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
		d = {}
		for m in shutit.shutit_modules:
			d.update({m.module_id:m.run_order})
		# sort dict by run_order; see http://stackoverflow.com/questions/613183/sort-a-python-dictionary-by-value
		b = sorted(d.items(), key=operator.itemgetter(1))
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
						compatible = shutit.determine_compatibility(m.module_id) == 0
						cfg[m.module_id]['shutit.core.module.build'] = False
					if long_output:
						table_list.append([str(count),m.module_id,m.description,str(m.run_order),str(cfg[m.module_id]['shutit.core.module.build']),str(compatible)])
						#table_list.append([str(count),m.module_id,m.description,str(m.run_order),str(cfg[m.module_id]['shutit.core.module.build'])])
					else:
						table_list.append([m.module_id,m.description,str(cfg[m.module_id]['shutit.core.module.build']),str(compatible)])
	elif sort_order == 'id':
		l = []
		for m in shutit.shutit_modules:
			l.append(m.module_id)
		l.sort()
		for k in l:
			for m in shutit.shutit_modules:
				if m.module_id == k:
					count = 1
					compatible = True
					if not cfg[m.module_id]['shutit.core.module.build']:
						cfg[m.module_id]['shutit.core.module.build'] = True
						compatible = shutit.determine_compatibility(m.module_id) == 0
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


# TODO: does this still work?
def print_config(shutit, cfg, hide_password=True, history=False, module_id=None):
	"""Returns a string representing the config of this ShutIt run.
	"""
	cp = shutit.config_parser
	s = ''
	keys1 = list(cfg.keys())
	if keys1:
		keys1.sort()
	for k in keys1:
		if module_id is not None and k != module_id:
			continue
		if isinstance(k, str) and isinstance(cfg[k], dict):
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


def load_all_from_path(shutit, path):
	"""Dynamically imports files within the same directory (in the end, the path).
	"""
	#111: handle expanded paths
	path = os.path.abspath(path)
	#http://stackoverflow.com/questions/301134/dynamic-module-import-in-python
	if os.path.abspath(path) == shutit.shutit_main_dir:
		return
	if not os.path.exists(path):
		return
	if os.path.exists(path + '/STOPBUILD') and not shutit.build['ignorestop']:
		shutit.log('Ignoring directory: ' + path + ' as it has a STOPBUILD file in it. Pass --ignorestop to shutit run to override.',level=logging.DEBUG)
		return
	for sub in glob.glob(os.path.join(path, '*')):
		subpath = os.path.join(path, sub)
		if os.path.isfile(subpath):
			load_mod_from_file(shutit, subpath)
		elif os.path.isdir(subpath):
			load_all_from_path(shutit, subpath)


def load_mod_from_file(shutit, fpath):
	"""Loads modules from a .py file into ShutIt if there are no modules from
	this file already.
	We expect to have a callable 'module/0' which returns one or more module
	objects.
	If this doesn't exist we assume that the .py file works in the old style
	(automatically inserting the module into shutit_global) or it's not a shutit
	module.
	"""
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
		if not isinstance(modules, list):
			modules = [modules]
		for module in modules:
			setattr(module, '__module_file', fpath)
			ShutItModule.register(module.__class__)
			target.add(module)
			shutit.build['source'][fpath] = open(fpath).read()



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



# TODO: move to shutit_class.py
def config_collection(shutit):
	"""Collect core config from config files for all seen modules.
	"""
	shutit.log('In config_collection',level=logging.DEBUG)
	cfg = shutit.cfg
	for module_id in shutit.module_ids():
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
								val = val # pylint
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




# TODO: move to shutit_class.py
def config_collection_for_built(shutit, throw_error=True,silent=False):
	"""Collect configuration for modules that are being built.
	When this is called we should know what's being built (ie after
	dependency resolution).
	"""
	shutit.log('In config_collection_for_built',level=logging.DEBUG)
	cfg = shutit.cfg
	for module_id in shutit.module_ids():
		# Get the config even if installed or building (may be needed in other hooks, eg test).
		if (shutit.is_to_be_built_or_is_installed(shutit.shutit_map[module_id]) and
			not shutit.shutit_map[module_id].get_config(shutit)):
			shutit.fail(module_id + ' failed on get_config') # pragma: no cover
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
								val = val # pylint
								# skip overrides
								if mod == module_id and opt == option:
									override = True
							if override:
								continue
							is_bool = isinstance(cfg[module_id][option], bool)
							if is_bool:
								value = config_parser.getboolean(section,option)
							else:
								value = config_parser.get(section,option)
							if option == 'shutit.core.module.allowed_images':
								value = json.loads(value)
							shutit.get_config(module_id, option, value, forcedefault=True)
	# Check the allowed_images against the base_image
	passed = True
	for module_id in shutit.module_ids():
		if (cfg[module_id]['shutit.core.module.build'] and
		   (cfg[module_id]['shutit.core.module.allowed_images'] and
		    shutit.target['docker_image'] not in cfg[module_id]['shutit.core.module.allowed_images'])):
			if not shutit.allowed_image(module_id):
				passed = False
				if not silent:
					print('\n\nWARNING!\n\nAllowed images for ' + module_id + ' are: ' + str(cfg[module_id]['shutit.core.module.allowed_images']) + ' but the configured image is: ' + shutit.target['docker_image'] + '\n\nIs your shutit_module_path set correctly?\n\nIf you want to ignore this, pass in the --ignoreimage flag to shutit.\n\n')
	if not passed:
		if not throw_error:
			return False
		if shutit.build['imageerrorok']:
			# useful for test scripts
			print('Exiting on allowed images error, with return status 0')
			handle_exit(shutit=shutit, exit_code=1)
		else:
			raise ShutItFailException('Allowed images checking failed') # pragma: no cover
	return True


# TODO: move to shutit_class.py
def handle_exit(shutit=None, exit_code=0,loglevel=logging.DEBUG,msg=None):
	if not msg:
		msg = '\nExiting with error code: ' + str(exit_code)
	if shutit is None:
		if exit_code != 0:
			#shutit_global.shutit_global_object.print_stack_trace()
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
