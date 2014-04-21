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
import binascii
import random
import textwrap
import tempfile

# TODO: Manage exits of containers on error
def fail(msg,child=None):
	if child:
		pause_point(child,'Pause point on fail: ' + msg,force=True)
	print >> sys.stderr, 'ERROR!'
	print >> sys.stderr, red(msg)
	sys.exit(1)

def is_file_secure(file_name):
	# If file doesn't exist, it's considered secure!
	if not os.path.isfile(file_name):
		return True
	file_mode = os.stat(file_name).st_mode
	if file_mode & (stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH):
		return False
	return True

def log(msg,code=None,pause=0,config_dict=None,prefix=True,force_stdout=False):
	if config_dict is None: config_dict = shutit_global.config_dict
	if prefix:
		prefix = 'LOG: ' + time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
		msg = prefix + ' ' + str(msg)
	if code != None:
		msg = colour(code, msg)
	if config_dict['build']['debug'] or force_stdout:
		print >> sys.stdout, msg
	if config_dict['build']['build_log'] != {}:
		print >> config_dict['build']['build_log'], msg
		config_dict['build']['build_log'].flush()
	time.sleep(pause)

def colour(code, msg):   return '\033[%sm%s\033[0m' % (code, msg)
def grey(msg):           return colour('30', msg)
def red(msg):            return colour('31', msg)
def green(msg):          return colour('32', msg)
def yellow(msg):         return colour('33', msg)
def blue(msg):           return colour('34', msg)
def white(msg):          return colour('37', msg)
def reverse_green(msg):  return colour('7;32', msg)
def reverse_yellow(msg): return colour('7;33', msg)

# Wrapper for send and expect where convenient.
# Helpful for debugging.
# Returns the expect return value
#
# child                      - pexpect child to issue command to.
# send                       - String to send, ie the command being issued.
# expect                     - String that we expect to see in the output. Usually a prompt.
# timeout                    - Timeout on response (default=3600 seconds).
# check_exit                 - Whether the check the shell exit code of the command. If the exit value was non-zero an error is thrown. (default=True)
# config_dict                - config_dict variable (default=shutit_global.config_dict)
# fail_on_empty_before       - If debug is set, fail on empty before match (default=True)
# record_command             - Whether to record the command for output at end (default=True)
# exit_values                - Array of acceptable exit values (default [0])
def send_and_expect(child,send,expect,timeout=3600,check_exit=True,config_dict=None,fail_on_empty_before=True,record_command=True,exit_values=['0']):
	if config_dict is None: config_dict = shutit_global.config_dict
	if config_dict['build']['debug']:
		log('================================================================================')
		log('Sending>>>' + send + '<<<')
		log('Expecting>>>' + str(expect) + '<<<')
	# Race conditions have been seen - might want to remove this
	time.sleep(config_dict['build']['command_pause'])
	child.sendline(send)
	expect_res = child.expect(expect,timeout)
	if config_dict['build']['debug']:
		log('child.before>>>' + child.before + '<<<')
		log('child.after>>>' + child.after + '<<<')
	if fail_on_empty_before == True:
		if child.before.strip() == '':
			fail('before empty after sending: ' + send + '\n\nThis is expected after some commands that take a password.\nIf so, add fail_on_empty_before=False to the send_and_expect call')
	elif fail_on_empty_before == False:
		# Don't check exit if fail_on_empty_before is False
		log('' + child.before + '<<<')
		check_exit = False
		for prompt in config_dict['expect_prompts']:
			if prompt == expect:
				# Reset prompt
				handle_login(child,config_dict,'reset_tmp_prompt')
				handle_revert_prompt(child,expect,'reset_tmp_prompt')
	if check_exit == True:
		child.sendline('echo EXIT_CODE:$?')
		child.expect(expect,timeout)
		res = get_re_from_child(child.before,'^EXIT_CODE:([0-9][0-9]?[0-9]?)$')
		#print 'RES', str(res), ' ', str(exit_values), ' ', str(res in exit_values)
		if res not in exit_values or res == None:
			if res == None:
				res = str(res)
			log(red('child.after: \n' + child.after + '\n'))
			log(red('Exit value from command+\n' + send + '\nwas:\n' + res))
			msg = '\nWARNING: command:\n' + send + '\nreturned unaccepted exit code: ' + res + '\nIf this is expected, pass in check_exit=False or an exit_values array into the send_and_expect function call.\nIf you want to error on these errors, set the config:\n[build]\naction_on_ret_code:error'
			config_dict['build']['report'] = config_dict['build']['report'] + msg
			if config_dict['build']['action_on_ret_code'] == 'error':
				pause_point(child,msg + '\n\nPause point on exit_code != 0. CTRL-C to quit',force=True)
				#raise Exception('Exit value from command\n' + send + '\nwas:\n' + res)
	# If the command matches any 'password's then don't record
	if record_command:
		ok_to_record = True
		for i in config_dict.keys():
			if isinstance(config_dict[i],dict):
				for j in config_dict[i].keys():
					if j == 'password' and config_dict[i][j] == send:
						shutit_global.shutit_command_history.append('#redacted command, password')
						ok_to_record = False
						break
				if not ok_to_record:
					break
		if ok_to_record:
			shutit_global.shutit_command_history.append(send)
	else:
		shutit_global.shutit_command_history.append('#redacted command')
	return expect_res


def get_config(config_dict,module_id,option,default,boolean=False):
	if module_id not in config_dict.keys():
		config_dict[module_id] = {}
	if not config_dict['config_parser'].has_section(module_id):
		config_dict['config_parser'].add_section(module_id)
	if config_dict['config_parser'].has_option(module_id,option):
		if boolean:
			config_dict[module_id][option] = config_dict['config_parser'].getboolean(module_id,option)
		else:
			config_dict[module_id][option] = config_dict['config_parser'].get(module_id,option)
	else:
		config_dict[module_id][option] = default

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
def get_base_config(config_dict, cfg_parser):
	config_dict['config_parser'] = cp = cfg_parser
	# BEGIN Read from config files
	config_dict['build']['interactive']                   = cp.getboolean('build','interactive')
	config_dict['build']['action_on_ret_code']            = cp.get('build','action_on_ret_code')
	config_dict['build']['privileged']                    = cp.getboolean('build','privileged')
	config_dict['build']['lxc_conf']                      = cp.get('build','lxc_conf')
	config_dict['build']['allowed_images']                = cp.get('build','allowed_images')
	config_dict['container']['password']                  = cp.get('container','password')
	config_dict['container']['hostname']                  = cp.get('container','hostname')
	config_dict['container']['force_repo_work']           = cp.getboolean('container','force_repo_work')
	config_dict['container']['locale']                    = cp.get('container','locale')
	config_dict['container']['ports']                     = cp.get('container','ports')
	config_dict['container']['name']                      = cp.get('container','name')
	config_dict['container']['rm']                        = cp.getboolean('container','rm')
	config_dict['host']['resources_dir']                  = cp.get('host','resources_dir')
	config_dict['host']['docker_executable']              = cp.get('host','docker_executable')
	config_dict['host']['dns']                            = cp.get('host','dns')
	config_dict['host']['username']                       = cp.get('host','username')
	config_dict['host']['password']                       = cp.get('host','password')
	config_dict['host']['logfile']                        = cp.get('host','logfile')
	config_dict['repository']['name']                     = cp.get('repository','name')
	config_dict['repository']['server']                   = cp.get('repository','server')
	config_dict['repository']['push']                     = cp.getboolean('repository','push')
	config_dict['repository']['tar']                      = cp.getboolean('repository','tar')
	config_dict['repository']['do_repository_work']       = cp.getboolean('repository','do_repository_work')
	config_dict['repository']['suffix_date']              = cp.getboolean('repository','suffix_date')
	config_dict['repository']['suffix_format']            = cp.get('repository','suffix_format')
	if config_dict['repository']['do_repository_work'] == True:
		config_dict['repository']['user']                     = cp.get('repository','user')
		if config_dict['repository']['user'] != '':
			config_dict['repository']['password']                 = cp.get('repository','password')
			config_dict['repository']['email']                    = cp.get('repository','email')
	# END Read from config files

	# BEGIN Standard expects
	# It's important that these have '.*' in them at the start, so that the matched data is reliablly 'after' in the
	# child object. Use these where possible to make things more consistent.
	# Attempt to capture any starting prompt (when starting)
	config_dict['expect_prompts']['base_prompt']             = '\r\n.*[@#$]'
	config_dict['expect_prompts']['real_user_prompt']        = '\r\n.*?' + config_dict['host']['real_user'] + '@.*:'
	# END Standard expects

	# BEGIN tidy configs up
	if config_dict['host']['resources_dir'] == 'resources':
		config_dict['host']['resources_dir'] = os.path.join(shutit_global.cwd, 'resources')
	elif config_dict['host']['resources_dir'] == '':
		config_dict['host']['resources_dir'] = os.path.join(shutit_global.shutit_main_dir, 'resources')
	if config_dict['host']['logfile'] == '':
		logfile = os.path.join('/tmp/', 'shutit_log_' + config_dict['build']['build_id'])
	else:
		logfile = logfile + '_' + config_dict['build']['build_id']
	config_dict['build']['build_log'] = open(logfile,'a')
	config_dict['build']['container_build_log'] = '/tmp/shutit_log_' + config_dict['build']['build_id']
	# Lock it down to the running user.
	os.chmod(logfile,0600)
	# tutorial implies interactive
	if config_dict['build']['tutorial']:
		config_dict['build']['interactive'] = True
	# debug implies interactive
	if config_dict['build']['debug']:
		config_dict['build']['interactive'] = True
	# END tidy configs up

	# BEGIN warnings
	# Warn if something appears not to have been overridden
	warn = ''
	if config_dict['container']['password'][:5] == 'YOUR_':
		warn = '# Found ' + config_dict['container']['password'] + ' in your config, you may want to quit and override, eg put the following into your\n# ' + shutit_global.cwd + '/configs/' + socket.gethostname() + '_' + config_dict['host']['real_user'] + '.cnf file (create if necessary):\n[container]\npassword:mycontainerpassword'
		issue_warning(warn,2)
	if config_dict['host']['username'][:5] == 'YOUR_':
		warn = '# Found ' + config_dict['host']['username'] + ' in your config, you may want to quit and override, eg put the following into your\n# ' + shutit_global.cwd + '/configs/' + socket.gethostname() + '_' + config_dict['host']['real_user'] + '.cnf file: (create if necessary)\n[host]\nusername:myusername'
		issue_warning(warn,2)
	if config_dict['host']['password'][:5] == 'YOUR_':
		warn = '# Found ' + config_dict['host']['password'] + ' in your config, you may want to quit and override, eg put the following into your\n# ' + shutit_global.cwd + '/configs/' + socket.gethostname() + '_' + config_dict['host']['real_user'] + '.cnf file: (create if necessary)\n[host]\npassword:mypassword'
		issue_warning(warn,2)
	# END warnings
	# FAILS begins
	# rm is incompatible with do_repository_work
	if config_dict['container']['rm'] and config_dict['repository']['do_repository_work']:
		fail("Can't have [container]/rm and [repository]/do_repository_work set to true")
	if warn != '' and not config_dict['build']['tutorial']:
		issue_warning('Showing computed config. This can also be done by calling --sc:',2)
		log(red(print_config(config_dict)),force_stdout=True)
		time.sleep(1)
	# If build/allowed_images doesn't contain container/docker_image
	if config_dict['build']['allowed_images'] != 'any' and config_dict['container']['docker_image'] not in config_dict['build']['allowed_images']:
		fail('Allowed images for this build are: ' + config_dict['build']['allowed_images'] + ' but the configured image is: ' + config_dict['container']['docker_image'])
	# FAILS ends
	if config_dict['host']['password'] == '':
		import getpass
		config_dict['host']['password'] = getpass.getpass(prompt='Input your host machine password: ')
	if config_dict['container']['password'] == '':
		import getpass
		config_dict['container']['password'] = getpass.getpass(prompt='Input your container password: ')
	# Check action_on_ret_code values
	if config_dict['build']['action_on_ret_code'] != 'msg' and config_dict['build']['action_on_ret_code'] != 'error':
		fail('[build]\naction_on_ret_code:\nshould be set to "msg" or "error"')

# Returns the config dict
def parse_args(config_dict):
	config_dict['host']['real_user_id'] = pexpect.run('id -u ' + config_dict['host']['real_user']).strip()

	parser = argparse.ArgumentParser(description='ShutIt - a tool for managing complex Docker deployments')
	parser.add_argument('--config', help='Config file for setup config. Must be with perms 0600. Multiple arguments allowed; config files considered in order.',default=[], action='append')
	parser.add_argument('-s', '--set', help='Override a config item, e.g. "-s container rm no". Can be specified multiple times.', default=[], action='append', nargs=3, metavar=('SEC','KEY','VAL'))
	parser.add_argument('--image_tag', help='Build container using specified image - if there is a symbolic reference, please use that, eg localhost.localdomain:5000/myref',default=config_dict['container']['docker_image_default'])
	parser.add_argument('--shutit_module_path', default='.',help='List of shutit module paths, separated by colons. ShutIt registers modules by running all .py files in these directories.')
	parser.add_argument('--pause',help='Pause between commands to avoid race conditions.',default='0.5')
	parser.add_argument('--sc',help='Show the config computed and quit',default=False,const=True,action='store_const')
	parser.add_argument('--depgraph',help='Show dependency graph and quit',default=False,const=True,action='store_const')
	parser.add_argument('--debug',help='Show debug. Implies [build]/interactive config settings set, even if set to "no".',default=False,const=True,action='store_const')
	parser.add_argument('--tutorial',help='Show tutorial info. Implies [build]/interactive config setting set, even if set to "no".',default=False,const=True,action='store_const')

	args_list = sys.argv[1:]
	# Load command line options from the environment (if set)
	# Behaves like GREP_OPTIONS
	# - space seperated list of arguments
	# - backslash before a spaces escapes the space seperation
	# - backslash before a backslash is interpreted as a single backslash
	# - all other backslashes are treated literally
	# e.g. ' a\ b c\\ \\d \\\e\' becomes '', 'a b', 'c\', '\d', '\\e\'
	if os.environ.get('SHUTIT_OPTIONS', None):
		env_args = os.environ['SHUTIT_OPTIONS']
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
	config_dict['build']['debug']    = args.debug
	config_dict['build']['tutorial'] = args.tutorial
	config_dict['build']['command_pause'] = float(args.pause)
	config_dict['build']['extra_configs'] = args.config
	config_dict['build']['show_config_only'] = args.sc
	config_dict['build']['show_depgraph_only'] = args.depgraph
	config_dict['build']['config_overrides'] = args.set
	config_dict['container']['docker_image'] = args.image_tag
	# Get module paths
	config_dict['host']['shutit_module_paths'] = args.shutit_module_path.split(':')
	if '.' not in config_dict['host']['shutit_module_paths']:
		if config_dict['build']['debug']:
			log('Working directory path not included, adding...')
			time.sleep(1)
		config_dict['host']['shutit_module_paths'].append('.')
	# Finished parsing args, tutorial stuff
	if config_dict['build']['tutorial']:
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
			\t\t""" + str(config_dict['host']['shutit_module_paths']) + """
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

def load_configs(config_dict):
	# Get root default config file
	default_config_file = os.path.join(shutit_global.shutit_main_dir, 'configs/defaults.cnf')
	configs = [default_config_file]
	# Now all the default configs we can see
	for path in config_dict['host']['shutit_module_paths']:
		if os.path.exists(path):
			for root, subFolders, files in os.walk(path):
				for f in files:
					if f == 'defaults.cnf':
						configs.append(root + '/' + f)
	# Add the shutit global host- and user-specific config file.
	configs.append(os.path.join(shutit_global.shutit_main_dir,
		'configs/' + socket.gethostname() + '_' + config_dict['host']['real_user'] + '.cnf'))
	# Then local host- and user-specific config file in this module.
	configs.append('configs/' + socket.gethostname() + '_' + config_dict['host']['real_user'] + '.cnf')
	# Add the local build.cnf
	configs.append('configs/build.cnf')
	# Get passed-in config(s)
	for config_file_name in config_dict['build']['extra_configs']:
		run_config_file = os.path.expanduser(config_file_name)
		if not os.path.isfile(run_config_file):
			fail('Did not recognise ' + run_config_file +
					' as a file - do you need to touch ' + run_config_file + '?')
		configs.append(run_config_file)
	# Image to use to start off. The script should be idempotent, so running it
	# on an already built image should be ok, and is advised to reduce diff space required.
	if config_dict['build']['tutorial'] or config_dict['build']['show_config_only']:
		msg = ''
		for c in configs:
			msg = msg + '\t\n' + c
			log('\t' + c)
		if config_dict['build']['tutorial']:
			pause_point(None,'\n' + msg + '\n\nLooking at config files in the '
				'above order (even if they do not exist - you may want to '
				'create them).\n\nIf you get a "Port already in use:" error, '
				'run:\n\n\tdocker ps -a | grep -w <port> | awk \'{print $1}\' '
				'| xargs docker kill\nor\n\tsudo docker ps -a | grep -w <port> '
				'| awk \'{print $1}\' | xargs sudo docker kill\n',
				print_input=False)

	# Interpret any config overrides, write to a file and add them to the
	# list of configs to be interpreted
	if config_dict['build']['config_overrides']:
		override_cp = ConfigParser.ConfigParser(None)
		for o_sec, o_key, o_val in config_dict['build']['config_overrides']:
			if not override_cp.has_section(o_sec):
				override_cp.add_section(o_sec)
			override_cp.set(o_sec, o_key, o_val)
		fd, name = tempfile.mkstemp()
		os.write(fd, print_config({ "config_parser": override_cp }))
		os.close(fd)
		configs.append(name)

	return get_configs(configs)

def load_shutit_modules(config_dict):
	if config_dict['build']['debug']:
		log('ShutIt module paths now: ')
		log(config_dict['host']['shutit_module_paths'])
		time.sleep(1)
	for shutit_module_path in config_dict['host']['shutit_module_paths']:
		load_all_from_path(shutit_module_path,config_dict)
	# Have we got anything to process?
	if len(shutit_global.shutit_modules) < 2 :
		log(shutit_global.shutit_modules)
		fail('No ShutIt modules in path: ' + ':'.join(config_dict['host']['shutit_module_paths']) + '. Check your --shutit_module_path setting.')

def print_config(config_dict):
	s = ''
	for section in config_dict['config_parser'].sections():
		s = s + '\n[' + section + ']\n'
		for item in config_dict['config_parser'].items(section):
			name = str(item[0])
			value = str(item[1])
			if name == 'password':
				value = 'XXX'
			s = s + name + ':' + value
			s = s + '\n'
	s = s + '\n'
	return s

# Inserts a pause in the expect session which allows the user to try things out
def pause_point(child,msg,print_input=True,expect='',config_dict=None,force=False):
	if config_dict is None: config_dict = shutit_global.config_dict
	if not config_dict['build']['interactive'] and not force:
		return
	# Sleep to try and make this the last thing we see before the prompt (not always the case)
	if child and print_input:
		print red('\n\nPause point:\n\n') + msg + red('\n\nYou can now type in commands and alter the state of the container.\nHit return to see the prompt\nHit CTRL and ] at the same time to continue with build\n\n')
		if print_input:
			if expect == '':
				expect = '@.*[#$]'
				print'\n\nexpect argument not supplied to pause_point, assuming "' + expect + '" is the regexp to expect\n\n'
		child.interact()
	else:
		print msg
		print red('\n\n[Hit return to continue]\n')
		raw_input('')


# Commit, tag, push, tar etc..
# expect must be a string
def do_repository_work(config_dict,expect,repo_name,repo_suffix='',docker_executable='docker',password=None,force=False):
	if config_dict['repository']['do_repository_work'] or force:
		child = get_pexpect_child('host_child')
		repository_server = config_dict['repository']['server']
		if repository_server != '':
			repository_server = repository_server + '/'
		if config_dict['repository']['user'] != '':
			repository_user = config_dict['repository']['user'] + '/'
			repository_user_tar = config_dict['repository']['user'] + '_'
		else:
			repository_user = ''
			repository_user_tar = ''
		if repo_suffix != '' and repo_name != '':
			repository = repository_server + repository_user + repo_name + '_' + repo_suffix
			repository_tar = repository_user_tar + repo_name + '_' + repo_suffix
		elif repo_suffix != '' and repo_name == '':
			repository = repository_server + repository_user + repo_suffix
			repository_tar = repository_user_tar + repo_suffix
		else:
			repository = repository_server + repository_user + repo_name
			repository_tar = repository_user_tar + repo_name
		# Slight pause due to race conditions seen.
		#time.sleep(0.3)
		res = send_and_expect(child,'SHUTIT_TMP_VAR=`' + docker_executable + ' commit ' + config_dict['container']['container_id'] + '`',[expect,'assword'],timeout=99999,check_exit=False)
		if res == 1:
			send_and_expect(child,config_dict['host']['password'],expect,check_exit=False,record_command=False)
		send_and_expect(child,'echo $SHUTIT_TMP_VAR && unset SHUTIT_TMP_VAR',expect,check_exit=False,record_command=False)
		image_id = child.after.split('\r\n')[1]
		if config_dict['repository']['suffix_date']:
			suffix_date = time.strftime(config_dict['repository']['suffix_format'])
			repository = repository + '_' + suffix_date
			repository_tar = repository_tar + '_' + suffix_date
		cmd = docker_executable + ' tag ' + image_id + ' ' + repository
		if image_id == None:
			fail('failed to commit with cmd: ' + cmd + ' could not determine image id')
		else:
			if config_dict['repository']['server'] == '' and len(repository) > 30:
				fail("""repository name: '""" + repository + """' too long. If using suffix_date consider shortening""")
			send_and_expect(child,cmd,expect,check_exit=False)
			if config_dict['repository']['tar'] == True:
				if config_dict['build']['tutorial']:
					pause_point(child,'We are now exporting the container to a bzipped tar file, as configured in \n[repository]\ntar:yes',print_input=False)
				bzfile = config_dict['host']['resources_dir'] + '/' + repository_tar + '.tar.bz2'
				log('\nDepositing bzip2 of exported container into ' + bzfile)
				res = send_and_expect(child,docker_executable + ' export ' + config_dict['container']['container_id'] + ' | bzip2 - > ' + bzfile,[expect,'assword'],timeout=99999)
				log(red('\nDeposited bzip2 of exported container into ' + bzfile))
				log(red('\nRun:\n\nbunzip2 -c ' + bzfile + ' | sudo docker import -\n\nto get this imported into docker.'))
				if res == 1:
					send_and_expect(child,password,expect,record_command=False)
			if config_dict['repository']['push'] == True:
				push_repository(child,repository,config_dict,docker_executable,expect)


# Return True if file exists, else False
def file_exists(child,filename,expect,directory=False):
	test = 'test %s %s' % ('-d' if directory is True else '-a', filename)
	send_and_expect(child,test+' && echo FILEXIST-""FILFIN || echo FILNEXIST-""FILFIN','-FILFIN',check_exit=False,record_command=False)
	res = get_re_from_child(child.before,'^(FILEXIST|FILNEXIST)$')
	ret = False
	if res == 'FILEXIST':
		ret = True
	elif res == 'FILNEXIST':
		pass
	else:
		# Change to log?
		print repr('before>>>>:%s<<<< after:>>>>%s<<<<' % (child.before, child.after))
		pause_point(child,'Did not see FIL(N)?EXIST in before')

	child.expect(expect)
	return ret

# Returns the file permission as an octal
def get_file_perms(child,filename,expect):
	cmd = 'stat -c %a ' + filename + r" | sed 's/.\(.*\)/\1/g'"
	send_and_expect(child,cmd,expect,check_exit=False,record_command=False)
	res = get_re_from_child(child.before,'([0-9][0-9][0-9])')
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
def add_line_to_file(child,line,filename,expect,match_regexp=None,truncate=False,force=False,literal=False):
	# assume we're going to add it
	res = '0'
	bad_chars    = '"'
	tmp_filename = '/tmp/' + str(random.getrandbits(32))
	if match_regexp == None and re.match('.*[' + bad_chars + '].*',line) != None:
		fail('Passed problematic character to add_line_to_file.\nPlease avoid using the following chars: ' + bad_chars + '\nor supply a match_regexp argument.\nThe line was:\n' + line)
	# truncate file if requested, or if the file doesn't exist
	if truncate:
		send_and_expect(child,'cat > ' + filename + ' <<< ""',expect,check_exit=False)
	elif not file_exists(child,filename,expect):
		# The above cat doesn't work so we touch the file if it doesn't exist already.
		send_and_expect(child,'touch ' + filename,expect,check_exit=False)
	elif not force:
		if literal:
			if match_regexp == None:
				send_and_expect(child,"""grep -w '^""" + line + """$' """ + filename + ' > ' + tmp_filename,expect,exit_values=['0','1'],record_command=False)
			else:
				send_and_expect(child,"""grep -w '^""" + match_regexp + """$' """ + filename + ' > ' + tmp_filename,expect,exit_values=['0','1'],record_command=False)
		else:
			if match_regexp == None:
				send_and_expect(child,'grep -w "^' + line + '$" ' + filename + ' > ' + tmp_filename,expect,exit_values=['0','1'],record_command=False)
			else:
				send_and_expect(child,'grep -w "^' + match_regexp + '$" ' + filename + ' > ' + tmp_filename,expect,exit_values=['0','1'],record_command=False)
		send_and_expect(child,'cat ' + tmp_filename + ' | wc -l',expect,exit_values=['0','1'],record_command=False,check_exit=False)
		res = get_re_from_child(child.before,'^([0-9]+)$')
	if res == '0' or force:
		send_and_expect(child,'cat >> ' + filename + """ <<< '""" + line + """'""",expect,check_exit=False)
		send_and_expect(child,'rm -f ' + tmp_filename,expect,exit_values=['0','1'],record_command=False)
		return True
	else:
		send_and_expect(child,'rm -f ' + tmp_filename,expect,exit_values=['0','1'],record_command=False)
		return False

# Get regular expression from lines
# Returns None if none matched.
def get_re_from_child(string,regexp,config_dict=None):
	if config_dict is None: config_dict = shutit_global.config_dict
	if config_dict['build']['debug']:
		log('get_re_from_child:')
		log(string)
		log(regexp)
	lines = string.split('\r\n')
	for l in lines:
		if config_dict['build']['debug']:
			log('trying: ' + l)
		match = re.match(regexp,l)
		if match != None:
			if config_dict['build']['debug']:
				log('returning: ' + match.group(1))
			return match.group(1)
	return None

# expect must be a string
def push_repository(child,repository,config_dict,docker_executable,expect):
	send = docker_executable + ' push ' + repository
	expect_list = ['Pushing','Buffering','Username:','Password:','Email:',expect]
	timeout=99999
	res = send_and_expect(child,send,expect_list,timeout=timeout,check_exit=False)
	while True:
		if res == 5:
			break
		elif res == 2:
			res = send_and_expect(child,config_dict['repository']['user'],expect_list,timeout=timeout,check_exit=False)
		elif res == 3:
			res = send_and_expect(child,config_dict['repository']['password'],expect_list,timeout=timeout,check_exit=False)
		elif res == 4:
			res = send_and_expect(child,config_dict['repository']['email'],expect_list,timeout=timeout,check_exit=False)
		else:
			res = child.expect(expect_list,timeout=timeout)

# Takes care of adding a line to everyone's bashrc
def add_to_bashrc(child,line,expect):
	add_line_to_file(child,line,'/etc/bash.bashrc',expect)
	res = add_line_to_file(child,line,'/etc/profile',expect)
	return res

# Set a pexpect child in the global dictionary by key.
def set_pexpect_child(key,child):
	shutit_global.pexpect_children.update({key:child})

# Get a pexpect child in the global dictionary by key.
def get_pexpect_child(key):
	return shutit_global.pexpect_children[key]

# dynamically import files within the same directory (in the end, the path)
#http://stackoverflow.com/questions/301134/dynamic-module-import-in-python
def load_all_from_path(path,config_dict):
	if os.path.abspath(path) == shutit_global.shutit_main_dir:
		return
	if os.path.exists(path):
		for root, subFolders, files in os.walk(path):
			for f in files:
				mod_name,file_ext = os.path.splitext(os.path.split(f)[-1])
				if file_ext.lower() == '.py':
					if config_dict['build']['debug']:
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


# Helper function to get preceding integer
# eg com.openbet == 1003189494
# >>> import binascii
# >>> abs(binascii.crc32('shutit.tk'))
# 782914092
def get_hash(string):
	return abs(binascii.crc32(string))


# Distro-independent install function.
# Takes a package name and runs
# Returns true if all ok (ie it's installed now), else false
def install(child,config_dict,package,expect,options=None,timeout=3600):
	if options is None: options = {}
	# TODO: maps of packages
	# TODO: config of maps of packages
	install_type = config_dict['container']['install_type']
	if install_type == 'apt':
		cmd = 'apt-get install'
		opts = options['apt'] if 'apt' in options else '-qq -y'
	elif install_type == 'yum':
		cmd = 'yum install'
		opts = options['yum'] if 'yum' in options else '-y'
	else:
		# Not handled
		return False
	send_and_expect(child,'%s %s %s' % (cmd,opts,package),expect,timeout=timeout)
	return True

# Distro-independent remove function.
# Takes a package name and runs purge/delete on it. Generally takes the most aggressive removal option.
# Returns true if all ok (ie it's installed now), else false
def remove(child,config_dict,package,expect,options=None):
	if options is None: options = {}
	# TODO: maps of packages
	# TODO: config of maps of packages
	install_type = config_dict['container']['install_type']
	if install_type == 'apt':
		cmd = 'apt-get purge'
		opts = options['apt'] if 'apt' in options else '-qq -y'
	elif install_type == 'yum':
		cmd = 'yum erase'
		opts = options['yum'] if 'yum' in options else '-y'
	else:
		# Not handled
		return False
	send_and_expect(child,'%s %s %s' % (cmd,opts,package),expect,check_exit=False)
	return True

# Return True if we can be sure the package is installed.
def package_installed(child,config_dict,package,expect):
	if config_dict['container']['install_type'] == 'apt':
		send_and_expect(child,"""dpkg -l | awk '{print $2}' | grep "^""" + package + """$" | wc -l""",expect,check_exit=False,record_command=False)
	elif config_dict['container']['install_type'] == 'yum':
		send_and_expect(child,"""yum list installed | awk '{print $1}' | grep "^""" + package + """$" | wc -l""",expect,check_exit=False,record_command=False)
	else:
		return False
	if get_re_from_child(child.before,'^([0-9]+)$') != '0':
		return True
	else:
		return False


# Fails if distro could not be determined.
# Should be called with the container is started up.
def get_distro_info(child,outer_expect,config_dict):
	config_dict['container']['install_type']      = ''
	config_dict['container']['distro']            = ''
	config_dict['container']['distro_version']    = ''
	install_type_map = {'ubuntu':'apt','debian':'apt','red hat':'yum','centos':'yum','fedora':'yum'}
	handle_login(child,config_dict,'tmp_prompt')
	if file_exists(child,config_dict['build']['cidfile'],config_dict['expect_prompts']['tmp_prompt']):
		fail('Did not start up container. If you got a "port in use" error, try:\n\n' + config_dict['host']['docker_executable'] + ' ps -a | grep ' + config_dict['container']['ports'] + ' | awk \'{print $1}\' | xargs ' + config_dict['host']['docker_executable'] + ' kill\n\n')
	for key in install_type_map.keys():
		# Use grep (not egrep) because it's likely installed _everywhere_ by default.
		child.sendline('cat /etc/issue | grep -i "' + key + '" | wc -l')
		child.expect(config_dict['expect_prompts']['tmp_prompt'])
		if get_re_from_child(child.before,'^([0-9]+)$') == '1':
			config_dict['container']['distro']       = key
			config_dict['container']['install_type'] = install_type_map[key]
			break
	set_password(child,config_dict,config_dict['expect_prompts']['tmp_prompt'],config_dict['container']['password'])
	if config_dict['container']['install_type'] == 'apt':
		config_dict['expect_prompts']['real_user_prompt']        = '\r\n.*?' + config_dict['host']['real_user'] + '@.*:'
		send_and_expect(child,'export DEBIAN_FRONTEND=noninteractive',config_dict['expect_prompts']['tmp_prompt'])
		send_and_expect(child,'apt-get update',config_dict['expect_prompts']['tmp_prompt'],timeout=9999,check_exit=False)
		send_and_expect(child,'dpkg-divert --local --rename --add /sbin/initctl',config_dict['expect_prompts']['tmp_prompt'])
		send_and_expect(child,'ln -f -s /bin/true /sbin/initctl',config_dict['expect_prompts']['tmp_prompt'])
	elif config_dict['container']['install_type'] == 'yum':
		config_dict['expect_prompts']['real_user_prompt']        = '\r\n.*?' + config_dict['host']['real_user'] + '@.*:'
		install(child,config_dict,'passwd',config_dict['expect_prompts']['tmp_prompt'])
		send_and_expect(child,'yum update -y',config_dict['expect_prompts']['tmp_prompt'],timeout=9999)
	if config_dict['container']['install_type'] == '' or config_dict['container']['distro'] == '':
		fail('Could not determine Linux distro information. Please inform maintainers.')
	handle_revert_prompt(child,outer_expect,'tmp_prompt')

def set_password(child,config_dict,expect,password):
	if config_dict['container']['install_type'] == 'apt':
		send_and_expect(child,'passwd','Enter new',check_exit=False)
		send_and_expect(child,password,'Retype new',check_exit=False,record_command=False)
		send_and_expect(child,password,expect,record_command=False)
	elif config_dict['container']['install_type'] == 'yum':
		send_and_expect(child,'passwd','ew password',check_exit=False,record_command=False)
		send_and_expect(child,password,'ew password',check_exit=False,record_command=False)
		send_and_expect(child,password,expect,record_command=False)
	handle_login(child,config_dict,'password_tmp_prompt')
	send_and_expect(child,'/bin/true',config_dict['expect_prompts']['password_tmp_prompt'],record_command=False)
	handle_revert_prompt(child,expect,'password_tmp_prompt')


# Returns prompt expected
def handle_login(child,config_dict,prompt_name):
	local_prompt = 'SHUTIT_TMP_PROMPT_' + prompt_name + '#' + str(random.getrandbits(32))
	config_dict['expect_prompts'][prompt_name] = '\r\n' + local_prompt
	send_and_expect(child,'SHUTIT_BACKUP_PS1_' + prompt_name + """=$PS1 && export SHUTIT_PROMPT_COMMAND_BACKUP_""" + prompt_name + """=$PROMPT_COMMAND""" + prompt_name + """ && PS1='""" + local_prompt + """' && unset PROMPT_COMMAND""",config_dict['expect_prompts'][prompt_name],record_command=False,fail_on_empty_before=False)

def handle_revert_prompt(child,expect,prompt_name):
	send_and_expect(child,"""PS1="${SHUTIT_BACKUP_PS1_""" + prompt_name + """}" && unset SHUTIT_PROMPT_COMMAND_BACKUP_""" + prompt_name + """ && unset SHUTIT_BACKUP_PS1_""" + prompt_name,expect,check_exit=False,record_command=False,fail_on_empty_before=False)



# Determine whether a user_id for a user is available
def is_user_id_available(child,user_id,expect):
	send_and_expect(child,'cut -d: -f3 /etc/paswd | grep -w ^' + user_id + '$ | wc -l',expect,check_exit=False,record_command=False)
	if get_re_from_child(child.before,'^([0-9]+)$') == '1':
		return False
	else:
		return True

# Sets up a base prompt
def setup_prompt(child,config_dict,prefix,prompt_name):
	local_prompt = prefix + str(random.getrandbits(32))
	child.sendline('SHUTIT_BACKUP_PS1=$PS1 && unset PROMPT_COMMAND && PS1="' + local_prompt + '"')
	config_dict['expect_prompts'][prompt_name] = '\r\n' + local_prompt
	child.expect(config_dict['expect_prompts'][prompt_name])


def print_modules(shutit_map,shutit_id_list,config_dict):
	s = ''
	s = s + 'Modules: \n'
	s = s + '\tRun order\tBuild\tRemove\tModule ID\n'
	for mid in shutit_id_list:
		s = s + ('\t' + str(shutit_map[mid].run_order) + '\t\t' +
			str(config_dict[mid]['build']) + '\t' +
			str(config_dict[mid]['remove']) + '\t' +
			mid + '\n')
	return s

# Build report
def build_report(msg=''):
	s = ''
	s = s + '################################################################################\n'
	s = s + '# COMMAND HISTORY BEGIN ' + shutit_global.config_dict['build']['build_id'] + '\n'
	s = s + '################################################################################\n'
	for c in shutit_global.shutit_command_history:
		s = s + c + '\n'
	s = s + '# COMMAND HISTORY END ' + shutit_global.config_dict['build']['build_id'] + '\n'
	s = s + '################################################################################\n'
	s = s + '################################################################################\n'
	s = s + '# BUILD REPORT FOR BUILD BEGIN ' + shutit_global.config_dict['build']['build_id'] + '\n'
	s = s + '# ' + msg + '\n'
	s = s + '################################################################################\n'
	if shutit_global.config_dict['build']['report'] != '':
		s = s + shutit_global.config_dict['build']['report'] + '\n'
	else:
		s = s + '# Nothing to report\n'
	s = s + '# BUILD REPORT FOR BUILD END ' + shutit_global.config_dict['build']['build_id'] + '\n'
	s = s + '################################################################################\n'
	return s
