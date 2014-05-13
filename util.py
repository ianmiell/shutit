#!/usr/bin/env pythen

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
import ConfigParser
import time
import re
import imp
import shutit_global
import pexpect
import socket
import random
import textwrap
import tempfile
import json
import binascii
from shutit_module import ShutItFailException

# TODO: Manage exits of containers on error
def fail(msg,child=None):
	if child:
		pause_point(child,'Pause point on fail: ' + msg,force=True)
	print >> sys.stderr, 'ERROR!'
	print >> sys.stderr, red(msg)
	raise ShutItFailException(msg)

def is_file_secure(file_name):
	# If file doesn't exist, it's considered secure!
	if not os.path.isfile(file_name):
		return True
	file_mode = os.stat(file_name).st_mode
	if file_mode & (stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH):
		return False
	return True

# Deprecated
def log(msg,code=None,pause=0,cfg=None,prefix=True,force_stdout=False):
	if cfg not in [None, shutit_global.shutit.cfg]:
		print "Report this error and stack trace to repo owner, #d101"
		assert False
	return shutit_global.shutit.log(msg, code=code, pause=pause, prefix=prefix, force_stdout=force_stdout)

def colour(code, msg):   return '\033[%sm%s\033[0m' % (code, msg)
def grey(msg):           return colour('30', msg)
def red(msg):            return colour('31', msg)
def green(msg):          return colour('32', msg)
def yellow(msg):         return colour('33', msg)
def blue(msg):           return colour('34', msg)
def white(msg):          return colour('37', msg)
def reverse_green(msg):  return colour('7;32', msg)
def reverse_yellow(msg): return colour('7;33', msg)

# Deprecated
def send_and_expect(child,send,expect,timeout=3600,check_exit=True,cfg=None,fail_on_empty_before=True,record_command=True,exit_values=['0']):
	if cfg not in [None, shutit_global.shutit.cfg]:
		print "Report this error and stack trace to repo owner, #d102"
		assert False
	return shutit_global.shutit.send_and_expect(send,expect,
		child=child, timeout=timeout, check_exit=check_exit,
		fail_on_empty_before=fail_on_empty_before,
		record_command=record_command,exit_values=exit_values)

def get_config(cfg,module_id,option,default,boolean=False):
	if module_id not in cfg.keys():
		cfg[module_id] = {}
	if not cfg['config_parser'].has_section(module_id):
		cfg['config_parser'].add_section(module_id)
	if cfg['config_parser'].has_option(module_id,option):
		if boolean:
			cfg[module_id][option] = cfg['config_parser'].getboolean(module_id,option)
		else:
			cfg[module_id][option] = cfg['config_parser'].get(module_id,option)
	else:
		cfg[module_id][option] = default

def get_configs(configs):
	cp = ConfigParser.ConfigParser(None)
	fail_str = ''
	for config_file in configs:
		if not is_file_secure(config_file):
			fail_str = fail_str + '\nchmod 0600 ' + config_file
	if fail_str != '':
		fail_str = 'Files are not secure, mode should be 0600. Run the following commands to correct:\n' + fail_str + '\n'
		fail(fail_str)
	read_files = cp.read(configs)
	return cp

# Helper function to issue warning
def issue_warning(msg,wait):
	print >> sys.stderr, msg
	time.sleep(wait)

# Manage config settings, returning a dict representing the settings
# that have been sanity-checked.
def get_base_config(cfg, cfg_parser):
	cfg['config_parser'] = cp = cfg_parser
	# BEGIN Read from config files
	cfg['build']['interactive']                   = cp.getboolean('build','interactive')
	cfg['build']['action_on_ret_code']            = cp.get('build','action_on_ret_code')
	cfg['build']['privileged']                    = cp.getboolean('build','privileged')
	cfg['build']['lxc_conf']                      = cp.get('build','lxc_conf')
	cfg['build']['allowed_images']                = json.loads(cp.get('build','allowed_images'))
	cfg['container']['password']                  = cp.get('container','password')
	cfg['container']['hostname']                  = cp.get('container','hostname')
	cfg['container']['force_repo_work']           = cp.getboolean('container','force_repo_work')
	cfg['container']['locale']                    = cp.get('container','locale')
	cfg['container']['ports']                     = cp.get('container','ports')
	cfg['container']['name']                      = cp.get('container','name')
	cfg['container']['rm']                        = cp.getboolean('container','rm')
	cfg['host']['resources_dir']                  = cp.get('host','resources_dir')
	cfg['host']['docker_executable']              = cp.get('host','docker_executable')
	cfg['host']['dns']                            = cp.get('host','dns')
	cfg['host']['username']                       = cp.get('host','username')
	cfg['host']['password']                       = cp.get('host','password')
	cfg['host']['logfile']                        = cp.get('host','logfile')
	cfg['repository']['name']                     = cp.get('repository','name')
	cfg['repository']['server']                   = cp.get('repository','server')
	cfg['repository']['push']                     = cp.getboolean('repository','push')
	cfg['repository']['tar']                      = cp.getboolean('repository','tar')
	cfg['repository']['do_repository_work']       = cp.getboolean('repository','do_repository_work')
	cfg['repository']['suffix_date']              = cp.getboolean('repository','suffix_date')
	cfg['repository']['suffix_format']            = cp.get('repository','suffix_format')
	# We need this here as it's referenced even when do_repository_work is False.
	cfg['repository']['user']                     = cp.get('repository','user')
	if cfg['repository']['do_repository_work'] == True:
		if cfg['repository']['user'] != '':
			cfg['repository']['password']                 = cp.get('repository','password')
			cfg['repository']['email']                    = cp.get('repository','email')
	# END Read from config files

	# BEGIN Standard expects
	# It's important that these have '.*' in them at the start, so that the matched data is reliablly 'after' in the
	# child object. Use these where possible to make things more consistent.
	# Attempt to capture any starting prompt (when starting)
	cfg['expect_prompts']['base_prompt']             = '\r\n.*[@#$]'
	cfg['expect_prompts']['real_user_prompt']        = '\r\n.*?' + cfg['host']['real_user'] + '@.*:'
	# END Standard expects

	# BEGIN tidy configs up
	if cfg['host']['resources_dir'] == 'resources':
		cfg['host']['resources_dir'] = os.path.join(shutit_global.cwd, 'resources')
	elif cfg['host']['resources_dir'] == '':
		cfg['host']['resources_dir'] = os.path.join(shutit_global.shutit_main_dir, 'resources')
	if cfg['host']['logfile'] == '':
		logfile = os.path.join('/tmp/', 'shutit_log_' + cfg['build']['build_id'])
	else:
		logfile = logfile + '_' + cfg['build']['build_id']
	cfg['build']['build_log'] = open(logfile,'a')
	cfg['build']['container_build_log'] = '/tmp/shutit_log_' + cfg['build']['build_id']
	# Lock it down to the running user.
	os.chmod(logfile,0600)
	# tutorial implies interactive
	if cfg['build']['tutorial']:
		cfg['build']['interactive'] = True
	# debug implies interactive
	if cfg['build']['debug']:
		cfg['build']['interactive'] = True
	# END tidy configs up

	# BEGIN warnings
	# Warn if something appears not to have been overridden
	warn = ''
	if cfg['container']['password'][:5] == 'YOUR_':
		warn = '# Found ' + cfg['container']['password'] + ' in your config, you may want to quit and override, eg put the following into your\n# ' + shutit_global.cwd + '/configs/' + socket.gethostname() + '_' + cfg['host']['real_user'] + '.cnf file (create if necessary):\n\n[container]\npassword:mycontainerpassword\n\n'
		issue_warning(warn,2)
	if cfg['host']['username'][:5] == 'YOUR_':
		warn = '# Found ' + cfg['host']['username'] + ' in your config, you may want to quit and override, eg put the following into your\n# ' + shutit_global.cwd + '/configs/' + socket.gethostname() + '_' + cfg['host']['real_user'] + '.cnf file: (create if necessary)\n\n[host]\nusername:myusername\n\n'
		issue_warning(warn,2)
	if cfg['host']['password'][:5] == 'YOUR_':
		warn = '# Found ' + cfg['host']['password'] + ' in your config, you may want to quit and override, eg put the following into your\n# ' + shutit_global.cwd + '/configs/' + socket.gethostname() + '_' + cfg['host']['real_user'] + '.cnf file: (create if necessary)\n\n[host]\npassword:mypassword\n\n'
		issue_warning(warn,2)
	if warn != '':
		fail('Failed due to above warnings - please correct and retry')
	# END warnings
	# FAILS begins
	# rm is incompatible with do_repository_work
	if cfg['container']['rm'] and cfg['repository']['do_repository_work']:
		fail("Can't have [container]/rm and [repository]/do_repository_work set to true")
	if warn != '' and not cfg['build']['tutorial']:
		issue_warning('Showing computed config. This can also be done by calling --sc:',2)
		log(red(print_config(cfg)),force_stdout=True)
		time.sleep(1)
	# If build/allowed_images doesn't contain container/docker_image
	if 'any' not in cfg['build']['allowed_images'] and cfg['container']['docker_image'] not in cfg['build']['allowed_images']:
		fail('Allowed images for this build are: ' + str(cfg['build']['allowed_images']) + ' but the configured image is: ' + cfg['container']['docker_image'])
	# FAILS ends
	if cfg['host']['password'] == '':
		import getpass
		cfg['host']['password'] = getpass.getpass(prompt='Input your host machine password: ')
	if cfg['container']['password'] == '':
		import getpass
		cfg['container']['password'] = getpass.getpass(prompt='Input your container password: ')
	# Check action_on_ret_code values
	if cfg['build']['action_on_ret_code'] != 'msg' and cfg['build']['action_on_ret_code'] != 'error':
		fail('[build]\naction_on_ret_code:\nshould be set to "msg" or "error"')

# Returns the config dict
def parse_args(cfg):
	cfg['host']['real_user_id'] = pexpect.run('id -u ' + cfg['host']['real_user']).strip()

	parser = argparse.ArgumentParser(description='ShutIt - a tool for managing complex Docker deployments')
	parser.add_argument('--config', help='Config file for setup config. Must be with perms 0600. Multiple arguments allowed; config files considered in order.',default=[], action='append')
	parser.add_argument('-s', '--set', help='Override a config item, e.g. "-s container rm no". Can be specified multiple times.', default=[], action='append', nargs=3, metavar=('SEC','KEY','VAL'))
	parser.add_argument('--image_tag', help='Build container using specified image - if there is a symbolic reference, please use that, eg localhost.localdomain:5000/myref',default=cfg['container']['docker_image_default'])
	parser.add_argument('--shutit_module_path', default='.',help='List of shutit module paths, separated by colons. ShutIt registers modules by running all .py files in these directories.')
	parser.add_argument('--pause',help='Pause between commands to avoid race conditions.',default='0.5')
	parser.add_argument('--sc',help='Show the config computed and quit',default=False,const=True,action='store_const')
	parser.add_argument('--depgraph',help='Show dependency graph and quit',default=False,const=True,action='store_const')
	parser.add_argument('--serve',help='Start the ShutIt web UI',default=False,const=True,action='store_const')
	parser.add_argument('--debug',help='Show debug. Implies [build]/interactive config settings set, even if set to "no".',default=False,const=True,action='store_const')
	parser.add_argument('--tutorial',help='Show tutorial info. Implies [build]/interactive config setting set, even if set to "no".',default=False,const=True,action='store_const')

	args_list = sys.argv[1:]
	# Load command line options from the environment (if set)
	# Behaves like GREP_OPTIONS
	# - space seperated list of arguments
	# - backslash before a spaces escapes the space separation
	# - backslash before a backslash is interpreted as a single backslash
	# - all other backslashes are treated literally
	# e.g. ' a\ b c\\ \\d \\\e\' becomes '', 'a b', 'c\', '\d', '\\e\'
	if os.environ.get('SHUTIT_OPTIONS', None):
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
		args_list = env_args_list + args_list

	args = parser.parse_args(args_list)
	# Get these early for this part of the build.
	# These should never be config arguments, since they are needed before config is passed in.
	cfg['action']['show_config'] = args.sc
	cfg['action']['show_depgraph'] = args.depgraph
	cfg['action']['serve'] = args.serve
	cfg['build']['debug'] = args.debug
	cfg['build']['tutorial'] = args.tutorial
	cfg['build']['command_pause'] = float(args.pause)
	cfg['build']['extra_configs'] = args.config
	cfg['build']['config_overrides'] = args.set
	cfg['container']['docker_image'] = args.image_tag
	# Get module paths
	cfg['host']['shutit_module_paths'] = args.shutit_module_path.split(':')
	if '.' not in cfg['host']['shutit_module_paths']:
		if cfg['build']['debug']:
			log('Working directory path not included, adding...')
			time.sleep(1)
		cfg['host']['shutit_module_paths'].append('.')
	# Finished parsing args, tutorial stuff
	if cfg['build']['tutorial']:
		print textwrap.dedent("""\
			================================================================================
			SHUTIT - INTRODUCTION
			================================================================================
			ShutIt is a script that allows the building of static containers.
			allowing a high degree of flexibility and easy conversion from other build
			methods (eg bash scripts)

			It is configured through command-line arguments (see --help) and .cnf files.
			================================================================================


			================================================================================
			CONFIG
			================================================================================
			The config files are read in the following order:
			================================================================================
			""" + shutit_global.shutit_main_dir + """/configs/defaults.cnf
			    - Core shutit defaults. Maintained by BDFL.
			/path/to/shutit/module/configs/defaults.cnf
			    - Maintained by the module path directory's maintainer. Do not edit these
			      files unless you are the maintainer.
			      These are read in in the order in which the module paths were added in
			      --shutit_module_path (see --help)
			      shutit_module_path defaults to ".", adding "." if it wasn't explicitly
			      included. The paths in this run are:
			\t\t""" + str(cfg['host']['shutit_module_paths']) + """
			""" + shutit_global.shutit_main_dir + """/configs/`hostname`_`whoami`.cnf
			    - Host- and username-specific config for this host.
			/path/to/shutit/module/configs/`hostname`_`whoami`.cnf
			    - Hostname-specific config for the running user for this module.
			/path/to/this/shutit/module/configs/build.cnf
			    - Config specifying what should be built when this module is invoked.
			/your/path/to/<configname>.cnf
			    - Passed-in config (via --config, see --help)
			================================================================================
			Config items look like this:

			[section]
			name:value
			================================================================================

			""" + red('[Hit return to continue]'))
		raw_input('')
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
			        cleanup
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
			run relative to other modules.

			See """ + shutit_global.shutit_main_dir + """/shutit_module.py for more detailed documentation on these.
			================================================================================

			""" + red("[Hit return to continue]"))
		raw_input('')
		print textwrap.dedent("""\
			================================================================================
			PAUSE POINTS
			================================================================================
			Pause points can be placed within the build, which is useful for debugging.
			This is used throughout this tutorial.
			When debugging, pause_points will output your keyboard input before you finish.
			This can help you build your build, as these commands can be pasted into the
			module you are developing easily.
			To escape a pause point, hit the "CTRL" and the "]" key simultaneously.
			================================================================================
			""")
		pause_point(None,'')

def load_configs(shutit):
	cfg = shutit.cfg
	# Get root default config file
	default_config_file = os.path.join(shutit.shutit_main_dir, 'configs/defaults.cnf')
	configs = [default_config_file]
	# Now all the default configs we can see
	for path in cfg['host']['shutit_module_paths']:
		if os.path.exists(path):
			for root, subFolders, files in os.walk(path):
				for f in files:
					if f == 'defaults.cnf':
						configs.append(root + '/' + f)
	# Add the shutit global host- and user-specific config file.
	configs.append(os.path.join(shutit.shutit_main_dir,
		'configs/' + socket.gethostname() + '_' + cfg['host']['real_user'] + '.cnf'))
	# Then local host- and user-specific config file in this module.
	configs.append('configs/' + socket.gethostname() + '_' + cfg['host']['real_user'] + '.cnf')
	# Add the local build.cnf
	configs.append('configs/build.cnf')
	# Get passed-in config(s)
	for config_file_name in cfg['build']['extra_configs']:
		run_config_file = os.path.expanduser(config_file_name)
		if not os.path.isfile(run_config_file):
			fail('Did not recognise ' + run_config_file +
					' as a file - do you need to touch ' + run_config_file + '?')
		configs.append(run_config_file)
	# Image to use to start off. The script should be idempotent, so running it
	# on an already built image should be ok, and is advised to reduce diff space required.
	if cfg['build']['tutorial'] or cfg['action']['show_config']:
		msg = ''
		for c in configs:
			msg = msg + '\t\n' + c
			log('\t' + c)
		if cfg['build']['tutorial']:
			pause_point(None,'\n' + msg + '\n\nLooking at config files in the '
				'above order (even if they do not exist - you may want to '
				'create them).\n\nIf you get a "Port already in use:" error, '
				'run:\n\n\tdocker ps -a | grep -w <port> | awk \'{print $1}\' '
				'| xargs docker kill\nor\n\tsudo docker ps -a | grep -w <port> '
				'| awk \'{print $1}\' | xargs sudo docker kill\n',
				print_input=False)

	# Interpret any config overrides, write to a file and add them to the
	# list of configs to be interpreted
	if cfg['build']['config_overrides']:
		override_cp = ConfigParser.ConfigParser(None)
		for o_sec, o_key, o_val in cfg['build']['config_overrides']:
			if not override_cp.has_section(o_sec):
				override_cp.add_section(o_sec)
			override_cp.set(o_sec, o_key, o_val)
		fd, name = tempfile.mkstemp()
		os.write(fd, print_config({ "config_parser": override_cp }))
		os.close(fd)
		configs.append(name)

	cfg_parser = get_configs(configs)
	get_base_config(cfg, cfg_parser)

def load_shutit_modules(shutit):
	if shutit.cfg['build']['debug']:
		log('ShutIt module paths now: ')
		log(shutit.cfg['host']['shutit_module_paths'])
		time.sleep(1)
	for shutit_module_path in shutit.cfg['host']['shutit_module_paths']:
		load_all_from_path(shutit, shutit_module_path)

def print_config(cfg):
	s = ''
	for section in cfg['config_parser'].sections():
		s = s + '\n[' + section + ']\n'
		for item in cfg['config_parser'].items(section):
			name = str(item[0])
			value = str(item[1])
			if name == 'password':
				value = 'XXX'
			s = s + name + ':' + value
			s = s + '\n'
	s = s + '\n'
	return s

# Deprecated
def pause_point(child,msg,print_input=True,expect='',cfg=None,force=False):
	if cfg not in [None, shutit_global.shutit.cfg]:
		print "Report this error and stack trace to repo owner, #d103"
		assert False
	shutit_global.shutit.pause_point(msg, child=child, print_input=print_input,
		expect=expect, force=force)

# Commit, tag, push, tar etc..
# expect must be a string
def do_repository_work(cfg,expect,repo_name,docker_executable='docker',password=None,force=False):
	if not (cfg['repository']['do_repository_work'] or force):
		return
	child = get_pexpect_child('host_child')
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
		fail('Could not form valid repository name')
	if cfg['repository']['tar'] and not repository_tar:
		fail('Could not form valid tar name')

	if server:
		repository = '%s/%s' % (server, repository)

	if cfg['repository']['suffix_date']:
		suffix_date = time.strftime(cfg['repository']['suffix_format'])
		repository = '%s_%s' % (repository, suffix_date)
		repository_tar = '%s_%s' % (repository_tar, suffix_date)

	if server == '' and len(repository) > 30:
		fail("""repository name: '""" + repository + """' too long. If using suffix_date consider shortening""")

	# Only lower case accepted
	repository = repository.lower()
	# Slight pause due to race conditions seen.
	#time.sleep(0.3)
	res = send_and_expect(child,'SHUTIT_TMP_VAR=`' + docker_executable + ' commit ' + cfg['container']['container_id'] + '`',[expect,'assword'],timeout=99999,check_exit=False)
	if res == 1:
		send_and_expect(child,cfg['host']['password'],expect,check_exit=False,record_command=False)
	send_and_expect(child,'echo $SHUTIT_TMP_VAR && unset SHUTIT_TMP_VAR',expect,check_exit=False,record_command=False)
	image_id = child.after.split('\r\n')[1]

	if not image_id:
		fail('failed to commit to ' + repository + ', could not determine image id')

	cmd = docker_executable + ' tag ' + image_id + ' ' + repository
	send_and_expect(child,cmd,expect,check_exit=False)
	if cfg['repository']['tar']:
		if cfg['build']['tutorial']:
			pause_point(child,'We are now exporting the container to a bzipped tar file, as configured in \n[repository]\ntar:yes',print_input=False)
		bzfile = cfg['host']['resources_dir'] + '/' + repository_tar + '.tar.bz2'
		log('\nDepositing bzip2 of exported container into ' + bzfile)
		res = send_and_expect(child,docker_executable + ' export ' + cfg['container']['container_id'] + ' | bzip2 - > ' + bzfile,[expect,'assword'],timeout=99999)
		log(red('\nDeposited bzip2 of exported container into ' + bzfile))
		log(red('\nRun:\n\nbunzip2 -c ' + bzfile + ' | sudo docker import -\n\nto get this imported into docker.'))
		cfg['build']['report'] = cfg['build']['report'] + '\nDeposited bzip2 of exported container into ' + bzfile
		cfg['build']['report'] = cfg['build']['report'] + '\nRun:\n\nbunzip2 -c ' + bzfile + ' | sudo docker import -\n\nto get this imported into docker.'
		if res == 1:
			send_and_expect(child,password,expect,record_command=False)
	if cfg['repository']['push'] == True:
		push_repository(child,repository,cfg,docker_executable,expect)
		cfg['build']['report'] = cfg['build']['report'] + 'Pushed repository: ' + repository

# Deprecated
def file_exists(child,filename,expect,directory=False):
	return shutit_global.shutit.file_exists(filename, expect, child=child,
		directory=directory)

# Deprecated
def get_file_perms(child,filename,expect):
	return shutit_global.shutit.get_file_perms(filename,expect,child=child)

# Deprecated
def add_line_to_file(child,line,filename,expect,match_regexp=None,truncate=False,force=False,literal=False):
	return shutit_global.shutit.add_line_to_file(line, filename, expect,
		child=child, match_regexp=match_regexp, truncate=truncate, force=force,
		literal=literal)

# Deprecated
def get_re_from_child(string,regexp,cfg=None):
	return shutit_global.shutit.get_re_from_child(string, regexp)

# expect must be a string
def push_repository(child,repository,cfg,docker_executable,expect):
	send = docker_executable + ' push ' + repository
	expect_list = ['Pushing','Buffering','Username:','Password:','Email:',expect]
	timeout=99999
	res = send_and_expect(child,send,expect_list,timeout=timeout,check_exit=False)
	while True:
		if res == 5:
			break
		elif res == 2:
			res = send_and_expect(child,cfg['repository']['user'],expect_list,timeout=timeout,check_exit=False)
		elif res == 3:
			res = send_and_expect(child,cfg['repository']['password'],expect_list,timeout=timeout,check_exit=False)
		elif res == 4:
			res = send_and_expect(child,cfg['repository']['email'],expect_list,timeout=timeout,check_exit=False)
		else:
			res = child.expect(expect_list,timeout=timeout)

# Deprecated
def add_to_bashrc(child,line,expect):
	return shutit_global.shutit.add_line_to_file(line,'/etc/profile',expect=expect) and shutit_global.shutit.add_line_to_file(line,'/etc/bash.bashrc',expect=expect)

# Set a pexpect child in the global dictionary by key.
def set_pexpect_child(key,child):
	shutit_global.pexpect_children.update({key:child})

# Get a pexpect child in the global dictionary by key.
def get_pexpect_child(key):
	return shutit_global.pexpect_children[key]

# dynamically import files within the same directory (in the end, the path)
#http://stackoverflow.com/questions/301134/dynamic-module-import-in-python
def load_all_from_path(shutit, path):
	if os.path.abspath(path) == shutit.shutit_main_dir:
		return
	if os.path.exists(path):
		for root, subFolders, files in os.walk(path):
			for f in files:
				mod_name,file_ext = os.path.splitext(os.path.split(f)[-1])
				if file_ext.lower() == '.py':
					if shutit.cfg['build']['debug']:
						log('Loading source for: ' + mod_name,os.path.join(root,f))
					imp.load_source(mod_name,os.path.join(root,f))

def module_exists(module_id):
	for m in get_shutit_modules():
		if m.module_id == module_id:
			return True
	return False


# Helper function to get global without importing it.
def get_shutit_modules():
	return shutit_global.shutit_modules


# Deprecated
def install(child,cfg,package,expect,options=None,timeout=3600):
	if cfg not in [None,shutit_global.shutit.cfg]:
		print "Report this error and stack trace to repo owner, #d102"
		assert False
	return shutit_global.shutit.install(package,
		child=child,expect=expect,options=options,timeout=timeout)

# Distro-independent remove function.
# Takes a package name and runs purge/delete on it. Generally takes the most aggressive removal option.
# Returns true if all ok (ie it's installed now), else false
def remove(child,cfg,package,expect,options=None):
	if cfg not in [None,shutit_global.shutit.cfg]:
		print "Report this error and stack trace to repo owner, #d102"
		assert False
	return shutit_global.shutit.remove(package,
		child=child,expect=expect,options=options)

# Deprecated
def package_installed(child,cfg,package,expect):
	if cfg not in [None,shutit_global.shutit.cfg]:
		print "Report this error and stack trace to repo owner, #d102"
		assert False
	return shutit_global.shutit.package_installed(package,expect,child)

# Fails if distro could not be determined.
# Should be called with the container is started up.
def get_distro_info(child,outer_expect,cfg):
	cfg['container']['install_type']      = ''
	cfg['container']['distro']            = ''
	cfg['container']['distro_version']    = ''
	install_type_map = {'ubuntu':'apt','debian':'apt','red hat':'yum','centos':'yum','fedora':'yum'}
	shutit_global.shutit.handle_login('tmp_prompt')
	if file_exists(child,cfg['build']['cidfile'],cfg['expect_prompts']['tmp_prompt']):
		fail('Did not start up container. If you got a "port in use" error, try:\n\n' + cfg['host']['docker_executable'] + ' ps -a | grep ' + cfg['container']['ports'] + ' | awk \'{print $1}\' | xargs ' + cfg['host']['docker_executable'] + ' kill\n\n')
	for key in install_type_map.keys():
		# Use grep (not egrep) because it's likely installed _everywhere_ by default.
		child.sendline('cat /etc/issue | grep -i "' + key + '" | wc -l')
		child.expect(cfg['expect_prompts']['tmp_prompt'])
		if get_re_from_child(child.before,'^([0-9]+)$') == '1':
			cfg['container']['distro']       = key
			cfg['container']['install_type'] = install_type_map[key]
			break
	set_password(child,cfg,cfg['expect_prompts']['tmp_prompt'],cfg['container']['password'])
	if cfg['container']['install_type'] == 'apt':
		cfg['expect_prompts']['real_user_prompt']        = '\r\n.*?' + cfg['host']['real_user'] + '@.*:'
		send_and_expect(child,'export DEBIAN_FRONTEND=noninteractive',cfg['expect_prompts']['tmp_prompt'])
		send_and_expect(child,'apt-get update',cfg['expect_prompts']['tmp_prompt'],timeout=9999,check_exit=False)
		send_and_expect(child,'dpkg-divert --local --rename --add /sbin/initctl',cfg['expect_prompts']['tmp_prompt'])
		send_and_expect(child,'ln -f -s /bin/true /sbin/initctl',cfg['expect_prompts']['tmp_prompt'])
		install(child,cfg,'passwd',cfg['expect_prompts']['tmp_prompt'])
		install(child,cfg,'sudo',cfg['expect_prompts']['tmp_prompt'])
	elif cfg['container']['install_type'] == 'yum':
		cfg['expect_prompts']['real_user_prompt']        = '\r\n.*?' + cfg['host']['real_user'] + '@.*:'
		install(child,cfg,'passwd',cfg['expect_prompts']['tmp_prompt'])
		install(child,cfg,'sudo',cfg['expect_prompts']['tmp_prompt'])
		send_and_expect(child,'yum update -y',cfg['expect_prompts']['tmp_prompt'],timeout=9999)
	if cfg['container']['install_type'] == '' or cfg['container']['distro'] == '':
		fail('Could not determine Linux distro information. Please inform maintainers.')
	shutit_global.shutit.handle_revert_prompt(outer_expect,'tmp_prompt')

def set_password(child,cfg,expect,password):
	if cfg['container']['install_type'] == 'apt':
		send_and_expect(child,'passwd','Enter new',check_exit=False)
		send_and_expect(child,password,'Retype new',check_exit=False,record_command=False)
		send_and_expect(child,password,expect,record_command=False)
	elif cfg['container']['install_type'] == 'yum':
		send_and_expect(child,'passwd','ew password',check_exit=False,record_command=False)
		send_and_expect(child,password,'ew password',check_exit=False,record_command=False)
		send_and_expect(child,password,expect,record_command=False)
	shutit_global.shutit.handle_login('password_tmp_prompt')
	send_and_expect(child,'/bin/true',cfg['expect_prompts']['password_tmp_prompt'],record_command=False)
	shutit_global.shutit.handle_revert_prompt(expect,'password_tmp_prompt')


# Deprecated
# Returns prompt expected
def handle_login(child,cfg,prompt_name):
	shutit_global.shutit.handle_login(prompt_name)

# Deprecated
def handle_revert_prompt(child,expect,prompt_name):
	shutit_global.shutit.handle_revert_prompt(expect,prompt_name)


# Determine whether a user_id for a user is available
def is_user_id_available(child,user_id,expect):
	send_and_expect(child,'cut -d: -f3 /etc/paswd | grep -w ^' + user_id + '$ | wc -l',expect,check_exit=False,record_command=False)
	if get_re_from_child(child.before,'^([0-9]+)$') == '1':
		return False
	else:
		return True

# Sets up a base prompt
def setup_prompt(child,cfg,prefix,prompt_name):
	local_prompt = prefix + str(random.getrandbits(32))
	child.sendline('SHUTIT_BACKUP_PS1=$PS1 && unset PROMPT_COMMAND && PS1="' + local_prompt + '"')
	cfg['expect_prompts'][prompt_name] = '\r\n' + local_prompt
	child.expect(cfg['expect_prompts'][prompt_name])

# Build report
def build_report(msg=''):
	s = ''
	s = s + '################################################################################\n'
	s = s + '# COMMAND HISTORY BEGIN ' + shutit_global.cfg['build']['build_id'] + '\n'
	s = s + '################################################################################\n'
	for c in shutit_global.shutit_command_history:
		s = s + c + '\n'
	s = s + '# COMMAND HISTORY END ' + shutit_global.cfg['build']['build_id'] + '\n'
	s = s + '################################################################################\n'
	s = s + '################################################################################\n'
	s = s + '# BUILD REPORT FOR BUILD BEGIN ' + shutit_global.cfg['build']['build_id'] + '\n'
	s = s + '# ' + msg + '\n'
	s = s + '################################################################################\n'
	if shutit_global.cfg['build']['report'] != '':
		s = s + shutit_global.cfg['build']['report'] + '\n'
	else:
		s = s + '# Nothing to report\n'
	s = s + '# BUILD REPORT FOR BUILD END ' + shutit_global.cfg['build']['build_id'] + '\n'
	s = s + '################################################################################\n'
	return s

# Helper function to get preceding integer
# eg com.openbet == 1003189494
# >>> import binascii
# >>> abs(binascii.crc32('shutit.tk'))
# 782914092
#
# Not in use, but recommended means of determining run order integer part.
def get_hash(string):
	return abs(binascii.crc32(string))
