#!/usr/bin/env pythen

"""ShutIt utility functions.
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
import argparse
import os
import stat
from ConfigParser import RawConfigParser
import time
import re
import imp
import shutit_global
from shutit_module import ShutItModule
import pexpect
import socket
import textwrap
import json
import binascii
import base64
import subprocess
import getpass
import StringIO
import glob
import hashlib
import urlparse
import urllib2
import shutil
from shutit_module import ShutItFailException
import operator
import threading
import string
import random

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
# Folder with files you want to copy from in your build.
# Often a good idea to have a central folder for this per host
# in your /path/to/shutit/configs/`hostname`_`username`.cnf
# If set to blank, then defaults to /path/to/shutit/artifacts (preferred)
# If set to "artifacts", then defaults to the artifacts folder in the cwd.
artifacts_dir:
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
name:my_module
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
repo_name:
tag_name:latest

# Root setup script
# Each module should set these in a config
[shutit.tk.setup]
shutit.core.module.build:yes
# Modules may rely on the below settings, only change for debugging.
do_update:yes

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
build_log:yes
# How to connect to target
conn_module:shutit.tk.conn_docker
# Run any docker container in privileged mode
privileged:no
# lxc-conf arg, eg
#lxc_conf:lxc.aa_profile=unconfined
lxc_conf:
# Base image can be over-ridden by --image_tag defaults to this.
base_image:ubuntu:14.04
# Whether to perform tests.
dotest:yes
# --net argument to docker, eg "bridge", "none", "container:<name|id>" or "host". Empty means use default (bridge).
net:
'''

class LayerConfigParser(RawConfigParser):

	def __init__(self):
		RawConfigParser.__init__(self)
		self.layers = []

	def read(self, filenames):
		if type(filenames) is not list:
			filenames = [filenames]
		for filename in filenames:
			cp = RawConfigParser()
			cp.read(filename)
			self.layers.append((cp, filename, None))
		return RawConfigParser.read(self, filenames)

	def readfp(self, fp, filename=None):
		cp = RawConfigParser()
		fp.seek(0)
		cp.readfp(fp, filename)
		self.layers.append((cp, filename, fp))
		fp.seek(0)
		ret = RawConfigParser.readfp(self, fp, filename)
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
		raise NotImplementedError('Layer config parsers aren\'t directly mutable')
	def remove_option(self, *args, **kwargs):
		raise NotImplementedError('Layer config parsers aren\'t directly mutable')
	def set(self, *args, **kwargs):
		raise NotImplementedError('Layer config parsers aren\'t directly mutable')

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


def colour(code, msg):
	"""Colourize the given string for a terminal.
	"""
	return '\033[%sm%s\033[0m' % (code, msg)


def get_configs(shutit, configs):
	"""Reads config files in, checking their security first
	(in case passwords/sensitive info is in them).
	"""
	cfg = shutit.cfg
	cp       = LayerConfigParser()
	fail_str = ''
	files    = []
	for config_file in configs:
		if type(config_file) is tuple:
			continue
		if not is_file_secure(config_file):
			fail_str = fail_str + '\nchmod 0600 ' + config_file
			files.append(config_file)
	if fail_str != '':
		if cfg['build']['interactive'] > 0:
			fail_str = 'Files are not secure, mode should be 0600. Running the following commands to correct:\n' + fail_str + '\n'
			# Actually show this to the user before failing...
			shutit.log(fail_str, force_stdout=True)
			shutit.log('\n\nDo you want me to run this for you? (input y/n)\n', force_stdout=True)
		if cfg['build']['interactive'] == 0 or util_raw_input(shutit=shutit,default='y') == 'y':
			for f in files:
				shutit.log('Correcting insecure file permissions on: ' + f, force_stdout=True)
				os.chmod(f,0600)
			# recurse
			return get_configs(shutit, configs)
		shutit.fail(fail_str)
	for config in configs:
		if type(config) is tuple:
			cp.readfp(config[1], filename=config[0])
		else:
			cp.read(config)
	# Treat allowed_images as a special, additive case
	cfg['build']['shutit.core.module.allowed_images'] = cp.get_config_set('build', 'shutit.core.module.allowed_images')
	return cp

def issue_warning(msg, wait):
	"""Issues a warning to stderr.
	"""
	print >> sys.stderr, msg
	time.sleep(wait)


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
	word_file = find_asset('words')
	words = open(word_file).read().splitlines()
	word = ''
	while len(word) != 6 or word.find("'") > -1:
		word = words[int(random.random() * (len(words) - 1))]
	return word.lower()

def find_asset(filename):
	dirs = ['/usr/share/dict',
	        sys.prefix,
	        os.path.join(sys.prefix,'local'),
	        shutit_global.shutit_main_dir,
	        os.path.join(shutit_global.shutit_main_dir,'../../..'),
	        shutit_global.shutit.cfg['host']['shutit_path'],
	        '/usr/local']
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
def get_base_config(cfg, cfg_parser):
	"""Responsible for getting core configuration from config files.
	"""
	cfg['config_parser'] = cp = cfg_parser
	# BEGIN Read from config files
	# build - details relating to the build
	cfg['build']['privileged']                 = cp.getboolean('build', 'privileged')
	cfg['build']['lxc_conf']                   = cp.get('build', 'lxc_conf')
	cfg['build']['build_log']                  = cp.getboolean('build', 'build_log')
	cfg['build']['base_image']                 = cp.get('build', 'base_image')
	cfg['build']['dotest']                     = cp.get('build', 'dotest')
	cfg['build']['net']                        = cp.get('build', 'net')
	cfg['build']['completed']                  = False
	cfg['build']['step_through']               = False
	cfg['build']['ctrlc_stop']                 = False
	cfg['build']['check_exit']                 = True
	# Width of terminal to set up on login and assume for other cases.
	cfg['build']['stty_cols']                  = 320
	# Take a command-line arg if given, else default.
	if cfg['build']['conn_module'] == None:
		cfg['build']['conn_module']            = cp.get('build', 'conn_module')
	# Track logins in a stack and details in logins.
	cfg['build']['login_stack']                = []
	cfg['build']['logins']                     = {}
	# Whether to accept default configs
	cfg['build']['accept_defaults']            = None
	# See shutit_global.check_environment
	cfg['build']['current_environment_id']     = None
	# target - the target of the build, ie the container
	cfg['target']['hostname']                  = cp.get('target', 'hostname')
	cfg['target']['locale']                    = cp.get('target', 'locale')
	cfg['target']['ports']                     = cp.get('target', 'ports')
	cfg['target']['volumes']                   = cp.get('target', 'volumes')
	cfg['target']['volumes_from']              = cp.get('target', 'volumes_from')
	cfg['target']['name']                      = cp.get('target', 'name')
	cfg['target']['rm']                        = cp.getboolean('target', 'rm')
	# host - the host on which the shutit script is run
	cfg['host']['add_shutit_to_path']          = cp.getboolean('host', 'add_shutit_to_path')
	cfg['host']['artifacts_dir']               = cp.get('host', 'artifacts_dir')
	cfg['host']['docker_executable']           = cp.get('host', 'docker_executable')
	cfg['host']['dns']                         = cp.get('host', 'dns')
	cfg['host']['password']                    = cp.get('host', 'password')
	cfg['host']['logfile']                     = cp.get('host', 'logfile')
	cfg['host']['shutit_module_path']          = cp.get('host', 'shutit_module_path').split(':')
	# repository - information relating to repository/registry
	cfg['repository']['name']                  = cp.get('repository', 'name')
	cfg['repository']['server']                = cp.get('repository', 'server')
	cfg['repository']['push']                  = cp.getboolean('repository', 'push')
	cfg['repository']['tag']                   = cp.getboolean('repository', 'tag')
	cfg['repository']['export']                = cp.getboolean('repository', 'export')
	cfg['repository']['save']                  = cp.getboolean('repository', 'save')
	cfg['repository']['suffix_date']           = cp.getboolean('repository', 'suffix_date')
	cfg['repository']['suffix_format']         = cp.get('repository', 'suffix_format')
	cfg['repository']['user']                  = cp.get('repository', 'user')
	cfg['repository']['password']              = cp.get('repository', 'password')
	cfg['repository']['email']                 = cp.get('repository', 'email')
	cfg['repository']['tag_name']              = cp.get('repository', 'tag_name')
	# END Read from config files

	# BEGIN Standard expects
	# It's important that these have '.*' in them at the start, so that the matched data is reliably 'after' in the
	# child object. Use these where possible to make things more consistent.
	# Attempt to capture any starting prompt (when starting) with this regexp.
	cfg['expect_prompts']['base_prompt']       = '\r\n.*[@#$] '
	# END Standard expects

	# BEGIN tidy configs up
	if cfg['host']['artifacts_dir'] == 'artifacts':
		cfg['host']['artifacts_dir'] = os.path.join(shutit_global.cwd, 'artifacts')
	elif cfg['host']['artifacts_dir'] == '':
		cfg['host']['artifacts_dir'] = os.path.join(shutit_global.shutit_main_dir, 'artifacts')
	if cfg['host']['logfile'] == '':
		if not os.access(cfg['build']['shutit_state_dir_base'],os.F_OK):
			os.mkdir(cfg['build']['shutit_state_dir_base'])
		if not os.access(cfg['build']['shutit_state_dir'],os.F_OK):
			os.mkdir(cfg['build']['shutit_state_dir'])
		os.chmod(cfg['build']['shutit_state_dir_base'],0777)
		os.chmod(cfg['build']['shutit_state_dir'],0777)
		logfile = os.path.join(cfg['build']['shutit_state_dir'], 'shutit_build.log')
	else:
		logfile = cfg['host']['logfile'] + '_' + cfg['build']['build_id']
	cfg['host']['logfile'] = logfile
	if cfg['build']['build_log']:
		cfg['build']['build_log_file'] = open(logfile, 'a')
		# Lock it down to the running user.
		os.chmod(logfile,0600)
	# delivery method bash and image_tag make no sense
	if cfg['build']['delivery'] in ('bash','ssh'):
		if cfg['target']['docker_image'] != '':
			print('delivery method specified (' + cfg['build']['delivery'] + ') and image_tag argument make no sense')
			sys.exit(1)
	if cfg['target']['docker_image'] == '':
		cfg['target']['docker_image'] = cfg['build']['base_image']
	# END tidy configs up

	# BEGIN warnings
	# Warn if something appears not to have been overridden
	warn = ''
	# FAILS begins
	# rm is incompatible with repository actions
	if cfg['target']['rm'] and (cfg['repository']['tag'] or cfg['repository']['push'] or cfg['repository']['save'] or cfg['repository']['export']):
		print("Can't have [target]/rm and [repository]/(push/save/export) set to true")
		sys.exit(1)
	if warn != '' and cfg['build']['debug']:
		issue_warning('Showing config as read in. This can also be done by calling with list_configs:',2)
		shutit_global.shutit.log(print_config(cfg), force_stdout=True, code='32')
		time.sleep(1)
	if cfg['target']['hostname'] != '' and cfg['build']['net'] != '' and cfg['build']['net'] != 'bridge':
		print('\n\ntarget/hostname or build/net configs must be blank\n\n')
		sys.exit(1)
	# FAILS ends

# Returns the config dict
def parse_args(shutit):
	"""Responsible for parsing arguments.

	TODO: precendence of configs documented

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
	cfg = shutit.cfg
	cfg['host']['real_user_id'] = pexpect.run('id -u ' + cfg['host']['real_user']).strip()

	# These are in order of their creation
	actions = ['build', 'list_configs', 'list_modules', 'list_deps', 'serve', 'skeleton']

	# COMPAT 2014-05-15 - build is the default if there is no action specified
	# and we've not asked for help and we've called via 'shutit_main.py'
	if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] not in actions
			and '-h' not in sys.argv and '--help' not in sys.argv
			and os.path.basename(sys.argv[0]) == 'shutit_main.py'):
		sys.argv.insert(1, 'build')

	# Pexpect documentation says systems have issues with pauses < 0.05
	def check_pause(value):
		ivalue = float(value)
		if ivalue < 0.05:
			raise argparse.ArgumentTypeError(
				"%s is an invalid pause (must be >= 0.05)" % value)
		return ivalue

	parser = argparse.ArgumentParser(description='ShutIt - a tool for managing complex Docker deployments.\n\nTo view help for a specific subcommand, type ./shutit <subcommand> -h',prog="ShutIt")
	parser.add_argument('--version', action='version', version='%(prog)s 0.7')
	subparsers = parser.add_subparsers(dest='action', help='''Action to perform - build=deploy to target, serve=run a shutit web server, skeleton=construct a skeleton module, list_configs=show configuration as read in, list_modules=show modules available, list_deps=show dep graph ready for graphviz. Defaults to 'build'.''')

	sub_parsers = dict()
	for action in actions:
		sub_parsers[action] = subparsers.add_parser(action)

	sub_parsers['skeleton'].add_argument('--module_directory', help='Absolute path to new directory for module',default='')
	sub_parsers['skeleton'].add_argument('--module_name', help='Name for your module. Single word and lower case, eg: mymysql',default='')
	sub_parsers['skeleton'].add_argument('--domain', help='Arbitrary but unique domain for namespacing your module, eg com.mycorp',default='')
	sub_parsers['skeleton'].add_argument('--depends', help='Module id to depend on, default shutit.tk.setup (optional)', default='shutit.tk.setup')
	sub_parsers['skeleton'].add_argument('--base_image', help='FROM image, default ubuntu:14.04 (optional)', default='ubuntu:14.04')
	sub_parsers['skeleton'].add_argument('--script', help='Pre-existing shell script to integrate into module (optional)', nargs='?', default=None)
	sub_parsers['skeleton'].add_argument('--output_dir', help='Just output the created directory', default=False, const=True, action='store_const')
	sub_parsers['skeleton'].add_argument('--dockerfile', default=None)
	sub_parsers['skeleton'].add_argument('--delivery', help='Delivery method, aka target. "docker" container (default), configured "ssh" connection, "bash" session', default=None, choices=('docker','dockerfile','ssh','bash'))

	sub_parsers['build'].add_argument('--export', help='Perform docker export to a tar file', const=True, default=False, action='store_const')
	sub_parsers['build'].add_argument('--save', help='Perform docker save to a tar file', const=True, default=False, action='store_const')
	sub_parsers['build'].add_argument('--push', help='Push to a repo', const=True, default=False, action='store_const')
	sub_parsers['build'].add_argument('--distro', help='Specify the distro type', default='', choices=('ubuntu','debian','alpine','steamos','red hat','centos','fedora','shutit'))
	sub_parsers['build'].add_argument('--mount_docker', help='Mount the docker socket', default=False, action='store_const', const=True)
	sub_parsers['build'].add_argument('-w','--walkthrough', help='Run in walkthrough mode', default=False, action='store_const', const=True)

	sub_parsers['list_configs'].add_argument('--history', help='Show config with history', const=True, default=False, action='store_const')
	sub_parsers['list_modules'].add_argument('--long', help='Show extended module info, including ordering', const=True, default=False, action='store_const')
	sub_parsers['list_modules'].add_argument('--sort', help='Order the modules seen, default to module id', default='id', choices=('id','run_order'))

	for action in ['build', 'serve', 'list_configs', 'list_modules', 'list_deps']:
		sub_parsers[action].add_argument('--config', help='Config file for setup config. Must be with perms 0600. Multiple arguments allowed; config files considered in order.', default=[], action='append')
		sub_parsers[action].add_argument('-d','--delivery', help='Delivery method, aka target. "docker" container (default), configured "ssh" connection, "bash" session', default=None, choices=('docker','dockerfile','ssh','bash'))
		sub_parsers[action].add_argument('-s', '--set', help='Override a config item, e.g. "-s target rm no". Can be specified multiple times.', default=[], action='append', nargs=3, metavar=('SEC', 'KEY', 'VAL'))
		sub_parsers[action].add_argument('--image_tag', help='Build container from specified image - if there is a symbolic reference, please use that, eg localhost.localdomain:5000/myref', default='')
		sub_parsers[action].add_argument('--tag_modules', help='''Tag each module after it's successfully built regardless of the module config and based on the repository config.''', default=False, const=True, action='store_const')
		sub_parsers[action].add_argument('-m', '--shutit_module_path', default=None, help='List of shutit module paths, separated by colons. ShutIt registers modules by running all .py files in these directories.')
		sub_parsers[action].add_argument('--pause', help='Pause between commands to avoid race conditions.', default='0.05', type=check_pause)
		sub_parsers[action].add_argument('--debug', help='Show debug.', default=False, const=True, action='store_const')
		sub_parsers[action].add_argument('--trace', help='Trace function calls', const=True, default=False, action='store_const')
		sub_parsers[action].add_argument('--interactive', help='Level of interactive. 0 = none, 1 = honour pause points and config prompting, 2 = query user on each module, 3 = tutorial mode', default='1')
		sub_parsers[action].add_argument('--ignorestop', help='Ignore STOP files', const=True, default=False, action='store_const')
		sub_parsers[action].add_argument('--ignoreimage', help='Ignore disallowed images', const=True, default=False, action='store_const')
		sub_parsers[action].add_argument('--imageerrorok', help='Exit without error if allowed images fails (used for test scripts)', const=True, default=False, action='store_const')
		sub_parsers[action].add_argument('--deps_only', help='build deps only, tag with suffix "_deps"', const=True, default=False, action='store_const')

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
				env_args_list[-1] = env_args_list[-1] + ' '
			elif item == '\\\\':
				env_args_list[-1] = env_args_list[-1] + '\\'
			else:
				env_args_list[-1] = env_args_list[-1] + item
		args_list[1:1] = env_args_list
	args = parser.parse_args(args_list)

	# What are we asking shutit to do?
	cfg['action']['list_configs'] = args.action == 'list_configs'
	cfg['action']['list_modules'] = args.action == 'list_modules'
	cfg['action']['list_deps']    = args.action == 'list_deps'
	cfg['action']['serve']        = args.action == 'serve'
	cfg['action']['skeleton']     = args.action == 'skeleton'
	cfg['action']['build']        = args.action == 'build'

	# This mode is a bit special - it's the only one with different arguments
	if cfg['action']['skeleton']:
		if args.dockerfile and args.script:
			shutit.fail('Cannot have any two of script, -d/--dockerfile Dockerfile as arguments')
		if args.module_directory == '':
			default_dir = '/tmp/shutit_' + random_word()
			module_directory = util_raw_input(prompt='# Input a new directory name for this module.\n# Default: ' + default_dir + '\n', default=default_dir)
		else:
			module_directory = args.module_directory
		while True:
			if args.module_name == '':
				default_module_name = module_directory.split('/')[-1]
				module_name = util_raw_input(prompt='# Input module name.\n# Default: ' + default_module_name + '\n', default=default_module_name)
			else:
				module_name = args.module_name
			if not re.match('^[a-z][a-z0-9-_.]*',module_name):
				print 'You can only have [a-z][a-z0-9-_.]* in your module_name'
			else:
				break
		if args.domain == '':
			default_domain_name = os.getcwd().split('/')[-1] + '.' + module_name
			domain = util_raw_input(prompt='# Input a unique domain.\n# Default: ' + default_domain_name + '\n', default=default_domain_name)
		else:
			domain = args.domain
		if args.delivery == None:
			import platform
			# If on mac, default to bash, else docker
			if platform.system() == 'Darwin':
				default_delivery = 'bash'
			else:
				default_delivery = 'docker'
			delivery = ''
			allowed = ('docker','dockerfile','ssh','bash')
			while delivery not in allowed:
				delivery = util_raw_input(prompt='# Input a delivery method from: ' + str(allowed) + '.\n# Default: ' + default_delivery + '\n\ndocker = build within a docker image\ndockerfile = call "shutit build" from within a dockerfile\nssh = ssh to target and build\nbash = run commands directly within bash\n', default=default_delivery)
		else:
			delivery = args.delivery
		cfg['skeleton'] = {
			'path':        module_directory,
			'module_name': module_name,
			'base_image':  args.base_image,
			'domain':      domain,
			'domainhash':  str(get_hash(domain)),
			'depends':     args.depends,
			'script':      args.script,
			'dockerfile':  args.dockerfile,
			'output_dir':  args.output_dir,
			'delivery':    delivery
		}
		return

	shutit_home = cfg['shutit_home'] = os.path.expanduser('~/.shutit')
	# We're not creating a skeleton, so make sure we have the infrastructure
	# in place for a user-level storage area
	if not os.path.isdir(shutit_home):
		os.mkdir(shutit_home, 0o700)
	if not os.path.isfile(os.path.join(shutit_home, 'config')):
		f = os.open(
			os.path.join(shutit_home, 'config'),
			os.O_WRONLY | os.O_CREAT,
			0o600
		)
		os.write(f,_default_cnf)
		os.close(f)

	# Default this to False as it's not always set (mostly for --debug calls).
	cfg['list_configs']['cfghistory'] = False
	cfg['list_modules']['long']       = False
	cfg['list_modules']['sort']       = None
	# Persistence-related arguments.
	if cfg['action']['build']:
		cfg['repository']['push']   = args.push
		cfg['repository']['export'] = args.export
		cfg['repository']['save']   = args.save
		cfg['build']['distro_override'] = args.distro
		cfg['build']['mount_docker']    = args.mount_docker
		cfg['build']['walkthrough']     = args.walkthrough
	elif cfg['action']['list_configs']:
		cfg['list_configs']['cfghistory'] = args.history
	elif cfg['action']['list_modules']:
		cfg['list_modules']['long'] = args.long
		cfg['list_modules']['sort'] = args.sort

	# What are we building on? Convert arg to conn_module we use.
	if args.delivery == 'docker' or args.delivery == None:
		cfg['build']['conn_module'] = 'shutit.tk.conn_docker'
		cfg['build']['delivery']    = 'docker'
	elif args.delivery == 'ssh':
		cfg['build']['conn_module'] = 'shutit.tk.conn_ssh'
		cfg['build']['delivery']    = 'ssh'
	elif args.delivery == 'bash' or args.delivery == 'dockerfile':
		cfg['build']['conn_module'] = 'shutit.tk.conn_bash'
		cfg['build']['delivery']    = args.delivery

	# Get these early for this part of the build.
	# These should never be config arguments, since they are needed before config is passed in.
	if args.shutit_module_path is not None:
		module_paths = args.shutit_module_path.split(':')
		if '.' not in module_paths:
			if cfg['build']['debug']:
				shutit_global.shutit.log('Working directory path not included, adding...')
				time.sleep(1)
			module_paths.append('.')
		args.set.append(('host', 'shutit_module_path', ':'.join(module_paths)))
	cfg['build']['debug']            = args.debug
	cfg['build']['trace']            = args.trace
	cfg['build']['interactive']      = int(args.interactive)
	cfg['build']['command_pause']    = float(args.pause)
	cfg['build']['extra_configs']    = args.config
	cfg['build']['config_overrides'] = args.set
	cfg['build']['ignorestop']       = args.ignorestop
	cfg['build']['ignoreimage']      = args.ignoreimage
	cfg['build']['imageerrorok']     = args.imageerrorok
	cfg['build']['tag_modules']      = args.tag_modules
	cfg['build']['deps_only']        = args.deps_only
	cfg['target']['docker_image']    = args.image_tag
	# Finished parsing args.
	# Sort out config path
	if cfg['build']['interactive'] >= 3 or cfg['action']['list_configs'] or cfg['action']['list_modules'] or cfg['action']['list_deps'] or cfg['build']['debug']:
		cfg['build']['log_config_path'] = cfg['build']['shutit_state_dir'] + '/config/' + cfg['build']['build_id']
		if os.path.exists(cfg['build']['log_config_path']):
			print(cfg['build']['log_config_path'] + ' exists. Please move and re-run.')
			sys.exit(1)
		os.makedirs(cfg['build']['log_config_path'])
		os.chmod(cfg['build']['log_config_path'],0777)
	# Tutorial stuff.
	if cfg['build']['interactive'] >= 3:
		print textwrap.dedent("""\
			================================================================================
			SHUTIT - INTRODUCTION
			================================================================================
			ShutIt is a script that allows the building of static target environments.
			allowing a high degree of flexibility and easy conversion from other build
			methods (eg bash scripts)

			It is configured through command-line arguments (see --help) and .cnf files.
			================================================================================
			
			
			================================================================================
			CONFIG
			================================================================================
			The config is read in the following order:
			================================================================================
			~/.shutit/config
				- Host- and username-specific config for this host.
			/path/to/this/shutit/module/configs/build.cnf
				- Config specifying what should be built when this module is invoked.
			/your/path/to/<configname>.cnf
				- Passed-in config (via --config, see --help)
			command-line overrides, eg -s com.mycorp.mymodule.module name value
			================================================================================
			Config items look like this:
			
			[section]
			name:value
			
			or as command-line overrides:
			
			-s section name value
			================================================================================
			""" + colour('32', '\n[Hit return to continue]'))
		util_raw_input()
		print textwrap.dedent("""\
			================================================================================
			MODULES
			================================================================================
			Each module (which is a .py file) has a lifecycle, "module_id" and "run_order".

			The lifecycle (briefly) is as follows:

				foreach module:
					remove all modules config'd for removal
				foreach module:
					build
					tag
						stop all modules already started
						do repository work configured
						start all modules that were stopped
					start
				foreach module:
					test module
				stop all modules already started
				foreach module:
					finalize module

			and these stages are run from the module code, returning True or False as
			appropriate.

			The module_id is a string that uniquely identifies the module.

			The run_order is a float that defines the order in which the module should be
			run relative to other modules. This guarantees a deterministic ordering of
			the modules run.

			See shutit_module.py for more detailed documentation on these.

			================================================================================
			""" + colour('32', '\n[Hit return to continue]'))
		util_raw_input()
		print textwrap.dedent("""\
			================================================================================
			PAUSE POINTS
			================================================================================
			Pause points can be placed within the build, which is useful for debugging.

			This is used throughout this tutorial.

			When debugging, pause_points will output your keyboard input before you finish.

			This can help you build your build, as these commands can be pasted into the
			module you are developing easily.

			To escape a pause point when it happens, hit the "CTRL" and the "]"
			key simultaneously.
			================================================================================
			""" + colour('32', '\n[Hit return to continue]'))
		util_raw_input()
	# Set up trace as fast as possible.
	if cfg['build']['trace']:
		def tracefunc(frame, event, arg, indent=[0]):
			if event == "call":
				shutit.log("-> call function: " + frame.f_code.co_name + " " + str(frame.f_code.co_varnames),force_stdout=True)
			elif event == "return":
				shutit.log("<- exit function: " + frame.f_code.co_name,force_stdout=True)
			return tracefunc
		sys.settrace(tracefunc)


def load_configs(shutit):
	"""Responsible for loading config files into ShutIt.
	Recurses down from configured shutit module paths.
	"""
	cfg = shutit.cfg
	# Get root default config.
	configs = [('defaults', StringIO.StringIO(_default_cnf))]
	# Add the shutit global host- and user-specific config file.
	configs.append(os.path.join(shutit.shutit_main_dir,
		'configs/' + socket.gethostname() + '_' + cfg['host']['real_user'] + '.cnf'))
	configs.append(os.path.join(cfg['shutit_home'], 'config'))
	# Add the local build.cnf
	configs.append('configs/build.cnf')
	# Get passed-in config(s)
	for config_file_name in cfg['build']['extra_configs']:
		run_config_file = os.path.expanduser(config_file_name)
		if not os.path.isfile(run_config_file):
			print('Did not recognise ' + run_config_file +
			      ' as a file - do you need to touch ' + run_config_file + '?')
			sys.exit()
		configs.append(run_config_file)
	# Image to use to start off. The script should be idempotent, so running it
	# on an already built image should be ok, and is advised to reduce diff space required.
	if cfg['build']['interactive'] >= 3 or cfg['action']['list_configs'] or cfg['build']['debug']:
		msg = ''
		print textwrap.dedent("""\n""") + textwrap.dedent("""Looking at config files in the following order:""")
		for c in configs:
			if type(c) is tuple:
				c = c[0]
			msg = msg + '    \n' + c
			shutit.log('    ' + c)
		if cfg['build']['interactive'] >= 3:
			print textwrap.dedent("""\n""") + msg + textwrap.dedent(colour('32', '\n\n[Hit return to continue]'))
			util_raw_input(shutit=shutit)
		if cfg['action']['list_configs'] or cfg['build']['debug']:
			f = file(cfg['build']['log_config_path'] + '/config_file_order.txt','w')
			f.write(msg)
			f.close()

	# Interpret any config overrides, write to a file and add them to the
	# list of configs to be interpreted
	if cfg['build']['config_overrides']:
		# We don't need layers, this is a temporary configparser
		override_cp = RawConfigParser()
		for o_sec, o_key, o_val in cfg['build']['config_overrides']:
			if not override_cp.has_section(o_sec):
				override_cp.add_section(o_sec)
			override_cp.set(o_sec, o_key, o_val)
		override_fd = StringIO.StringIO()
		override_cp.write(override_fd)
		override_fd.seek(0)
		configs.append(('overrides', override_fd))

	cfg_parser = get_configs(shutit, configs)
	get_base_config(cfg, cfg_parser)
	if cfg['build']['debug']:
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
			shutit.log('No manhole package available, skipping import')
			pass


def load_shutit_modules(shutit):
	"""Responsible for loading the shutit modules based on the configured module
	paths.
	"""
	cfg = shutit.cfg
	if cfg['build']['debug']:
		shutit.log('ShutIt module paths now: ')
		shutit.log(cfg['host']['shutit_module_path'])
		time.sleep(1)
	for shutit_module_path in cfg['host']['shutit_module_path']:
		load_all_from_path(shutit, shutit_module_path)


def list_modules(shutit):
	"""Display a list of loaded modules.

	Config items:
		- ['list_modules']['long']
		  If set, also print each module's run order value

		- ['list_modules']['sort']
		  Select the column by which the list is ordered:
			- id: sort the list by module id
			- run_order: sort the list by module run order

	The output is also saved to ['build']['log_config_path']/module_order.txt

	Dependencies: texttable, operator
	"""
	cfg = shutit.cfg
	# list of module ids and other details
	# will also contain column headers
	table_list = []
	if cfg['list_modules']['long']:
		# --long table: sort modules by run order
		table_list.append(["Order","Module ID","Description","Run Order"])
	else:
		# "short" table ==> sort module by module_id
		table_list.append(["Module ID","Description"])

	if cfg['list_modules']['sort'] == 'run_order':
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
					count = count + 1
					if cfg['list_modules']['long']:
						table_list.append([str(count),m.module_id,m.description,str(m.run_order)])
					else:
						table_list.append([m.module_id,m.description])
	elif cfg['list_modules']['sort'] == 'id':
		a = []
		for m in shutit.shutit_modules:
			a.append(m.module_id)
		a.sort()
		count = 0
		for k in a:
			for m in shutit.shutit_modules:
				if m.module_id == k:
					count = count + 1
					if cfg['list_modules']['long']:
						table_list.append([str(count),m.module_id,m.description,str(m.run_order)])
					else:
						table_list.append([m.module_id,m.description])

	# format table for display
	import texttable
	table = texttable.Texttable()
	table.add_rows(table_list)
	msg = table.draw()
	print msg
	f = file(cfg['build']['log_config_path'] + '/module_order.txt','w')
	f.write(msg)
	f.close()


def print_config(cfg, hide_password=True, history=False):
	"""Returns a string representing the config of this ShutIt run.
	"""
	cp = cfg['config_parser']
	s = ''
	keys1 = cfg.keys()
	if keys1:
		keys1.sort()
	for k in keys1:
		if type(k) == str and type(cfg[k]) == dict:
			s += '\n[' + k + ']\n'
			keys2 = cfg[k].keys()
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
							i = i - 1
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
	shutit_global.pexpect_children.update({key:child})

def get_pexpect_child(key):
	"""Get a pexpect child in the global dictionary by key.
	"""
	return shutit_global.pexpect_children[key]

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
	if os.path.exists(path + '/STOPBUILD') and not cfg['build']['ignorestop']:
		shutit.log('Ignoring directory: ' + path + ' as it has a STOPBUILD file in it. Pass --ignorestop to shutit run to override.', force_stdout=True)
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
	cfg = shutit.cfg
	fpath = os.path.abspath(fpath)
	file_ext = os.path.splitext(os.path.split(fpath)[-1])[-1]
	if file_ext.lower() != '.py':
		return
	if re.match(shutit_global.cwd + '\/context\/.*',fpath):
		shutit.log('Ignoring file: "' + fpath + '" as this appears to be part of the context directory')
		return
	# Do we already have modules from this file? If so we know we can skip.
	# Note that this attribute will only be set for 'new style' module loading,
	# this should be ok because 'old style' loading checks for duplicate
	# existing modules.
	# TODO: this is quadratic complexity
	existingmodules = [
		m for m in shutit.shutit_modules
		if getattr(m, '__module_file', None) == fpath
	]
	if len(existingmodules) > 0:
		return
	# Looks like it's ok to load this file
	if cfg['build']['debug']:
		shutit.log('Loading source for: ' + fpath)

	# Add this directory to the python path iff not already there.
	directory = os.path.dirname(fpath)
	if directory not in sys.path:
		sys.path.append(os.path.dirname(fpath))
	mod_name = base64.b32encode(fpath).replace('=', '')
	pymod = imp.load_source(mod_name, fpath)

	# Got the python module, now time to pull the shutit module(s) out of it.
	targets = [
		('module', shutit.shutit_modules), ('conn_module', shutit.conn_modules)
	]
	cfg['build']['source'] = {}
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
			cfg['build']['source'][fpath] = open(fpath).read()


# Build report
def build_report(shutit, msg=''):
	"""Resposible for constructing a report to be output as part of the build.
	Retrurns report as a string.
	"""
	cfg = shutit.cfg
	s = ''
	s += '################################################################################\n'
	s += '# COMMAND HISTORY BEGIN ' + shutit_global.cfg['build']['build_id'] + '\n'
	s += get_commands(shutit)
	s += '# COMMAND HISTORY END ' + shutit_global.cfg['build']['build_id'] + '\n'
	s += '################################################################################\n'
	s += '################################################################################\n'
	s += '# BUILD REPORT FOR BUILD BEGIN ' + shutit_global.cfg['build']['build_id'] + '\n'
	s += '# ' + msg + '\n'
	if shutit_global.cfg['build']['report'] != '':
		s += shutit_global.cfg['build']['report'] + '\n'
	else:
		s += '# Nothing to report\n'

	if 'container_id' in cfg['target']:
		s += '# CONTAINER_ID: ' + cfg['target']['container_id'] + '\n'
	s += '# BUILD REPORT FOR BUILD END ' + shutit_global.cfg['build']['build_id'] + '\n'
	s += '###############################################################################\n'
	return s

def get_commands(shutit):
	"""Gets command that have been run and have not been redacted.
	"""
	s = ''
	for c in shutit.shutit_command_history:
		if type(c) == str:
			#Ignore commands with leading spaces
			if c[0] != ' ':
				s += c + '\n'
	return s


def get_hash(string):
	"""Helper function to get preceding integer
	eg com.openbet == 1003189494
	>>> import binascii
	>>> abs(binascii.crc32('shutit.tk'))
	782914092

	Recommended means of determining run order integer part.
	"""
	return abs(binascii.crc32(string))

def create_skeleton(shutit):
	"""Helper function to create a standard module directory ready to run
	and tinker with.
	"""
	cfg = shutit.cfg
	shutit_dir = sys.path[0]

	# Set up local directories
	skel_path        = cfg['skeleton']['path']
	skel_module_name = cfg['skeleton']['module_name']
	skel_domain      = cfg['skeleton']['domain']
	skel_domain_hash = cfg['skeleton']['domainhash']
	skel_depends     = cfg['skeleton']['depends']
	skel_base_image  = cfg['skeleton']['base_image']
	skel_script      = cfg['skeleton']['script']
	skel_dockerfile  = cfg['skeleton']['dockerfile']
	skel_output_dir  = cfg['skeleton']['output_dir']
	skel_delivery    = cfg['skeleton']['delivery']
	# Set up dockerfile cfg
	cfg['dockerfile']['base_image'] = skel_base_image
	cfg['dockerfile']['cmd']        = """/bin/sh -c 'sleep infinity'"""
	cfg['dockerfile']['user']       = ''
	cfg['dockerfile']['maintainer'] = ''
	cfg['dockerfile']['entrypoint'] = ''
	cfg['dockerfile']['expose']     = []
	cfg['dockerfile']['env']        = []
	cfg['dockerfile']['volume']     = []
	cfg['dockerfile']['onbuild']    = []
	cfg['dockerfile']['script']     = []

	# Check setup
	if len(skel_path) == 0 or skel_path[0] != '/':
		shutit.fail('Must supply a directory and it must be absolute')
	if os.path.exists(skel_path):
		shutit.fail(skel_path + ' already exists')
	if len(skel_module_name) == 0:
		shutit.fail('Must supply a name for your module, eg mymodulename')
	if not re.match('^[a-zA-z_][0-9a-zA-Z_]+$', skel_module_name):
		shutit.fail('Module names must comply with python classname standards: cf: http://stackoverflow.com/questions/10120295/valid-characters-in-a-python-class-name')
	if len(skel_domain) == 0:
		shutit.fail('Must supply a domain for your module, eg com.yourname.madeupdomainsuffix')
	
	os.makedirs(skel_path)
	os.mkdir(os.path.join(skel_path, 'configs'))
	os.mkdir(os.path.join(skel_path, 'bin'))
	if skel_delivery != 'bash':
		os.mkdir(os.path.join(skel_path, 'context'))
		os.mkdir(os.path.join(skel_path, 'haproxy'))

	templatemodule_path   = os.path.join(skel_path, skel_module_name + '.py')
	readme_path           = os.path.join(skel_path, 'README.md')
	buildsh_path          = os.path.join(skel_path, 'bin', 'build.sh')
	testsh_path           = os.path.join(skel_path, 'bin', 'test.sh')
	runsh_path            = os.path.join(skel_path, 'bin', 'run.sh')
	phoenixsh_path        = os.path.join(skel_path, 'bin', 'phoenix.sh')
	buildpushsh_path      = os.path.join(skel_path, 'bin', 'build_and_push.sh')
	buildcnf_path         = os.path.join(skel_path, 'configs', 'build.cnf')
	pushcnf_path          = os.path.join(skel_path, 'configs', 'push.cnf')
	builddockerfile_path  = os.path.join(skel_path, 'Dockerfile')
	if skel_delivery != 'bash':
		haproxycnf_path          = os.path.join(skel_path, 'haproxy', 'haproxy.cfg')
		haproxydockerfile_path   = os.path.join(skel_path, 'haproxy', 'Dockerfile')

	if skel_dockerfile:
		if os.path.basename(skel_dockerfile) != 'Dockerfile':
			skel_dockerfile += '/Dockerfile'
		if not os.path.exists(skel_dockerfile):
			if urlparse.urlparse(skel_dockerfile)[0] == '':
				shutit.fail('Dockerfile "' + skel_dockerfile + '" must exist')
			dockerfile_contents = urllib2.urlopen(skel_dockerfile).read()
			dockerfile_dirname = None
		else:
			dockerfile_contents = open(skel_dockerfile).read()
			dockerfile_dirname = os.path.dirname(skel_dockerfile)
			if dockerfile_dirname == '':
				dockerfile_dirname = './'
			if os.path.exists(dockerfile_dirname):
				shutil.rmtree(skel_path + '/context')
				shutil.copytree(dockerfile_dirname, skel_path + '/context')
				# Remove Dockerfile as it's not part of the context.
				if os.path.isfile(skel_path + '/context/Dockerfile'):
					os.remove(skel_path + '/context/Dockerfile')
			# Change to this context
			os.chdir(dockerfile_dirname)
		# Wipe the command as we expect one in the file.
		cfg['dockerfile']['cmd']        = ''
		dockerfile_list = parse_dockerfile(shutit, dockerfile_contents)
		# Set defaults from given dockerfile
		for item in dockerfile_list:
			# These items are not order-dependent and don't affect the build, so we collect them here:
			docker_command = item[0].upper()
			if docker_command == 'FROM':
				# Should be only one of these
				cfg['dockerfile']['base_image'] = item[1]
			elif docker_command == "ONBUILD":
				# Maps to finalize :) - can we have more than one of these? assume yes
				# This contains within it one of the above commands, so we need to abstract this out.
				cfg['dockerfile']['onbuild'].append(item[1])
			elif docker_command == "MAINTAINER":
				cfg['dockerfile']['maintainer'] = item[1]
			elif docker_command == "VOLUME":
				# Put in the run.sh.
				try:
					cfg['dockerfile']['volume'].append(' '.join(json.loads(item[1])))
				except Exception:
					cfg['dockerfile']['volume'].append(item[1])
			elif docker_command == 'EXPOSE':
				# Put in the run.sh.
				cfg['dockerfile']['expose'].append(item[1])
			elif docker_command == "ENTRYPOINT":
				# Put in the run.sh? Yes, if it exists it goes at the front of cmd
				try:
					cfg['dockerfile']['entrypoint'] = ' '.join(json.loads(item[1]))
				except Exception:
					cfg['dockerfile']['entrypoint'] = item[1]
			elif docker_command == "CMD":
				# Put in the run.sh
				try:
					cfg['dockerfile']['cmd'] = ' '.join(json.loads(item[1]))
				except Exception:
					cfg['dockerfile']['cmd'] = item[1]
			# Other items to be run through sequentially (as they are part of the script)
			if docker_command == "USER":
				# Put in the start script as well as su'ing from here - assuming order dependent?
				cfg['dockerfile']['script'].append((docker_command, item[1]))
				# We assume the last one seen is the one we use for the image.
				# Put this in the default start script.
				cfg['dockerfile']['user']        = item[1]
			elif docker_command == 'ENV':
				# Put in the run.sh.
				cfg['dockerfile']['script'].append((docker_command, item[1]))
				# Set in the build
				cfg['dockerfile']['env'].append(item[1])
			elif docker_command == "RUN":
				# Only handle simple commands for now and ignore the fact that Dockerfiles run
				# with /bin/sh -c rather than bash.
				try:
					cfg['dockerfile']['script'].append((docker_command, ' '.join(json.loads(item[1]))))
				except Exception:
					cfg['dockerfile']['script'].append((docker_command, item[1]))
			elif docker_command == "ADD":
				# Send file - is this potentially got from the web? Is that the difference between this and COPY?
				cfg['dockerfile']['script'].append((docker_command, item[1]))
			elif docker_command == "COPY":
				# Send file
				cfg['dockerfile']['script'].append((docker_command, item[1]))
			elif docker_command == "WORKDIR":
				# Push and pop
				cfg['dockerfile']['script'].append((docker_command, item[1]))
			elif docker_command == "COMMENT":
				# Push and pop
				cfg['dockerfile']['script'].append((docker_command, item[1]))
		# We now have the script, so let's construct it inline here
		templatemodule = ''
		# Header.
		templatemodule += '''
# Created from dockerfile: ''' + skel_dockerfile + '''
# Maintainer:              ''' + cfg['dockerfile']['maintainer'] + '''
from shutit_module import ShutItModule

class template(ShutItModule):

	def is_installed(self, shutit):
		return False
'''
		# build
		build     = ''
		numpushes = 0
		wgetgot   = False
		for item in cfg['dockerfile']['script']:
			dockerfile_command = item[0].upper()
			dockerfile_args    = item[1].split()
			cmd = ' '.join(dockerfile_args).replace("'", "\\'")
			if dockerfile_command == 'RUN':
				build += """\n\t\tshutit.send('""" + cmd + """')"""
			elif dockerfile_command == 'WORKDIR':
				build += """\n\t\tshutit.send('pushd """ + cmd + """')"""
				numpushes = numpushes + 1
			elif dockerfile_command == 'COPY' or dockerfile_command == 'ADD':
				# The <src> path must be inside the context of the build; you cannot COPY ../something /something, because the first step of a docker build is to send the context directory (and subdirectories) to the docker daemon.
				if dockerfile_args[0][0:1] == '..' or dockerfile_args[0][0] == '/' or dockerfile_args[0][0] == '~':
					shutit.fail('Invalid line: ' + str(dockerfile_args) + ' file must be in local subdirectory')
				if dockerfile_args[1][-1] == '/':
					# Dir we're COPYing or ADDing to
					destdir  = dockerfile_args[1]
					# File/dir we're COPYing or ADDing from
					fromfile = dockerfile_args[0]
					# Final file/dir
					outfile  = destdir + fromfile
					if os.path.isfile(fromfile):
						outfiledir = os.path.dirname(fromfile)
						build += """\n\t\tshutit.send('mkdir -p """ + destdir + '/' + outfiledir + """')"""
					elif os.path.isdir(fromfile):
						build += """\n\t\tshutit.send('mkdir -p """ + destdir + fromfile + """')"""
				else:
					outfile = dockerfile_args[1]
				# If this is something we have to wget:
				if dockerfile_command == 'ADD' and urlparse.urlparse(dockerfile_args[0])[0] != '':
					if not wgetgot:
						build += """\n\t\tshutit.install('wget')"""
						wgetgot = True
					if dockerfile_args[1][-1] == '/':
						destdir = destdir[0:-1]
						outpath = urlparse.urlparse(dockerfile_args[0])[2]
						outpathdir = os.path.dirname(outpath)
						build += """\n\t\tshutit.send('mkdir -p """ + destdir + outpathdir + """')"""
						build += """\n\t\tshutit.send('wget -O """ + destdir + outpath + ' ' + dockerfile_args[0] + """')"""
					else:
						outpath  = dockerfile_args[1]
						destdir  = os.path.dirname(dockerfile_args[1])
						build += """\n\t\tshutit.send('mkdir -p """ + destdir + """')"""
						build += """\n\t\tshutit.send('wget -O """ + outpath + ' ' + dockerfile_args[0] + """')"""
				else:
					# From the local filesystem on construction:
					localfile = dockerfile_args[0]
					# Local file location on build:
					buildstagefile = 'context/' + dockerfile_args[0]
					#if localfile[-4:] == '.tar':
					#	build += """\n\t\tshutit.send_file('""" + outfile + '/' + localfile + """')"""
					#elif localfile[-4:] == '.bz2':
					#elif localfile[-3:] == '.gz':
					#elif localfile[-3:] == '.xz':
					if os.path.isdir(localfile):
						build += """\n\t\tshutit.send_host_dir('""" + outfile + """', '""" + buildstagefile + """')"""
					else:
						build += """\n\t\tshutit.send_host_file('""" + outfile + """', '""" + buildstagefile + """')"""
			elif dockerfile_command == 'ENV':
				cmd = '='.join(dockerfile_args).replace("'", "\\'")
				build += """\n\t\tshutit.send('export """ + '='.join(dockerfile_args) + """')"""
			elif dockerfile_command == 'COMMENT':
				build += """\n\t\t# """ + ' '.join(dockerfile_args)
		while numpushes > 0:
			build += """\n\t\tshutit.send('popd')"""
			numpushes = numpushes - 1
		templatemodule += '''
	def build(self, shutit):''' + build + '''
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
        # shutit.get_ip_address()            - Returns the ip address of the target
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
        # shutit.host_file_exists(filename, directory=False)
        #                                    - Returns True if file exists on host
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
'''
		# Gather and place finalize bit
		finalize = ''
		for line in cfg['dockerfile']['onbuild']:
			finalize += '\n\t\tshutit.send(\'' + line + '\''
		templatemodule += '''
	def finalize(self, shutit):''' + finalize + '''
		return True

	def test(self, shutit):
		return True

	def is_installed(self, shutit):
		return False

	def get_config(self, shutit):
		# CONFIGURATION
		# shutit.get_config(module_id,option,default=None,boolean=False)
		#                                    - Get configuration value, boolean indicates whether the item is
		#                                      a boolean type, eg get the config with:
		# shutit.get_config(self.module_id, 'myconfig', default='a value')
		#                                      and reference in your code with:
		# shutit.cfg[self.module_id]['myconfig']
		return True

'''
		templatemodule += """
def module():
		return template(
				""" + """\'%s.%s.%s\'""" % (skel_domain, skel_module_name, skel_module_name) + """, """ + skel_domain_hash + ".00" + """,
				description='',
				delivery_methods=[('""" + skel_delivery + """')],
				maintainer='""" + cfg['dockerfile']['maintainer'] + """',
				depends=['%s""" % (skel_depends) + """']
		)
"""
		# Return program to main shutit_dir
		if dockerfile_dirname:
			os.chdir(shutit_dir)

	else:
		templatemodule = open(find_asset('shutit_module_template_bare.py')).read()
	templatemodule = (templatemodule
		).replace('template', skel_module_name
		).replace('GLOBALLY_UNIQUE_STRING', '\'%s.%s.%s\'' % (skel_domain, skel_module_name, skel_module_name)
		).replace('FLOAT', skel_domain_hash + '.00'
		).replace('DEPENDS', skel_depends
		).replace('DELIVERY', skel_delivery
	)
	readme = skel_module_name + ': description of module directory in here'
	buildsh = textwrap.dedent('''\
		#!/bin/bash
		[[ -z "$SHUTIT" ]] && SHUTIT="$1/shutit"
		[[ ! -a "$SHUTIT" ]] || [[ -z "$SHUTIT" ]] && SHUTIT="$(which shutit)"
		if [[ ! -a "$SHUTIT" ]]
		then
			echo "Must have shutit on path, eg export PATH=$PATH:/path/to/shutit_dir"
			exit 1
		fi
		pushd ..
		$SHUTIT build "$@"
		if [[ $? != 0 ]]
		then
			popd
			exit 1
		fi
		popd
		''')
	testsh = textwrap.dedent('''\
		#!/bin/bash
		# Test the building of this module
		if [ $0 != test.sh ] && [ $0 != ./test.sh ]
		then
			echo
			echo "Called as: $0"
			echo "Must be run as test.sh or ./test.sh"
			exit
		fi
		./build.sh "$@"
		''')
	volumes_arg = ''
	for varg in cfg['dockerfile']['volume']:
		volumes_arg += ' -v ' + varg + ':' + varg
	ports_arg = ''
	if type(cfg['dockerfile']['expose']) == str:
		for parg in cfg['dockerfile']['expose']:
			ports_arg += ' -p ' + parg + ':' + parg
	else:
		for parg in cfg['dockerfile']['expose']:
			for port in parg.split():
				ports_arg += ' -p ' + port + ':' + port
	env_arg = ''
	for earg in cfg['dockerfile']['env']:
		env_arg += ' -e ' + earg.split()[0] + ':' + earg.split()[1]
	runsh = textwrap.dedent('''\
		#!/bin/bash
		# Example for running
		DOCKER=${DOCKER:-docker}
		IMAGE_NAME=%s
		CONTAINER_NAME=$IMAGE_NAME
		DOCKER_ARGS=''
		while getopts "i:c:a:" opt
		do
			case "$opt" in
			i)
				IMAGE_NAME=$OPTARG
				;;
			c)
				CONTAINER_NAME=$OPTARG
				;;
			a)
				DOCKER_ARGS=$OPTARG
				;;
			esac
		done
		${DOCKER} run -d --name ${CONTAINER_NAME}''' % (skel_module_name,) + ports_arg + volumes_arg + env_arg + ' ${DOCKER_ARGS} ${IMAGE_NAME} ' + cfg['dockerfile']['entrypoint'] + ' ' + cfg['dockerfile']['cmd'] + '\n')
	buildpushsh = textwrap.dedent('''\
		export SHUTIT_OPTIONS="$SHUTIT_OPTIONS --config configs/push.cnf -s repository push yes"
		./build.sh "$@"
		''')
	buildcnf = textwrap.dedent('''\
		###############################################################################
		# PLEASE NOTE: This file should be changed only by the maintainer.
		# PLEASE NOTE: This file is only sourced if the "shutit build" command is run
		#              and this file is in the relative path: configs/build.cnf
		#              This is to ensure it is only sourced if _this_ module is the
		#              target.
		###############################################################################
		# When this module is the one being built, which modules should be built along with it by default?
		# This feeds into automated testing of each module.
		[''' + '%s.%s.%s' % (skel_domain, skel_module_name, skel_module_name) + ''']
		shutit.core.module.build:yes
		# Allowed images as a regexp, eg ["ubuntu:12.*"], or [".*"], or ["centos"].
		# It's recommended this is locked down as far as possible.
		shutit.core.module.allowed_images:["''' + cfg['dockerfile']['base_image'] + '''"]

		# Aspects of build process
		[build]
		base_image:''' + cfg['dockerfile']['base_image'] + '''

		# Volume arguments wanted as part of the build
		[target]
		volumes:

		[repository]
		name:''' + skel_module_name + '''
		''')
	phoenixsh = textwrap.dedent('''\
#!/bin/bash
set -e
DOCKER=${DOCKER:-docker}
CONTAINER_BASE_NAME=${CONTAINER_BASE_NAME:-%s}
# haproxy image suffix
#                             Sent on to:
#                             HA_BACKEND_PORT_A
#                                   +
#                                   |
#            +------------------+   |    +----------------+
#            |                  |   |    |  Container A   |
#            |                  +---v---->  Open on port: |
#            |    HAProxy       |        |  CONTAINER_PORT|
#            |    Container     |        |                |
#            |                  |        +----------------+
#Request+---->received          |
#            |on port:          |        +----------------+
#            |HA_PROXY_PORT     |        |  Container B   |
#            |                  +---+---->  Open on port: |
#            |                  |   ^    |  CONTAINER_PORT|
#            |                  |   |    |                |
#            +------------------+   |    +----------------+
#                                   |
#                                   +
#                              Sent on to:
#                              HA_BACKEND_PORT_B
#
HA_PROXY_CONTAINER_SUFFIX=${HA_PROXY_CONTAINER_SUFFIX:-haproxy}
# The port on which your haproxy image is configured to receive requests from inside
HA_PROXY_PORT=${HA_PROXY_PORT:-8080}
# The port on which your backend 'a' is configured to receive requests on the host
HA_BACKEND_PORT_A=${HA_BACKEND_PORT_A:-8081}
# The port on which your backend 'b' is configured to receive requests on the host
HA_BACKEND_PORT_B=${HA_BACKEND_PORT_B:-8082}
# The port on which your service container receives requests
CONTAINER_PORT=${CONTAINER_PORT:-80}

# Set up haproxy.
# Remove proxy if it's died. If it doesn't exist, rebuild it first.
HAPROXY=$($DOCKER ps --filter=name=${CONTAINER_BASE_NAME}_${HA_PROXY_CONTAINER_SUFFIX} -q)
if [[ $HAPROXY = '' ]]
then
	HAPROXY=$($DOCKER ps --filter=name=${CONTAINER_BASE_NAME}_${HA_PROXY_CONTAINER_SUFFIX} -q -a)
	if [[ $HAPROXY != '' ]]
	then
		$DOCKER rm -f ${CONTAINER_BASE_NAME}_${HA_PROXY_CONTAINER_SUFFIX}
	fi
	pushd ../haproxy
	sed "s/HA_PROXY_PORT/${HA_PROXY_PORT}/g;s/HA_BACKEND_PORT_A/${HA_BACKEND_PORT_A}/g;s/HA_BACKEND_PORT_B/${HA_BACKEND_PORT_B}/g" haproxy.cfg.template > haproxy.cfg
	$DOCKER build -t ${CONTAINER_BASE_NAME}_${HA_PROXY_CONTAINER_SUFFIX} .
	$DOCKER run -d --net=host --name ${CONTAINER_BASE_NAME}_${HA_PROXY_CONTAINER_SUFFIX} ${CONTAINER_BASE_NAME}_${HA_PROXY_CONTAINER_SUFFIX}
	popd
fi

# Cleanup any left-over containers, build the new one, rename the old one,
# rename the new one, delete the old one.
$DOCKER rm -f ${CONTAINER_BASE_NAME}_old > /dev/null 2>&1 || /bin/true
./build.sh -s repository tag yes -s repository name ${CONTAINER_BASE_NAME}
# If there's a running instance, gather the used port, and move any old container
USED_PORT=''
NEW_PORT=${HA_BACKEND_PORT_A}
if [[ $($DOCKER ps --filter=name="${CONTAINER_BASE_NAME}$" -q -a) != '' ]]
then
	$DOCKER rm -f ${CONTAINER_BASE_NAME}_old > /dev/null 2>&1 || /bin/true
	USED_PORT=$($DOCKER inspect -f '{{range $p, $conf := .NetworkSettings.Ports}}{{(index $conf 0).HostPort}} {{end}}' $CONTAINER_BASE_NAME)
	# Decide which port to use
	if [[ "$USED_PORT" -eq "${HA_BACKEND_PORT_A}" ]]
	then
		NEW_PORT=${HA_BACKEND_PORT_B}
	fi
	$DOCKER rename ${CONTAINER_BASE_NAME} ${CONTAINER_BASE_NAME}_old
fi
# The random id is required - suspected docker bug
RANDOM_ID=$RANDOM
./run.sh -i "${CONTAINER_BASE_NAME}" -c "${CONTAINER_BASE_NAME}_${RANDOM_ID}" -a "-p ${NEW_PORT}:${CONTAINER_PORT}"
$DOCKER rm -f ${CONTAINER_BASE_NAME}_old > /dev/null 2>&1 || /bin/true
$DOCKER rename ${CONTAINER_BASE_NAME}_${RANDOM_ID} ${CONTAINER_BASE_NAME}''' % (skel_module_name))
	pushcnf = textwrap.dedent('''\
		###############################################################################
		# PLEASE NOTE: This file should be changed only by the maintainer.
		# PLEASE NOTE: IF YOU WANT TO CHANGE THE CONFIG, PASS IN
		#              --config configfilename
		#              OR ADD DETAILS TO YOUR
		#              ~/.shutit/config
		#              FILE
		###############################################################################
		[target]
		rm:false

		[repository]
		# COPY THESE TO YOUR ~/.shutit/config FILE AND FILL OUT ITEMS IN CAPS
		#user:YOUR_USERNAME
		## Fill these out in server- and username-specific config (also in this directory)
		#password:YOUR_REGISTRY_PASSWORD_OR_BLANK
		## Fill these out in server- and username-specific config (also in this directory)
		#email:YOUR_REGISTRY_EMAIL_OR_BLANK
		#tag:no
		#push:yes
		#save:no
		#export:no
		##server:REMOVE_ME_FOR_DOCKER_INDEX
		## tag suffix, defaults to "latest", eg registry/username/repository:latest.
		## empty is also "latest"
		#tag_name:latest
		#suffix_date:no
		#suffix_format:%s
		''')
	haproxycnf = textwrap.dedent('''\
		global
		    maxconn 256
		defaults
		    mode tcp
		frontend front_door
			bind *:HA_PROXY_PORT
			default_backend nodes
			timeout client 10m
		backend nodes
			timeout connect 2s
			timeout server  10m
			server server1 127.0.0.1:HA_BACKEND_PORT_A maxconn 32 check
			server server2 127.0.0.1:HA_BACKEND_PORT_B maxconn 32 check''')
	haproxydockerfile = textwrap.dedent('''\
		FROM haproxy:1.5
		COPY haproxy.cfg /usr/local/etc/haproxy/haproxy.cfg''')
	builddockerfile = textwrap.dedent('''\
       FROM ''' + cfg['dockerfile']['base_image'] + '''

       RUN apt-get update
       RUN apt-get install -y -qq git python-pip
       RUN pip install shutit

       WORKDIR /opt
       # Change the next two lines to build your ShutIt module.
       RUN git clone https://github.com/yourname/yourshutitproject.git
       WORKDIR /opt/yourshutitproject
       RUN shutit build --delivery dockerfile

       CMD ["/bin/bash"]
		''')

	open(templatemodule_path, 'w').write(templatemodule)
	open(buildsh_path, 'w').write(buildsh)
	os.chmod(buildsh_path, os.stat(buildsh_path).st_mode | 0111) # chmod +x
	open(buildcnf_path, 'w').write(buildcnf)
	os.chmod(buildcnf_path, 0400)
	if skel_delivery != 'bash':
		open(buildpushsh_path, 'w').write(buildpushsh)
		os.chmod(buildpushsh_path, os.stat(buildpushsh_path).st_mode | 0111) # chmod +x
		# build.cnf should be read-only (maintainer changes only)
		open(pushcnf_path, 'w').write(pushcnf)
		os.chmod(pushcnf_path, 0600)
		open(testsh_path, 'w').write(testsh)
		os.chmod(testsh_path, os.stat(testsh_path).st_mode | 0111) # chmod +x
		open(builddockerfile_path, 'w').write(builddockerfile)
		open(readme_path, 'w').write(readme)
		open(runsh_path, 'w').write(runsh)
		os.chmod(runsh_path, os.stat(runsh_path).st_mode | 0111) # chmod +x
		open(phoenixsh_path, 'w').write(phoenixsh)
		os.chmod(phoenixsh_path, os.stat(phoenixsh_path).st_mode | 0111) # chmod +x
		open(haproxycnf_path, 'w').write(haproxycnf)
		open(haproxycnf_path + '.template', 'w').write(haproxycnf)
		open(haproxydockerfile_path, 'w').write(haproxydockerfile)

	if skel_script is not None:
		print textwrap.dedent('''\
			================================================================================
			Please note that your bash script in:
			''' + skel_script + '''
			should be a simple set of one-liners
			that return to the prompt. Anything fancy with ifs, backslashes or other
			multi-line commands need to be handled more carefully.
			================================================================================''')

		sbsi = cfg['build']['shutit_state_dir'] + '/shutit_bash_script_include_' + str(int(time.time()))
		skel_mod_path = os.path.join(skel_path, skel_module_name + '.py')
		# Read in new file
		script_list = open(skel_script).read().splitlines()
		skel_mod_path_list = open(skel_mod_path).read().splitlines()
		new_script = []
		for line in script_list:
			# remove leading space
			line = line.strip()
			# ignore empty lines
			# ignore lines with leading #
			if len(line) == 0 or line[0] == '#':
				continue
			# surround with send command and space
			line = "\t\tshutit.send('''" + line + "''')"
			# double quotes (?)
			new_script.append(line)
		# insert code into relevant part of skel_mod_path
		final_script = ''
		def_build_found = False
		# Go through each line of the base file
		for line in skel_mod_path_list:
			# Set trip switch to on once we find def build
			if string.find(line,'def build') != -1:
				def_build_found = True
			# If we're in the build method, and at the return line....
			if def_build_found and string.find(line,'return True') != -1:
				# ...script in
				for new_script_line in new_script:
					final_script += new_script_line + '\r\n'
				# Set trip switch back to off
				def_build_found = False
			# Add line to final script
			final_script += line + '\r\n'
		open(skel_mod_path,'w').write(final_script)

	# Are we creating a new folder inside an existing git repo?
	if subprocess.call(['git', 'status'], stderr=open(os.devnull, 'wb'), stdout=open(os.devnull, 'wb')) != 0:
		subprocess.check_call(['git', 'init'], cwd=skel_path, stderr=open(os.devnull, 'wb'), stdout=open(os.devnull, 'wb'))
		try:
			subprocess.check_call([
				'cp', find_asset('.gitignore'), '.gitignore'
			], cwd=skel_path)
		except Exception:
			#gitignore is not essential
			pass

	if skel_output_dir:
		print skel_path
	else:
		print textwrap.dedent('''\
		================================================================================
		Run:
	
			cd ''' + skel_path + '''/bin && ./build.sh
	
		to build.
	
		An image called ''' + skel_module_name + ''' will be created
		and can be run with the run.sh command in bin/.
		================================================================================''')


# Parses the dockerfile (passed in as a string)
# and info to extract, and returns a list with the information in a more canonical form, still ordered.
def parse_dockerfile(shutit, contents):
	ret = []
	full_line = ''
	for l in contents.split('\n'):
		# Handle continuations
		if len(l) > 0:
			if l[-1] == '\\':
				full_line += l[0:-1]
				pass
			else:
				full_line += l
				m = re.match("^[\s]*([A-Za-z]+)[\s]*(.*)$", full_line)
				m1 = None
				if m:
					ret.append([m.group(1), m.group(2)])
				else:
					m1 = re.match("^#(..*)$", full_line)
				if m1:
					ret.append(['COMMENT', m1.group(1)])
				else:
					shutit.log("Ignored line in parse_dockerfile: " + l)
				full_line = ''
	return ret

def util_raw_input(shutit=None, prompt='', default=None, ispass=False):
	"""Handles raw_input calls, and switches off interactivity if there is apparently
	no controlling terminal (or there are any other problems)
	"""
	msg = ''
	prompt = '\n' + prompt + '\n'
	if shutit and shutit.cfg['build']['interactive'] == 0:
		return default
	if not determine_interactive(shutit):
		return default
	try:
		if ispass:
			print prompt
			return getpass.getpass()
		else:
			resp = raw_input(prompt).strip()
			if resp == '':
				return default
			else:
				return resp
	except Exception:
		msg = 'Problems getting raw input, assuming no controlling terminal.'
	if shutit:
		set_noninteractive(shutit,msg=msg)
	return default


def determine_interactive(shutit=None):
	"""Determine whether we're in an interactive context.
	Sets interactivity off if appropriate.
	cf http://stackoverflow.com/questions/24861351/how-to-detect-if-python-script-is-being-run-as-a-background-process
	"""
	try:
		if not sys.stdout.isatty() or os.getpgrp() != os.tcgetpgrp(sys.stdout.fileno()):
			if shutit != None:
				set_noninteractive(shutit)
			return False
	except Exception:
		if shutit != None:
			set_noninteractive(shutit,msg='Problems determining interactivity, assuming not.')
		return False
	return True


def set_noninteractive(shutit,msg="setting non-interactive"):
	cfg = shutit.cfg
	shutit.log(msg)
	cfg['build']['interactive'] = 0
	return


def print_stack_trace():
	print '================================================================================'
	print 'Strack trace was:\n================================================================================'
	import traceback
	(a,b,c) = sys.exc_info()
	traceback.print_tb(c)
	print '================================================================================'


# get the ordinal for a given char, in a friendly way
def get_wide_hex(char):
	if len(char) != 2:
		return r'\x' + hex(ord(char))[2:]
	return r'\u' + hex(0x10000 + (ord(char[0]) - 0xD800) * 0x400 + (ord(char[1]) - 0xDC00))[2:]



in_ctrlc = False
def ctrlc_background():
	global in_ctrlc
	in_ctrlc = True
	time.sleep(1)
	in_ctrlc = False
def ctrl_c_signal_handler(signal, frame):
	"""CTRL-c signal handler - enters a pause point if it can.
	"""
	if in_ctrlc:
		print "CTRL-c quit!"
		# Unfortunately we have 'except' blocks catching all exceptions,
		# so we can't use sys.exit
		os._exit(1)
	shutit_frame = get_shutit_frame(frame)
	print '\n' + '*' * 80
	print "CTRL-c caught"
	if shutit_frame:
		shutit = shutit_frame.f_locals['shutit']
		shutit.cfg['build']['ctrlc_stop'] = True
		print "You may need to wait for the command to complete for a pause point"
	print "CTRL-c twice to quit."
	print '*' * 80
	t = threading.Thread(target=ctrlc_background)
	t.daemon = True
	t.start()


def get_shutit_frame(frame):
	if not frame.f_back:
		return None
	else:
		if 'shutit' in frame.f_locals:
			return frame
		return get_shutit_frame(frame.f_back)


def print_frame_recurse(frame):
	if not frame.f_back:
		return
	else:
		print '============================================================================='
		print frame.f_locals
		print_frame_recurse(frame.f_back)


def check_regexp(regex):
	if regex == None:
		# Is this ok?
		return True
	try:
		re.compile(regex);
		result = True
	except re.error:
		result = False
	return result
