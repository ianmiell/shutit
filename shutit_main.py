#!/usr/bin/env python
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

"""ShutIt is a means of building stateless target hosts in a flexible and predictable way.
"""


from shutit_module import ShutItModule, ShutItException, ShutItFailException
import ConfigParser
import shutit_util
import urllib
import shutit_global
import sys
import os
import json
import re
import signal
from distutils import spawn


def module_ids(shutit, rev=False):
	"""Gets a list of module ids guaranteed to be sorted by run_order, ignoring conn modules
	(run order < 0).
	"""
	ids = sorted(shutit.shutit_map.keys(),key=lambda module_id: shutit.shutit_map[module_id].run_order)
	if rev:
		return list(reversed(ids))
	else:
		return ids


def allowed_module_ids(shutit, rev=False):
	"""Gets a list of module ids that are allowed to be run,
	guaranteed to be sorted by run_order, ignoring conn modules
	(run order < 0).
	"""
	module_ids_list = module_ids(shutit,rev)
	allowed_module_ids = []
	for module_id in module_ids_list:
		if allowed_image(shutit,module_id):
			allowed_module_ids.append(module_id) 
	return allowed_module_ids


def disallowed_module_ids(shutit, rev=False):
	"""Gets a list of disallowed module ids that are not allowed to be run,
	guaranteed to be sorted by run_order, ignoring conn modules
	(run order < 0).
	"""
	module_ids_list = module_ids(shutit,rev)
	disallowed_module_ids = []
	for module_id in module_ids_list:
		if not allowed_image(shutit,module_id):
			disallowed_module_ids.append(module_id) 
	return disallowed_module_ids


def print_modules(shutit):
	"""Returns a string table representing the modules in the ShutIt module map.
	"""
	cfg = shutit.cfg
	string = ''
	string = string + 'Modules: \n'
	string = string + '    Run order    Build    Remove    Module ID\n'
	for module_id in module_ids(shutit):
		string = string + ('    ' + str(shutit.shutit_map[module_id].run_order) +
		                   '        ' +
		                   str(cfg[module_id]['shutit.core.module.build']) + '    ' +
		                   str(cfg[module_id]['shutit.core.module.remove']) + '    ' +
		                   module_id + '\n')
	return string


# run_order of -1 means 'stop everything'
def stop_all(shutit, run_order=-1):
	"""Runs stop method on all modules less than the passed-in run_order.
	Used when target is exporting itself mid-build, so we clean up state
	before committing run files etc.
	"""
	cfg = shutit.cfg
	if cfg['build']['interactive'] >= 3:
		print('\nRunning stop on all modules' + \
			shutit_util.colour('32', '\n\n[Hit return to continue]'))
		shutit_util.util_raw_input(shutit=shutit)
	# sort them so they're stopped in reverse order
	for module_id in module_ids(shutit, rev=True):
		shutit_module_obj = shutit.shutit_map[module_id]
		if run_order == -1 or shutit_module_obj.run_order <= run_order:
			if is_installed(shutit, shutit_module_obj):
				if not shutit_module_obj.stop(shutit):
					shutit.fail('failed to stop: ' + \
						module_id, child=shutit.pexpect_children['target_child'])


# Start all apps less than the supplied run_order
def start_all(shutit, run_order=-1):
	"""Runs start method on all modules less than the passed-in run_order.
	Used when target is exporting itself mid-build, so we can export a clean
	target and still depended-on modules running if necessary.
	"""
	cfg = shutit.cfg
	if cfg['build']['interactive'] >= 3:
		print('\nRunning start on all modules' + 
			shutit_util.colour('32', '\n\n[Hit return to continue]\n'))
		shutit_util.util_raw_input(shutit=shutit)
	# sort them so they're started in order
	for module_id in module_ids(shutit):
		shutit_module_obj = shutit.shutit_map[module_id]
		if run_order == -1 or shutit_module_obj.run_order <= run_order:
			if is_installed(shutit, shutit_module_obj):
				if not shutit_module_obj.start(shutit):
					shutit.fail('failed to start: ' + module_id, \
						child=shutit.pexpect_children['target_child'])


def is_installed(shutit, shutit_module_obj):
	"""Returns true if this module is installed.
	Uses cache where possible.
	"""
	cfg = shutit.cfg
	# Cache first
	cfg = shutit.cfg
	if shutit_module_obj.module_id in cfg['environment'][cfg['build']['current_environment_id']]['modules_installed']:
		return True
	if shutit_module_obj.module_id in cfg['environment'][cfg['build']['current_environment_id']]['modules_not_installed']:
		return False
	# Is it installed?
	if shutit_module_obj.is_installed(shutit):
		cfg['environment'][cfg['build']['current_environment_id']]['modules_installed'].append(shutit_module_obj.module_id)
		return True
	# If not installed, and not in cache, add it.
	else:
		if shutit_module_obj.module_id not in cfg['environment'][cfg['build']['current_environment_id']]['modules_not_installed']:
			cfg['environment'][cfg['build']['current_environment_id']]['modules_not_installed'].append(shutit_module_obj.module_id)
		return False


def is_to_be_built_or_is_installed(shutit, shutit_module_obj):
	"""Returns true if this module is configured to be built,
	or if it is already installed.
	"""
	cfg = shutit.cfg
	if cfg[shutit_module_obj.module_id]['shutit.core.module.build']:
		return True
	return is_installed(shutit, shutit_module_obj)


def is_ready(shutit, shutit_module_obj):
	"""Returns true if this module is ready to be built.
	Caches the result (as it's assumed not to change during the build).
	"""
	cfg = shutit.cfg
	if shutit_module_obj.module_id in cfg['environment'][cfg['build']['current_environment_id']]['modules_ready']:
		shutit.log('is_ready: returning True from cache')
		return True
	ready = shutit_module_obj.check_ready(shutit)
	if ready:
		cfg['environment'][cfg['build']['current_environment_id']]['modules_ready'].append(shutit_module_obj.module_id)
		return True
	else:
		return False
	
		


def init_shutit_map(shutit):
	"""Initializes the module map of shutit based on the modules
	we have gathered.

	Checks we have core modules
	Checks for duplicate module details.
	Sets up common config.
	Sets up map of modules.
	"""
	cfg = shutit.cfg

	modules = shutit.shutit_modules

	# Have we got anything to process outside of special modules?
	if len([mod for mod in modules if mod.run_order > 0]) < 1:
		shutit.log(modules)
		path = ':'.join(cfg['host']['shutit_module_path'])
		shutit.log('\nIf you are new to ShutIt, see:\n\n\thttp://ianmiell.github.io/shutit/\n\nor try running\n\n\tshutit skeleton\n\n',code=31,prefix=False,force_stdout=True)
		if path == '':
			shutit.fail('No ShutIt modules aside from core ones found and no ShutIt' + 
			            ' module path given. ' + 
			            '\nDid you set --shutit_module_path/-m wrongly?\n')
		elif path == '.':
			shutit.fail('No modules aside from core ones found and no ShutIt' + 
			            ' module path given apart from default (.).\n\n- Did you' + 
			            ' set --shutit_module_path/-m?\n- Is there a STOP* file' + 
			            ' in your . dir?\n')
		else:
			shutit.fail('No modules aside from core ones found and no ShutIt ' +
			            'modules in path:\n\n' + path +
			            '\n\nor their subfolders. Check your ' + 
			            '--shutit_module_path/-m setting and check that there are ' + 
			            'ShutIt modules below without STOP* files in any relevant ' + 
			            'directories.\n')

	shutit.log('PHASE: base setup', code='32')
	if cfg['build']['interactive'] >= 3:
		shutit.log('\nChecking to see whether there are duplicate module ids ' +
		           'or run orders in the visible modules.', force_stdout=True)
		shutit.log('\nModules I see are:\n', force_stdout=True)
		for module in modules:
			shutit.log(module.module_id, force_stdout=True, code='32')
		shutit.log('\n', force_stdout=True)

	run_orders = {}
	has_core_module = False
	for module in modules:
		assert isinstance(module, ShutItModule)
		if module.module_id in shutit.shutit_map:
			shutit.fail('Duplicated module id: ' + module.module_id + 
			            '\n\nYou may want to check your --shutit_module_path setting')
		if module.run_order in run_orders:
			shutit.fail('Duplicate run order: ' + str(module.run_order) +
			            ' for ' + module.module_id + ' and ' +
			            run_orders[module.run_order].module_id + 
			            '\n\nYou may want to check your --shutit_module_path setting')
		if module.run_order == 0:
			has_core_module = True
		shutit.shutit_map[module.module_id] = run_orders[module.run_order] = module

	if not has_core_module:
		shutit.fail('No module with run_order=0 specified! This is required.')

	if cfg['build']['interactive'] >= 3:
		print(shutit_util.colour('32', 'Module id and run order checks OK' + 
		                  '\n\n[Hit return to continue]\n'))
		shutit_util.util_raw_input(shutit=shutit)


def config_collection(shutit):
	"""Collect core config from config files for all seen modules.
	"""
	shutit.log('In config_collection')
	cfg = shutit.cfg
	for module_id in module_ids(shutit):
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
							for mod, opt, val in cfg['build']['config_overrides']:
								# skip overrides
								if mod == module_id and opt == option:
									override = True
							if override:
								continue
							value = config_parser.get(section,option)
							if option == 'shutit.core.module.allowed_images':
								value = json.loads(value)
							shutit.get_config(module_id, option,
							                  value, forcedefault=True)
		# ifneeded will (by default) only take effect if 'build' is not
		# specified. It can, however, be forced to a value, but this
		# should be unusual.
		if cfg[module_id]['shutit.core.module.build'] is None:
			shutit.get_config(module_id, 'shutit.core.module.build_ifneeded', True, boolean=True)
			cfg[module_id]['shutit.core.module.build'] = False
		else:
			shutit.get_config(module_id, 'shutit.core.module.build_ifneeded', False, boolean=True)


def config_collection_for_built(shutit):
	"""Collect configuration for modules that are being built.
	When this is called we should know what's being built (ie after
	dependency resolution).
	"""
	cfg = shutit.cfg
	shutit.log('In config_collection_for_built')
	cfg = shutit.cfg
	for module_id in module_ids(shutit):
		# Get the config even if installed or building (may be needed in other
		# hooks, eg test).
		if (is_to_be_built_or_is_installed(shutit, shutit.shutit_map[module_id]) and
			not shutit.shutit_map[module_id].get_config(shutit)):
				shutit.fail(module_id + ' failed on get_config')
		# Collect the build.cfg if we are building here.
		# If this file exists, process it.
		if cfg[module_id]['shutit.core.module.build']:
			module = shutit.shutit_map[module_id]
			cfg_file = os.path.dirname(module.__module_file) + '/configs/build.cnf'
			if os.path.isfile(cfg_file):
				# use shutit.get_config, forcing the passed-in default
				config_parser = ConfigParser.ConfigParser()
				config_parser.read(cfg_file)
				for section in config_parser.sections():
					if section == module_id:
						for option in config_parser.options(section):
							override = False
							for mod, opt, val in cfg['build']['config_overrides']:
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
							shutit.get_config(module_id, option,
							                  value, forcedefault=True)
	# Check the allowed_images against the base_image
	passed = True
	for module_id in module_ids(shutit):
		if (cfg[module_id]['shutit.core.module.build'] and
		   (cfg[module_id]['shutit.core.module.allowed_images'] and
		    cfg['target']['docker_image'] not in cfg[module_id]['shutit.core.module.allowed_images'])):
			if not allowed_image(shutit,module_id):
				passed = False
				print('\n\nWARNING!\n\nAllowed images for ' + module_id + ' are: ' +
				      str(cfg[module_id]['shutit.core.module.allowed_images']) +
				      ' but the configured image is: ' +
				      cfg['target']['docker_image'] +
				      '\n\nIs your shutit_module_path set correctly?' +
				      '\n\nIf you want to ignore this, ' + 
				      'pass in the --ignoreimage flag to shutit.\n\n')
	if not passed:
		if cfg['build']['imageerrorok']:
			# useful for test scripts
			print('Exiting on allowed images error, with return status 0')
			sys.exit(0)
		else:
			raise ShutItFailException('Allowed images checking failed')


def allowed_image(shutit,module_id):
	"""Given a module id and a shutit object, determine whether the image is allowed to be built.
	"""
	cfg = shutit.cfg
	shutit.log("In allowed_image: " + module_id)
	cfg = shutit.cfg
	if cfg['build']['ignoreimage']:
		shutit.log("ignoreimage == true, returning true" + module_id,force_stdout=True)
		return True
	shutit.log(str(cfg[module_id]['shutit.core.module.allowed_images']))
	if cfg[module_id]['shutit.core.module.allowed_images']:
		# Try allowed images as regexps
		for regexp in cfg[module_id]['shutit.core.module.allowed_images']:
			if not shutit_util.check_regexp(regexp):
				shutit.fail('Illegal regexp found in allowed_images: ' + regexp)
			if re.match('^' + regexp + '$', cfg['target']['docker_image']):
				return True
	return False
	


def conn_target(shutit):
	"""Connect to the target.
	"""
	cfg = shutit.cfg
	conn_module = None
	cfg = shutit.cfg
	for mod in shutit.conn_modules:
		if mod.module_id == cfg['build']['conn_module']:
			conn_module = mod
			break
	if conn_module is None:
		shutit.fail('Couldn\'t find conn_module ' + cfg['build']['conn_module'])

	# Set up the target in pexpect.
	if cfg['build']['interactive'] >= 3:
		print('\nRunning the conn module (' +
			shutit.shutit_main_dir + '/shutit_setup.py)' + shutit_util.colour('32',
				'\n\n[Hit return to continue]\n'))
		shutit_util.util_raw_input(shutit=shutit)
	conn_module.get_config(shutit)
	conn_module.build(shutit)


def finalize_target(shutit):
	"""Finalize the target using the core finalize method.
	"""
	cfg = shutit.cfg
	shutit.pause_point('\nFinalizing the target module (' +
		shutit.shutit_main_dir + '/shutit_setup.py)', print_input=False, level=3)
	# Can assume conn_module exists at this point
	for mod in shutit.conn_modules:
		if mod.module_id == cfg['build']['conn_module']:
			conn_module = mod
			break
	conn_module.finalize(shutit)


# Once we have all the modules, then we can look at dependencies.
# Dependency validation begins.
def resolve_dependencies(shutit, to_build, depender):
	"""Add any required dependencies.
	"""
	shutit.log('In resolve_dependencies')
	cfg = shutit.cfg
	for dependee_id in depender.depends_on:
		dependee = shutit.shutit_map.get(dependee_id)
		# Don't care if module doesn't exist, we check this later
		if (dependee and dependee not in to_build
		    and cfg[dependee_id]['shutit.core.module.build_ifneeded']):
			to_build.append(dependee)
			cfg[dependee_id]['shutit.core.module.build'] = True
	return True


def check_dependee_exists(shutit, depender, dependee, dependee_id):
	"""Checks whether a depended-on module is available.
	"""
	cfg = shutit.cfg
	# If the module id isn't there, there's a problem.
	if dependee == None:
		return ('module: \n\n' + dependee_id + '\n\nnot found in paths: ' +
		        str(cfg['host']['shutit_module_path']) +
		        ' but needed for ' + depender.module_id +
		        '\nCheck your --shutit_module_path setting and ensure that ' +
		        'all modules configured to be built are in that path setting, ' +
		        'eg "--shutit_module_path /path/to/other/module/:."\n\n' +
		        'Also check that the module is configured to be built with ' +
		        'the correct module id in that module\'s configs/build.cnf file.' +
		        '\n\nSee also help.')


def check_dependee_build(shutit, depender, dependee, dependee_id):
	"""Checks whether a depended on module is configured to be built.
	"""
	cfg = shutit.cfg
	# If depender is installed or will be installed, so must the dependee
	cfg = shutit.cfg
	if not (cfg[dependee.module_id]['shutit.core.module.build'] or
	        is_to_be_built_or_is_installed(shutit,dependee)):
		return ('depender module id:\n\n[' + depender.module_id + ']\n\n' +
		        'is configured: "build:yes" or is already built ' +
		        'but dependee module_id:\n\n[' + dependee_id + ']\n\n' +
		        'is not configured: "build:yes"')


def check_dependee_order(_shutit, depender, dependee, dependee_id):
	"""Checks whether run orders are in the appropriate order.
	"""
	# If it depends on a module id, then the module id should be higher up
	# in the run order.
	if dependee.run_order > depender.run_order:
		return ('depender module id:\n\n' + depender.module_id +
		        '\n\n(run order: ' + str(depender.run_order) + ') ' +
		        'depends on dependee module_id:\n\n' + dependee_id +
		        '\n\n(run order: ' + str(dependee.run_order) + ') ' +
		        'but the latter is configured to run after the former')


def make_dep_graph(depender):
	"""Returns a digraph string fragment based on the passed-in module 
	"""
	digraph = ''
	for dependee_id in depender.depends_on:
		digraph = (digraph + '"' + depender.module_id + '"->"' +
		   dependee_id + '";\n')
	return digraph


def check_deps(shutit):
	"""Dependency checking phase is performed in this method.
	"""
	cfg = shutit.cfg
	shutit.log('PHASE: dependencies', code='32')
	shutit.pause_point('\nNow checking for dependencies between modules',
	                   print_input=False, level=3)
	# Get modules we're going to build
	to_build = [
		shutit.shutit_map[module_id] for module_id in shutit.shutit_map
		if module_id in cfg and cfg[module_id]['shutit.core.module.build']
	]
	# Add any deps we may need by extending to_build and altering cfg
	for module in to_build:
		resolve_dependencies(shutit, to_build, module)

	# Dep checking
	def err_checker(errs, triples):
		"""Collate error information.
		""" 
		new_triples = []
		for err, triple in zip(errs, triples):
			if not err:
				new_triples.append(triple)
				continue
			found_errs.append(err)
		return new_triples

	found_errs = []
	triples    = []
	for depender in to_build:
		for dependee_id in depender.depends_on:
			triples.append((depender, shutit.shutit_map.get(dependee_id),
							dependee_id))

	triples = err_checker([
		check_dependee_exists(shutit, depender, dependee, dependee_id)
		for depender, dependee, dependee_id in triples
	], triples)
	triples = err_checker([
		check_dependee_build(shutit, depender, dependee, dependee_id)
		for depender, dependee, dependee_id in triples
	], triples)
	triples = err_checker([
		check_dependee_order(shutit, depender, dependee, dependee_id)
		for depender, dependee, dependee_id in triples
	], triples)

	if found_errs:
		return [(err,) for err in found_errs]

	if cfg['build']['debug']:
		shutit.log('Modules configured to be built (in order) are: ', code='32')
		for module_id in module_ids(shutit):
			module = shutit.shutit_map[module_id]
			if cfg[module_id]['shutit.core.module.build']:
				shutit.log(module_id + '    ' + str(module.run_order), code='32')
		shutit.log('\n', code='32')

	return []


def check_conflicts(shutit):
	"""Checks for any conflicts between modules configured to be built.
	"""
	cfg = shutit.cfg
	# Now consider conflicts
	shutit.log('PHASE: conflicts', code='32')
	errs = []
	shutit.pause_point('\nNow checking for conflicts between modules',
	                   print_input=False, level=3)
	for module_id in module_ids(shutit):
		if not cfg[module_id]['shutit.core.module.build']:
			continue
		conflicter = shutit.shutit_map[module_id]
		for conflictee in conflicter.conflicts_with:
			# If the module id isn't there, there's no problem.
			conflictee_obj = shutit.shutit_map.get(conflictee)
			if conflictee_obj == None:
				continue
			if ((cfg[conflicter.module_id]['shutit.core.module.build'] or
			     is_to_be_built_or_is_installed(shutit,conflicter)) and
			    (cfg[conflictee_obj.module_id]['shutit.core.module.build'] or
			     is_to_be_built_or_is_installed(shutit,conflictee_obj))):
			    errs.append(('conflicter module id: ' + conflicter.module_id +
	                    ' is configured to be built or is already built but ' +
	                    'conflicts with module_id: ' + conflictee_obj.module_id,))
	return errs


def check_ready(shutit, throw_error=True):
	"""Check that all modules are ready to be built, calling check_ready on
	each of those configured to be built and not already installed
	(see is_installed).
	"""
	cfg = shutit.cfg
	shutit.log('PHASE: check_ready', code='32')
	errs = []
	shutit.pause_point('\nNow checking whether we are ready to build modules' + 
	                   ' configured to be built',
	                   print_input=False, level=3)
	# Find out who we are to see whether we need to log in and out or not. 
	for module_id in module_ids(shutit):
		module = shutit.shutit_map[module_id]
		shutit.log('considering check_ready (is it ready to be built?): ' +
		           module_id, code='32')
		if cfg[module_id]['shutit.core.module.build'] and module.module_id not in cfg['environment'][cfg['build']['current_environment_id']]['modules_ready'] and not is_installed(shutit,module):
			shutit.log('checking whether module is ready to build: ' + module_id,
			           code='32')
			shutit.login(prompt_prefix=module_id,command='bash')
			# Move to the directory so context is correct (eg for checking for
			# the existence of files needed for build)
			revert_dir = os.getcwd()
			cfg['environment'][cfg['build']['current_environment_id']]['module_root_dir'] = os.path.dirname(module.__module_file)
			shutit.chdir(cfg['environment'][cfg['build']['current_environment_id']]['module_root_dir'])
			if not is_ready(shutit, module) and throw_error:
				errs.append((module_id + ' not ready to install.\nRead the ' +
				            'check_ready function in the module,\nor log ' + 
				            'messages above to determine the issue.\n\n',
				            shutit.pexpect_children['target_child']))
			shutit.logout()
			shutit.chdir(revert_dir)
	return errs


def do_remove(shutit):
	"""Remove modules by calling remove method on those configured for removal.
	"""
	cfg = shutit.cfg
	# Now get the run_order keys in order and go.
	shutit.log('PHASE: remove', code='32')
	shutit.pause_point('\nNow removing any modules that need removing',
					   print_input=False, level=3)
	# Login at least once to get the exports.
	for module_id in module_ids(shutit):
		module = shutit.shutit_map[module_id]
		shutit.log('considering whether to remove: ' + module_id, code='32')
		if cfg[module_id]['shutit.core.module.remove']:
			shutit.log('removing: ' + module_id, code='32')
			shutit.login(prompt_prefix=module_id,command='bash')
			if not module.remove(shutit):
				shutit.log(print_modules(shutit), code='31')
				shutit.fail(module_id + ' failed on remove',
				child=shutit.pexpect_children['target_child'])
			else:
				if cfg['build']['delivery'] in ('docker','dockerfile'):
					# Create a directory and files to indicate this has been removed.
					shutit.send(' mkdir -p ' + cfg['build']['build_db_dir'] + '/module_record/' + module.module_id + ' && rm -f ' + cfg['build']['build_db_dir'] + '/module_record/' + module.module_id + '/built && touch ' + cfg['build']['build_db_dir'] + '/module_record/' + module.module_id + '/removed')
					# Remove from "installed" cache
					if module.module_id in cfg['environment'][cfg['build']['current_environment_id']]['modules_installed']:
						cfg['environment'][cfg['build']['current_environment_id']]['modules_installed'].remove(module.module_id)
					# Add to "not installed" cache
					cfg['environment'][cfg['build']['current_environment_id']]['modules_not_installed'].append(module.module_id)
			shutit.logout()
			


def build_module(shutit, module):
	"""Build passed-in module.
	"""
	cfg = shutit.cfg
	shutit.log('building: ' + module.module_id + ' with run order: ' +
			   str(module.run_order), code='32')
	cfg['build']['report'] = (cfg['build']['report'] + '\nBuilding: ' +
	                          module.module_id + ' with run order: ' +
	                          str(module.run_order))
	if not module.build(shutit):
		shutit.fail(module.module_id + ' failed on build',
		            child=shutit.pexpect_children['target_child'])
	else:
		if cfg['build']['delivery'] in ('docker','dockerfile'):
			# Create a directory and files to indicate this has been built.
			shutit.send(' mkdir -p ' + cfg['build']['build_db_dir'] + '/module_record/' + module.module_id + ' && touch ' + cfg['build']['build_db_dir'] + '/module_record/' + module.module_id + '/built && rm -f ' + cfg['build']['build_db_dir'] + '/module_record/' + module.module_id + '/removed')
		# Put it into "installed" cache
		cfg['environment'][cfg['build']['current_environment_id']]['modules_installed'].append(module.module_id)
		# Remove from "not installed" cache
		if module.module_id in cfg['environment'][cfg['build']['current_environment_id']]['modules_not_installed']:
			cfg['environment'][cfg['build']['current_environment_id']]['modules_not_installed'].remove(module.module_id)
	shutit.pause_point('\nPausing to allow inspect of build for: ' +
	                   module.module_id, print_input=True, level=2)
	cfg['build']['report'] = (cfg['build']['report'] + '\nCompleted module: ' +
	                          module.module_id)
	if cfg[module.module_id]['shutit.core.module.tag'] or cfg['build']['interactive'] >= 3:
		shutit.log(shutit_util.build_report(shutit, '#Module:' + module.module_id),
		           code='32')
	if (not cfg[module.module_id]['shutit.core.module.tag'] and
		cfg['build']['interactive'] >= 2):
		shutit.log("\n\nDo you want to save state now we\'re at the " +
		           "end of this module? (" + module.module_id +
		           ") (input y/n)", force_stdout=True, code='32')
		cfg[module.module_id]['shutit.core.module.tag'] = (shutit_util.util_raw_input(shutit=shutit,default='y') == 'y')
	if cfg[module.module_id]['shutit.core.module.tag'] or cfg['build']['tag_modules']:
		shutit.log(module.module_id +
		           ' configured to be tagged, doing repository work',
		           force_stdout=True)
		# Stop all before we tag to avoid file changing errors,
		# and clean up pid files etc..
		stop_all(shutit, module.run_order)
		shutit.do_repository_work(str(module.module_id) + '_' + 
		                          str(module.run_order),
		                          password=cfg['host']['password'],
		                          docker_executable=cfg['host']['docker_executable'],
		                          force=True)
		# Start all after we tag to ensure services are up as expected.
		start_all(shutit, module.run_order)
	if cfg['build']['interactive'] >= 2:
		shutit.log("\n\nDo you want to stop interactive mode? (input y/n)\n",
		           force_stdout=True,code='32')
		if shutit_util.util_raw_input(shutit=shutit,default='y') == 'y':
			cfg['build']['interactive'] = 0


def do_build(shutit):
	"""Runs build phase, building any modules that we've determined
	need building.
	"""
	cfg = shutit.cfg
	shutit.log('PHASE: build, repository work', code='32')
	shutit.log(shutit_util.print_config(cfg))
	if cfg['build']['interactive'] >= 3:
		print ('\nNow building any modules that need building' +
	 	       shutit_util.colour('32', '\n\n[Hit return to continue]\n'))
		shutit_util.util_raw_input(shutit=shutit)
	module_id_list = module_ids(shutit)
	if cfg['build']['deps_only']:
		module_id_list_build_only = filter(lambda x: cfg[x]['shutit.core.module.build'], module_id_list)
	for module_id in module_id_list:
		module = shutit.shutit_map[module_id]
		shutit.log('considering whether to build: ' + module.module_id,
		           code='32')
		if cfg[module.module_id]['shutit.core.module.build']:
			if cfg['build']['delivery'] not in module.ok_delivery_methods:
				shutit.fail('Module: ' + module.module_id + ' can only be built with one of these --delivery methods: ' + str(module.ok_delivery_methods) + '\nSee shutit build -h for more info, or try adding: --delivery <method> to your shutit invocation')
			if is_installed(shutit,module):
				cfg['build']['report'] = (cfg['build']['report'] +
				    '\nBuilt already: ' + module.module_id +
				    ' with run order: ' + str(module.run_order))
			else:
				# We move to the module directory to perform the build, returning immediately afterwards.
				if cfg['build']['deps_only'] and module_id == module_id_list_build_only[-1]:
					# If this is the last module, and we are only building deps, stop here.
					cfg['build']['report'] = (cfg['build']['report'] + '\nSkipping: ' +
					    module.module_id + ' with run order: ' + str(module.run_order) +
					    '\n\tas this is the final module and we are building dependencies only')
				else:
					revert_dir = os.getcwd()
					cfg['environment'][cfg['build']['current_environment_id']]['module_root_dir'] = os.path.dirname(module.__module_file)
					shutit.chdir(cfg['environment'][cfg['build']['current_environment_id']]['module_root_dir'])
					shutit.login(prompt_prefix=module_id,command='bash')
					build_module(shutit, module)
					shutit.logout()
					shutit.chdir(revert_dir)
		if is_installed(shutit, module):
			shutit.log('Starting module')
			if not module.start(shutit):
				shutit.fail(module.module_id + ' failed on start',
				    child=shutit.pexpect_children['target_child'])


def do_test(shutit):
	"""Runs test phase, erroring if any return false.
	"""
	cfg = shutit.cfg
	if not cfg['build']['dotest']:
		shutit.log('Tests configured off, not running')
		return
	# Test in reverse order
	shutit.log('PHASE: test', code='32')
	if cfg['build']['interactive'] >= 3:
		print '\nNow doing test phase' + shutit_util.colour('32',
			'\n\n[Hit return to continue]\n')
		shutit_util.util_raw_input(shutit=shutit)
	stop_all(shutit)
	start_all(shutit)
	for module_id in module_ids(shutit, rev=True):
		module = shutit.shutit_map[module_id]
		# Only test if it's installed.
		if is_installed(shutit, shutit.shutit_map[module_id]):
			shutit.log('RUNNING TEST ON: ' + module_id, code='32')
			shutit.login(prompt_prefix=module_id,command='bash')
			if not shutit.shutit_map[module_id].test(shutit):
				shutit.fail(module_id + ' failed on test',
				child=shutit.pexpect_children['target_child'])
			shutit.logout()


def do_finalize(shutit):
	"""Runs finalize phase; run after all builds are complete and all modules
	have been stopped.
	"""
	cfg = shutit.cfg
	# Stop all the modules
	if cfg['build']['interactive'] >= 3:
		print('\nStopping all modules before finalize phase' + shutit_util.colour('32',
		      '\n\n[Hit return to continue]\n'))
		shutit_util.util_raw_input(shutit=shutit)
	stop_all(shutit)
	# Finalize in reverse order
	shutit.log('PHASE: finalize', code='32')
	if cfg['build']['interactive'] >= 3:
		print('\nNow doing finalize phase, which we do when all builds are ' +
		      'complete and modules are stopped' +
		      shutit_util.colour('32', '\n\n[Hit return to continue]\n'))
		shutit_util.util_raw_input(shutit=shutit)
	# Login at least once to get the exports.
	for module_id in module_ids(shutit, rev=True):
		# Only finalize if it's thought to be installed.
		if is_installed(shutit, shutit.shutit_map[module_id]):
			shutit.login(prompt_prefix=module_id,command='bash')
			if not shutit.shutit_map[module_id].finalize(shutit):
				shutit.fail(module_id + ' failed on finalize',
			                child=shutit.pexpect_children['target_child'])
			shutit.logout()


def setup_shutit_path(cfg):
	# try the current directory, the .. directory, or the ../shutit directory, the ~/shutit
	if not cfg['host']['add_shutit_to_path']:
		return
	res = shutit_util.util_raw_input(prompt='shutit appears not to be on your path - should try and we find it and add it to your ~/.bashrc (Y/n)?')
	if res in ['n','N']:
		with open(os.path.join(cfg['shutit_home'], 'config'), 'a') as f:
			f.write('\n[host]\nadd_shutit_to_path: no\n')
		return
	path_to_shutit = ''
	for d in ['.','..','~','~/shutit']:
		path = os.path.abspath(d + '/shutit')
		if not os.path.isfile(path):
			continue
		path_to_shutit = path
	while path_to_shutit == '':
		d = shutit_util.util_raw_input(prompt='cannot auto-find shutit - please input the path to your shutit dir\n')
		path = os.path.abspath(d + '/shutit')
		if not os.path.isfile(path):
			continue
		path_to_shutit = path
	if path_to_shutit != '':
		bashrc = os.path.expanduser('~/.bashrc')
		with open(bashrc, "a") as myfile:
			#http://unix.stackexchange.com/questions/26676/how-to-check-if-a-shell-is-login-interactive-batch
			myfile.write('\nexport PATH="$PATH:' + os.path.dirname(path_to_shutit) + '"\n')
		shutit_util.util_raw_input(prompt='\nPath set up - please open new terminal and re-run command\n')
		sys.exit()


def main():
	"""Main ShutIt function.

	Handles the configured actions:

		- skeleton     - create skeleton module
		- serve        - run as a server
		- list_configs - output computed configuration
		- depgraph     - output digraph of module dependencies
	"""
	if sys.version_info.major == 2:
		if sys.version_info.minor < 7:
			shutit_global.shutit.fail('Python version must be 2.7+')

	shutit = shutit_global.shutit
	cfg = shutit.cfg
	shutit_util.parse_args(shutit)

	if cfg['action']['skeleton']:
		shutit_util.create_skeleton(shutit)
		cfg['build']['completed'] = True
		return

	if cfg['action']['serve']:
		import shutit_srv
		cfg['build']['interactive'] = 0
		revert_dir = os.getcwd()
		os.chdir(sys.path[0])
		shutit_srv.start()
		os.chdir(revert_dir)
		return

	shutit_util.load_configs(shutit)

	# Try and ensure shutit is on the path - makes onboarding easier
	# Only do this if we're in a terminal
	if shutit_util.determine_interactive() and spawn.find_executable('shutit') is None:
		setup_shutit_path(cfg)

	shutit_util.load_mod_from_file(shutit, os.path.join(shutit.shutit_main_dir, 'shutit_setup.py'))
	shutit_util.load_shutit_modules(shutit)

	if cfg['action']['list_modules']:
		shutit_util.list_modules(shutit)
		sys.exit(0)

	init_shutit_map(shutit)
	config_collection(shutit)

	conn_target(shutit)

	errs = []
	errs.extend(check_deps(shutit))
	if cfg['action']['list_deps']:
		# Show dependency graph
		digraph = 'digraph depgraph {\n'
		digraph = digraph + '\n'.join([
			make_dep_graph(module) for module_id, module in shutit.shutit_map.items()
			if module_id in cfg and cfg[module_id]['shutit.core.module.build']
		])
		digraph = digraph + '\n}'
		f = file(cfg['build']['log_config_path'] + '/digraph.txt','w')
		f.write(digraph)
		f.close()
		digraph_all = 'digraph depgraph {\n'
		digraph_all = digraph_all + '\n'.join([
			make_dep_graph(module) for module_id, module in shutit.shutit_map.items()
		])
		digraph_all = digraph_all + '\n}'
		f = file(cfg['build']['log_config_path'] + '/digraph_all.txt','w')
		f.write(digraph_all)
		f.close()
		shutit.log('\n================================================================================\n' + digraph_all, force_stdout=True)
		shutit.log('\nAbove is the digraph for all modules seen in this shutit invocation. Use graphviz to render into an image, eg\n\n\tshutit depgraph -m mylibrary | dot -Tpng -o depgraph.png\n', force_stdout=True)
		shutit.log('\n================================================================================\n', force_stdout=True)
		shutit.log('\n\n' + digraph, force_stdout=True)
		shutit.log('\n================================================================================\n' + digraph, force_stdout=True)
		shutit.log('\nAbove is the digraph for all modules configured to be built in this shutit invocation. Use graphviz to render into an image, eg\n\n\tshutit depgraph -m mylibrary | dot -Tpng -o depgraph.png\n', force_stdout=True)
		shutit.log('\n================================================================================\n', force_stdout=True)
		# Exit now
		sys.exit(0)
	# Dependency validation done, now collect configs of those marked for build.
	config_collection_for_built(shutit)
	if cfg['action']['list_configs'] or cfg['build']['debug']:
		shutit.log(shutit_util.print_config(cfg, history=cfg['list_configs']['cfghistory']),
				   force_stdout=True)
		# Set build completed
		cfg['build']['completed'] = True
		f = file(cfg['build']['log_config_path'] + '/cfg.txt','w')
		f.write(shutit_util.print_config(cfg, history=cfg['list_configs']['cfghistory']))
		f.close()
		shutit.log('================================================================================', force_stdout=True)
		shutit.log('Config details placed in: ' + cfg['build']['log_config_path'], force_stdout=True)
		shutit.log('================================================================================', force_stdout=True)
		shutit.log('To render the digraph of this build into an image run eg:\n\ndot -Tgv -o ' + cfg['build']['log_config_path'] + '/digraph.gv ' + cfg['build']['log_config_path'] + '/digraph.txt && dot -Tpdf -o digraph.pdf ' + cfg['build']['log_config_path'] + '/digraph.gv\n\n', force_stdout=True)
		shutit.log('================================================================================', force_stdout=True)
		shutit.log('To render the digraph of all visible modules into an image, run eg:\n\ndot -Tgv -o ' + cfg['build']['log_config_path'] + '/digraph_all.gv ' + cfg['build']['log_config_path'] + '/digraph_all.txt && dot -Tpdf -o digraph_all.pdf ' + cfg['build']['log_config_path'] + '/digraph_all.gv\n\n', force_stdout=True)
		shutit.log('================================================================================', force_stdout=True)
		shutit.log('\nConfiguration details have been written to the folder: ' + cfg['build']['log_config_path'] + '\n', force_stdout=True)
		shutit.log('================================================================================', force_stdout=True)
	if cfg['action']['list_configs']:
		return
	# Check for conflicts now.
	errs.extend(check_conflicts(shutit))
	# Cache the results of check_ready at the start.
	errs.extend(check_ready(shutit, throw_error=False))
	if errs:
		shutit.log(print_modules(shutit), code='31')
		child = None
		for err in errs:
			shutit.log(err[0], force_stdout=True, code='31')
			if not child and len(err) > 1:
				child = err[1]
		shutit.fail("Encountered some errors, quitting", child=child)

	shutit.record_config()
	do_remove(shutit)
	do_build(shutit)
	do_test(shutit)
	do_finalize(shutit)

	finalize_target(shutit)

	shutit.log(shutit_util.build_report(shutit, '#Module: N/A (END)'), prefix=False,
			   force_stdout=True, code='32')

	if cfg['build']['build_log']:
		cfg['build']['report_final_messages'] += "Build log file: " + cfg['host']['logfile']

	# Show final report messages (ie messages to show after standard report).
	if cfg['build']['report_final_messages'] != '':
		shutit.log(cfg['build']['report_final_messages'], prefix=False,
		           force_stdout=True, code='31')

	if cfg['build']['interactive'] >= 3:
		shutit.log('\n' +
		           'The build is complete. You should now have a target ' + 
		           'called ' + cfg['target']['name'] +
		           ' and a new image if you chose to commit it.\n\n' + 
		           'Look and play with the following files from the newly-created ' + 
		           'module directory to dig deeper:\n\n    configs/build.cnf\n    ' + 
		           '*.py\n\nYou can rebuild at any time by running the supplied ' + 
		           './build.sh and run with the supplied ./run.sh. These may need ' + 
		           'tweaking for your particular environment, eg sudo\n\n' +
		           'You can inspect the details of the build in the target image\'s ' + 
		           cfg['build']['build_db_dir'] + ' directory.', force_stdout=True, code='32')

	# Mark the build as completed
	cfg['build']['completed'] = True


def do_phone_home(msg=None,question='Error seen - would you like to inform the maintainers?'):
	"""Report message home.
	msg - message to send home
	question - question to ask - assumes Y/y for send message, else no
	"""
	cfg = shutit.cfg
	if msg is None:
		msg = {}
	if shutit_global.cfg['build']['interactive'] == 0:
		return
	msg.update({'shutitrunstatus':'fail','pwd':os.getcwd(),'user':os.environ.get('LOGNAME', '')})
	if question != '' and shutit_util.util_raw_input(prompt=question + ' (Y/n)\n') not in ('y','Y',''):
		return
	try:
		urllib.urlopen("http://shutit.tk?" + urllib.urlencode(msg))
	except Exception as e:
		shutit_global.shutit.log('failed to send message: ' + str(e.message))


signal.signal(signal.SIGINT, shutit_util.ctrl_c_signal_handler)

if __name__ == '__main__':
	main()
