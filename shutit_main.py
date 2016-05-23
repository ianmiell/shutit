#!/usr/bin/env python
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



"""ShutIt is a means of building stateless target hosts in a flexible and predictable way.
"""


from shutit_module import ShutItModule, ShutItException, ShutItFailException
import shutit_util
import urllib
import shutit_global
import os
import signal
import sys
import logging
from distutils import spawn


# run_order of -1 means 'stop everything'
def stop_all(run_order=-1):
	"""Runs stop method on all modules less than the passed-in run_order.
	Used when target is exporting itself mid-build, so we clean up state
	before committing run files etc.
	"""
	shutit = shutit_global.shutit
	if shutit.build['interactive'] >= 3:
		print('\nRunning stop on all modules' + shutit_util.colourise('32', '\n\n[Hit return to continue]'))
		shutit_util.util_raw_input()
	# sort them so they're stopped in reverse order
	for module_id in shutit_util.module_ids(rev=True):
		shutit_module_obj = shutit.shutit_map[module_id]
		if run_order == -1 or shutit_module_obj.run_order <= run_order:
			if shutit_util.is_installed(shutit_module_obj):
				if not shutit_module_obj.stop(shutit):
					shutit.fail('failed to stop: ' + module_id, shutit_pexpect_child=shutit.get_shutit_pexpect_session_from_id('target_child').shutit_pexpect_child)


# Start all apps less than the supplied run_order
def start_all(run_order=-1):
	"""Runs start method on all modules less than the passed-in run_order.
	Used when target is exporting itself mid-build, so we can export a clean
	target and still depended-on modules running if necessary.
	"""
	shutit = shutit_global.shutit
	if shutit.build['interactive'] >= 3:
		print('\nRunning start on all modules' + shutit_util.colourise('32', '\n\n[Hit return to continue]\n'))
		shutit_util.util_raw_input()
	# sort them so they're started in order
	for module_id in shutit_util.module_ids():
		shutit_module_obj = shutit.shutit_map[module_id]
		if run_order == -1 or shutit_module_obj.run_order <= run_order:
			if shutit_util.is_installed(shutit_module_obj):
				if not shutit_module_obj.start(shutit):
					shutit.fail('failed to start: ' + module_id, shutit_pexpect_child=shutit.get_shutit_pexpect_session_from_id('target_child').shutit_pexpect_child)






def is_ready(shutit_module_obj):
	"""Returns true if this module is ready to be built.
	Caches the result (as it's assumed not to change during the build).
	"""
	shutit = shutit_global.shutit
	if shutit_module_obj.module_id in shutit_global.shutit.get_current_shutit_pexpect_session_environment().modules_ready:
		shutit.log('is_ready: returning True from cache',level=logging.DEBUG)
		return True
	ready = shutit_module_obj.check_ready(shutit)
	if ready:
		shutit_global.shutit.get_current_shutit_pexpect_session_environment().modules_ready.append(shutit_module_obj.module_id)
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
	modules = shutit.shutit_modules
	# Have we got anything to process outside of special modules?
	if len([mod for mod in modules if mod.run_order > 0]) < 1:
		shutit.log(modules,level=logging.DEBUG)
		path = ':'.join(shutit.host['shutit_module_path'])
		shutit.log('\nIf you are new to ShutIt, see:\n\n\thttp://ianmiell.github.io/shutit/\n\nor try running\n\n\tshutit skeleton\n\n',level=logging.INFO)
		if path == '':
			shutit.fail('No ShutIt modules aside from core ones found and no ShutIt module path given.\nDid you set --shutit_module_path/-m wrongly?\n')
		elif path == '.':
			shutit.fail('No modules aside from core ones found and no ShutIt module path given apart from default (.).\n\n- Did you set --shutit_module_path/-m?\n- Is there a STOP* file in your . dir?')
		else:
			shutit.fail('No modules aside from core ones found and no ShutIt modules in path:\n\n' + path + '\n\nor their subfolders. Check your --shutit_module_path/-m setting and check that there are ShutIt modules below without STOP* files in any relevant directories.')

	shutit.log('PHASE: base setup', level=logging.DEBUG)
	if shutit.build['interactive'] >= 3:
		shutit.log('\nChecking to see whether there are duplicate module ids or run orders in the visible modules.\nModules I see are:\n',level=logging.DEBUG)
		for module in modules:
			shutit.log(module.module_id, level=logging.DEBUG)
		shutit.log('\n',level=logging.DEBUG)

	run_orders = {}
	has_core_module = False
	for module in modules:
		assert isinstance(module, ShutItModule)
		if module.module_id in shutit.shutit_map:
			shutit.fail('Duplicated module id: ' + module.module_id + '\n\nYou may want to check your --shutit_module_path setting')
		if module.run_order in run_orders:
			shutit.fail('Duplicate run order: ' + str(module.run_order) + ' for ' + module.module_id + ' and ' + run_orders[module.run_order].module_id + '\n\nYou may want to check your --shutit_module_path setting')
		if module.run_order == 0:
			has_core_module = True
		shutit.shutit_map[module.module_id] = run_orders[module.run_order] = module

	if not has_core_module:
		shutit.fail('No module with run_order=0 specified! This is required.')

	if shutit.build['interactive'] >= 3:
		print(shutit_util.colourise('32', 'Module id and run order checks OK\n\n[Hit return to continue]\n'))
		shutit_util.util_raw_input()


def conn_target(shutit):
	"""Connect to the target.
	"""
	conn_module = None
	for mod in shutit.conn_modules:
		if mod.module_id == shutit.build['conn_module']:
			conn_module = mod
			break
	if conn_module is None:
		shutit.fail('Couldn\'t find conn_module ' + shutit.build['conn_module'])

	# Set up the target in pexpect.
	if shutit.build['interactive'] >= 3:
		print('\nRunning the conn module (' + shutit.shutit_main_dir + '/shutit_setup.py)' + shutit_util.colourise('32', '\n\n[Hit return to continue]\n'))
		shutit_util.util_raw_input()
	conn_module.get_config(shutit)
	conn_module.build(shutit)


def finalize_target():
	"""Finalize the target using the core finalize method.
	"""
	shutit = shutit_global.shutit
	shutit.pause_point('\nFinalizing the target module (' + shutit.shutit_main_dir + '/shutit_setup.py)', print_input=False, level=3)
	# Can assume conn_module exists at this point
	for mod in shutit.conn_modules:
		if mod.module_id == shutit.build['conn_module']:
			conn_module = mod
			break
	conn_module.finalize(shutit)


# Once we have all the modules, then we can look at dependencies.
# Dependency validation begins.
def resolve_dependencies(to_build, depender):
	"""Add any required dependencies.
	"""
	shutit = shutit_global.shutit
	shutit.log('In resolve_dependencies',level=logging.DEBUG)
	cfg = shutit.cfg
	for dependee_id in depender.depends_on:
		dependee = shutit.shutit_map.get(dependee_id)
		# Don't care if module doesn't exist, we check this later
		if (dependee and dependee not in to_build
		    and cfg[dependee_id]['shutit.core.module.build_ifneeded']):
			to_build.append(dependee)
			cfg[dependee_id]['shutit.core.module.build'] = True
	return True


def check_dependee_exists(depender, dependee, dependee_id):
	"""Checks whether a depended-on module is available.
	"""
	# If the module id isn't there, there's a problem.
	if dependee == None:
		return ('module: \n\n' + dependee_id + '\n\nnot found in paths: ' + str(shutit_global.shutit.host['shutit_module_path']) + ' but needed for ' + depender.module_id + '\nCheck your --shutit_module_path setting and ensure that all modules configured to be built are in that path setting, eg "--shutit_module_path /path/to/other/module/:."\n\nAlso check that the module is configured to be built with the correct module id in that module\'s configs/build.cnf file.\n\nSee also help.')


def check_dependee_build(depender, dependee, dependee_id):
	"""Checks whether a depended on module is configured to be built.
	"""
	cfg = shutit_global.shutit.cfg
	# If depender is installed or will be installed, so must the dependee
	if not (cfg[dependee.module_id]['shutit.core.module.build'] or
	        shutit_util.is_to_be_built_or_is_installed(dependee)):
		return ('depender module id:\n\n[' + depender.module_id + ']\n\nis configured: "build:yes" or is already built but dependee module_id:\n\n[' + dependee_id + ']\n\n is not configured: "build:yes"')


def check_dependee_order(depender, dependee, dependee_id):
	"""Checks whether run orders are in the appropriate order.
	"""
	# If it depends on a module id, then the module id should be higher up
	# in the run order.
	if dependee.run_order > depender.run_order:
		return ('depender module id:\n\n' + depender.module_id + '\n\n(run order: ' + str(depender.run_order) + ') ' + 'depends on dependee module_id:\n\n' + dependee_id + '\n\n(run order: ' + str(dependee.run_order) + ') ' + 'but the latter is configured to run after the former')


def make_dep_graph(depender):
	"""Returns a digraph string fragment based on the passed-in module
	"""
	digraph = ''
	for dependee_id in depender.depends_on:
		digraph = (digraph + '"' + depender.module_id + '"->"' + dependee_id + '";\n')
	return digraph


def check_deps():
	"""Dependency checking phase is performed in this method.
	"""
	shutit = shutit_global.shutit
	cfg = shutit.cfg
	shutit.log('PHASE: dependencies', level=logging.DEBUG)
	shutit.pause_point('\nNow checking for dependencies between modules', print_input=False, level=3)
	# Get modules we're going to build
	to_build = [
		shutit.shutit_map[module_id] for module_id in shutit.shutit_map
		if module_id in cfg and cfg[module_id]['shutit.core.module.build']
	]
	# Add any deps we may need by extending to_build and altering cfg
	for module in to_build:
		resolve_dependencies(to_build, module)

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
			triples.append((depender, shutit.shutit_map.get(dependee_id), dependee_id))

	triples = err_checker([ check_dependee_exists(depender, dependee, dependee_id) for depender, dependee, dependee_id in triples ], triples)
	triples = err_checker([ check_dependee_build(depender, dependee, dependee_id) for depender, dependee, dependee_id in triples ], triples)
	triples = err_checker([ check_dependee_order(depender, dependee, dependee_id) for depender, dependee, dependee_id in triples ], triples)

	if found_errs:
		return [(err,) for err in found_errs]

	shutit.log('Modules configured to be built (in order) are: ', level=logging.DEBUG)
	for module_id in shutit_util.module_ids():
		module = shutit.shutit_map[module_id]
		if cfg[module_id]['shutit.core.module.build']:
			shutit.log(module_id + '    ' + str(module.run_order), level=logging.DEBUG)
	shutit.log('\n', level=logging.DEBUG)

	return []


def check_conflicts(shutit):
	"""Checks for any conflicts between modules configured to be built.
	"""
	cfg = shutit.cfg
	# Now consider conflicts
	shutit.log('PHASE: conflicts', level=logging.DEBUG)
	errs = []
	shutit.pause_point('\nNow checking for conflicts between modules', print_input=False, level=3)
	for module_id in shutit_util.module_ids():
		if not cfg[module_id]['shutit.core.module.build']:
			continue
		conflicter = shutit.shutit_map[module_id]
		for conflictee in conflicter.conflicts_with:
			# If the module id isn't there, there's no problem.
			conflictee_obj = shutit.shutit_map.get(conflictee)
			if conflictee_obj == None:
				continue
			if ((cfg[conflicter.module_id]['shutit.core.module.build'] or
			     shutit_util.is_to_be_built_or_is_installed(conflicter)) and
			    (cfg[conflictee_obj.module_id]['shutit.core.module.build'] or
			     shutit_util.is_to_be_built_or_is_installed(conflictee_obj))):
			    errs.append(('conflicter module id: ' + conflicter.module_id + ' is configured to be built or is already built but conflicts with module_id: ' + conflictee_obj.module_id,))
	return errs


def check_ready(throw_error=True):
	"""Check that all modules are ready to be built, calling check_ready on
	each of those configured to be built and not already installed
	(see shutit_util.is_installed).
	"""
	shutit = shutit_global.shutit
	cfg = shutit.cfg
	shutit.log('PHASE: check_ready', level=logging.DEBUG)
	errs = []
	shutit.pause_point('\nNow checking whether we are ready to build modules configured to be built', print_input=False, level=3)
	# Find out who we are to see whether we need to log in and out or not.
	for module_id in shutit_util.module_ids():
		module = shutit.shutit_map[module_id]
		shutit.log('considering check_ready (is it ready to be built?): ' + module_id, level=logging.DEBUG)
		if cfg[module_id]['shutit.core.module.build'] and module.module_id not in shutit_global.shutit.get_current_shutit_pexpect_session_environment().modules_ready and not shutit_util.is_installed(module):
			shutit.log('checking whether module is ready to build: ' + module_id, level=logging.DEBUG)
			shutit.login(prompt_prefix=module_id,command='bash')
			# Move to the correct directory (eg for checking for the existence of files needed for build)
			revert_dir = os.getcwd()
			shutit_global.shutit.get_current_shutit_pexpect_session_environment().module_root_dir = os.path.dirname(module.__module_file)
			shutit.chdir(shutit_global.shutit.get_current_shutit_pexpect_session_environment().module_root_dir)
			if not is_ready(module) and throw_error:
				errs.append((module_id + ' not ready to install.\nRead the check_ready function in the module,\nor log messages above to determine the issue.\n\n', shutit.get_shutit_pexpect_session_from_id('target_child')))
			shutit.logout()
			shutit.chdir(revert_dir)
	return errs


def do_remove(loglevel=logging.DEBUG):
	"""Remove modules by calling remove method on those configured for removal.
	"""
	shutit = shutit_global.shutit
	cfg = shutit.cfg
	# Now get the run_order keys in order and go.
	shutit.log('PHASE: remove', level=loglevel)
	shutit.pause_point('\nNow removing any modules that need removing', print_input=False, level=3)
	# Login at least once to get the exports.
	for module_id in shutit_util.module_ids():
		module = shutit.shutit_map[module_id]
		shutit.log('considering whether to remove: ' + module_id, level=logging.DEBUG)
		if cfg[module_id]['shutit.core.module.remove']:
			shutit.log('removing: ' + module_id, level=logging.DEBUG)
			shutit.login(prompt_prefix=module_id,command='bash')
			if not module.remove(shutit):
				shutit.log(shutit_util.print_modules(), level=logging.DEBUG)
				shutit.fail(module_id + ' failed on remove', shutit_pexpect_child=shutit.get_shutit_pexpect_session_from_id('target_child').pexpect_child)
			else:
				if shutit.build['delivery'] in ('docker','dockerfile'):
					# Create a directory and files to indicate this has been removed.
					shutit.send(' mkdir -p ' + shutit.build['build_db_dir'] + '/module_record/' + module.module_id + ' && rm -f ' + shutit.build['build_db_dir'] + '/module_record/' + module.module_id + '/built && touch ' + shutit.build['build_db_dir'] + '/module_record/' + module.module_id + '/removed', loglevel=loglevel)
					# Remove from "installed" cache
					if module.module_id in shutit_global.shutit.get_current_shutit_pexpect_session_environment().modules_installed:
						shutit_global.shutit.get_current_shutit_pexpect_session_environment().modules_installed.remove(module.module_id)
					# Add to "not installed" cache
					shutit_global.shutit.get_current_shutit_pexpect_session_environment().modules_not_installed.append(module.module_id)
			shutit.logout()
			


def build_module(module, loglevel=logging.DEBUG):
	"""Build passed-in module.
	"""
	shutit = shutit_global.shutit
	cfg = shutit.cfg
	shutit.log('Building ShutIt module: ' + module.module_id + ' with run order: ' + str(module.run_order), level=logging.INFO)
	shutit.build['report'] = (shutit.build['report'] + '\nBuilding ShutIt module: ' + module.module_id + ' with run order: ' + str(module.run_order))
	if not module.build(shutit):
		shutit.fail(module.module_id + ' failed on build', shutit_pexpect_child=shutit.get_shutit_pexpect_session_from_id('target_child').pexpect_child)
	else:
		if shutit.build['delivery'] in ('docker','dockerfile'):
			# Create a directory and files to indicate this has been built.
			shutit.send(' mkdir -p ' + shutit.build['build_db_dir'] + '/module_record/' + module.module_id + ' && touch ' + shutit.build['build_db_dir'] + '/module_record/' + module.module_id + '/built && rm -f ' + shutit.build['build_db_dir'] + '/module_record/' + module.module_id + '/removed', loglevel=loglevel)
		# Put it into "installed" cache
		shutit_global.shutit.get_current_shutit_pexpect_session_environment().modules_installed.append(module.module_id)
		# Remove from "not installed" cache
		if module.module_id in shutit_global.shutit.get_current_shutit_pexpect_session_environment().modules_not_installed:
			shutit_global.shutit.get_current_shutit_pexpect_session_environment().modules_not_installed.remove(module.module_id)
	shutit.pause_point('\nPausing to allow inspect of build for: ' + module.module_id, print_input=True, level=2)
	shutit.build['report'] = (shutit.build['report'] + '\nCompleted module: ' + module.module_id)
	if cfg[module.module_id]['shutit.core.module.tag'] or shutit.build['interactive'] >= 3:
		shutit.log(shutit_util.build_report('#Module:' + module.module_id), level=logging.DEBUG)
	if (not cfg[module.module_id]['shutit.core.module.tag'] and shutit.build['interactive'] >= 2):
		print ("\n\nDo you want to save state now we\'re at the " + "end of this module? (" + module.module_id + ") (input y/n)")
		cfg[module.module_id]['shutit.core.module.tag'] = (shutit_util.util_raw_input(default='y') == 'y')
	if cfg[module.module_id]['shutit.core.module.tag'] or shutit.build['tag_modules']:
		shutit.log(module.module_id + ' configured to be tagged, doing repository work',level=logging.INFO)
		# Stop all before we tag to avoid file changing errors, and clean up pid files etc..
		stop_all(module.run_order)
		shutit.do_repository_work(str(module.module_id) + '_' + str(module.run_order), password=shutit.host['password'], docker_executable=shutit.host['docker_executable'], force=True)
		# Start all after we tag to ensure services are up as expected.
		start_all(module.run_order)
	if shutit.build['interactive'] >= 2:
		print ("\n\nDo you want to stop interactive mode? (input y/n)\n")
		if shutit_util.util_raw_input(default='y') == 'y':
			shutit.build['interactive'] = 0


def do_build():
	"""Runs build phase, building any modules that we've determined
	need building.
	"""
	shutit = shutit_global.shutit
	cfg = shutit.cfg
	shutit.log('PHASE: build, repository work', level=logging.DEBUG)
	if shutit.build['interactive'] >= 3:
		print ('\nNow building any modules that need building' + shutit_util.colourise('32', '\n\n[Hit return to continue]\n'))
		shutit_util.util_raw_input()
	module_id_list = shutit_util.module_ids()
	if shutit.build['deps_only']:
		module_id_list_build_only = filter(lambda x: cfg[x]['shutit.core.module.build'], module_id_list)
	for module_id in module_id_list:
		module = shutit.shutit_map[module_id]
		shutit.log('Considering whether to build: ' + module.module_id, level=logging.INFO)
		if cfg[module.module_id]['shutit.core.module.build']:
			if shutit.build['delivery'] not in module.ok_delivery_methods:
				shutit.fail('Module: ' + module.module_id + ' can only be built with one of these --delivery methods: ' + str(module.ok_delivery_methods) + '\nSee shutit build -h for more info, or try adding: --delivery <method> to your shutit invocation')
			if shutit_util.is_installed(module):
				shutit.build['report'] = (shutit.build['report'] + '\nBuilt already: ' + module.module_id + ' with run order: ' + str(module.run_order))
			else:
				# We move to the module directory to perform the build, returning immediately afterwards.
				if shutit.build['deps_only'] and module_id == module_id_list_build_only[-1]:
					# If this is the last module, and we are only building deps, stop here.
					shutit.build['report'] = (shutit.build['report'] + '\nSkipping: ' + module.module_id + ' with run order: ' + str(module.run_order) + '\n\tas this is the final module and we are building dependencies only')
				else:
					revert_dir = os.getcwd()
					shutit_global.shutit.get_current_shutit_pexpect_session_environment().module_root_dir = os.path.dirname(module.__module_file)
					shutit.chdir(shutit_global.shutit.get_current_shutit_pexpect_session_environment().module_root_dir)
					shutit.login(prompt_prefix=module_id,command='bash')
					build_module(module)
					shutit.logout()
					shutit.chdir(revert_dir)
		if shutit_util.is_installed(module):
			shutit.log('Starting module',level=logging.DEBUG)
			if not module.start(shutit):
				shutit.fail(module.module_id + ' failed on start', shutit_pexpect_child=shutit.get_shutit_pexpect_session_from_id('target_child').pexpect_child)


def do_test():
	"""Runs test phase, erroring if any return false.
	"""
	shutit = shutit_global.shutit
	if not shutit.build['dotest']:
		shutit.log('Tests configured off, not running',level=logging.DEBUG)
		return
	# Test in reverse order
	shutit.log('PHASE: test', level=logging.DEBUG)
	if shutit.build['interactive'] >= 3:
		print '\nNow doing test phase' + shutit_util.colourise('32', '\n\n[Hit return to continue]\n')
		shutit_util.util_raw_input()
	stop_all()
	start_all()
	for module_id in shutit_util.module_ids(rev=True):
		# Only test if it's installed.
		if shutit_util.is_installed(shutit.shutit_map[module_id]):
			shutit.log('RUNNING TEST ON: ' + module_id, level=logging.DEBUG)
			shutit.login(prompt_prefix=module_id,command='bash')
			if not shutit.shutit_map[module_id].test(shutit):
				shutit.fail(module_id + ' failed on test', shutit_pexpect_child=shutit.get_shutit_pexpect_session_from_id('target_child').pexpect_child)
			shutit.logout()


def do_finalize():
	"""Runs finalize phase; run after all builds are complete and all modules
	have been stopped.
	"""
	shutit = shutit_global.shutit
	# Stop all the modules
	if shutit.build['interactive'] >= 3:
		print('\nStopping all modules before finalize phase' + shutit_util.colourise('32', '\n\n[Hit return to continue]\n'))
		shutit_util.util_raw_input()
	stop_all()
	# Finalize in reverse order
	shutit.log('PHASE: finalize', level=logging.DEBUG)
	if shutit.build['interactive'] >= 3:
		print('\nNow doing finalize phase, which we do when all builds are ' + 'complete and modules are stopped' + shutit_util.colourise('32', '\n\n[Hit return to continue]\n'))
		shutit_util.util_raw_input()
	# Login at least once to get the exports.
	for module_id in shutit_util.module_ids(rev=True):
		# Only finalize if it's thought to be installed.
		if shutit_util.is_installed(shutit.shutit_map[module_id]):
			shutit.login(prompt_prefix=module_id,command='bash')
			if not shutit.shutit_map[module_id].finalize(shutit):
				shutit.fail(module_id + ' failed on finalize', shutit_pexpect_child=shutit.get_shutit_pexpect_session_from_id('target_child').pexpect_child)
			shutit.logout()


def setup_shutit_path(cfg):
	# try the current directory, the .. directory, or the ../shutit directory, the ~/shutit
	shutit = shutit_global.shutit
	if not shutit.host['add_shutit_to_path']:
		return
	res = shutit_util.util_raw_input(prompt='shutit appears not to be on your path - should try and we find it and add it to your ~/.bashrc (Y/n)?')
	if res in ['n','N']:
		with open(os.path.join(shutit.shutit_path, 'config'), 'a') as f:
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
		shutit_util.handle_exit()


def main():
	"""Main ShutIt function.

	Handles the configured actions:

		- skeleton     - create skeleton module
		- list_configs - output computed configuration
		- depgraph     - output digraph of module dependencies
	"""
	if sys.version_info.major == 2:
		if sys.version_info.minor < 7:
			shutit_global.shutit.fail('Python version must be 2.7+')

	shutit = shutit_global.shutit
	cfg = shutit.cfg
	shutit.log('ShutIt Started... ',transient=True,newline=False)
	shutit_util.parse_args()

	if shutit.action['skeleton']:
		shutit_util.create_skeleton()
		shutit.build['completed'] = True
		return

	shutit.log('Loading configs...',transient=True)
	shutit_util.load_configs()

	# Try and ensure shutit is on the path - makes onboarding easier
	# Only do this if we're in a terminal
	if shutit_util.determine_interactive() and spawn.find_executable('shutit') is None:
		setup_shutit_path(cfg)

	shutit_util.load_mod_from_file(os.path.join(shutit.shutit_main_dir, 'shutit_setup.py'))
	shutit_util.load_shutit_modules()
	shutit.log('ShutIt modules loaded',level=logging.INFO)

	init_shutit_map(shutit)

	shutit_util.config_collection()
	shutit.log('Configuration loaded',level=logging.INFO)

	if shutit.action['list_modules']:
		shutit_util.list_modules()
		shutit_util.handle_exit()
	conn_target(shutit)
	shutit.log('Connected to target',level=logging.INFO)

	if shutit.build['interactive'] > 0 and shutit.build['choose_config']:
		errs = do_interactive_modules()
	else:
		errs = []
		errs.extend(check_deps())

	if shutit.action['list_deps']:
		# Show dependency graph
		digraph = 'digraph depgraph {\n'
		digraph += '\n'.join([ make_dep_graph(module) for module_id, module in shutit.shutit_map.items() if module_id in cfg and cfg[module_id]['shutit.core.module.build'] ])
		digraph += '\n}'
		f = file(shutit.build['log_config_path'] + '/digraph.txt','w')
		f.write(digraph)
		f.close()
		digraph_all = 'digraph depgraph {\n'
		digraph_all += '\n'.join([ make_dep_graph(module) for module_id, module in shutit.shutit_map.items() ])
		digraph_all += '\n}'
		f = file(shutit.build['log_config_path'] + '/digraph_all.txt','w')
		f.write(digraph_all)
		f.close()
		shutit.log('\n================================================================================\n' + digraph_all)
		shutit.log('\nAbove is the digraph for all modules seen in this shutit invocation. Use graphviz to render into an image, eg\n\n\tshutit depgraph -m mylibrary | dot -Tpng -o depgraph.png\n')
		shutit.log('\n================================================================================\n')
		shutit.log('\n\n' + digraph)
		shutit.log('\n================================================================================\n' + digraph)
		shutit.log('\nAbove is the digraph for all modules configured to be built in this shutit invocation. Use graphviz to render into an image, eg\n\n\tshutit depgraph -m mylibrary | dot -Tpng -o depgraph.png\n')
		shutit.log('\n================================================================================\n')
		# Exit now
		shutit_util.handle_exit()
	# Dependency validation done, now collect configs of those marked for build.
	shutit_util.config_collection_for_built()


	if shutit.action['list_configs'] or shutit.build['loglevel'] <= logging.DEBUG:
		# Set build completed
		shutit.build['completed'] = True
		shutit.log('================================================================================')
		shutit.log('Config details placed in: ' + shutit.build['log_config_path'])
		shutit.log('================================================================================')
		shutit.log('To render the digraph of this build into an image run eg:\n\ndot -Tgv -o ' + shutit.build['log_config_path'] + '/digraph.gv ' + shutit.build['log_config_path'] + '/digraph.txt && dot -Tpdf -o digraph.pdf ' + shutit.build['log_config_path'] + '/digraph.gv\n\n')
		shutit.log('================================================================================')
		shutit.log('To render the digraph of all visible modules into an image, run eg:\n\ndot -Tgv -o ' + shutit.build['log_config_path'] + '/digraph_all.gv ' + shutit.build['log_config_path'] + '/digraph_all.txt && dot -Tpdf -o digraph_all.pdf ' + shutit.build['log_config_path'] + '/digraph_all.gv\n\n')
		shutit.log('================================================================================')
		shutit.log('\nConfiguration details have been written to the folder: ' + shutit.build['log_config_path'] + '\n')
		shutit.log('================================================================================')
	if shutit.action['list_configs']:
		return

	# Check for conflicts now.
	errs.extend(check_conflicts(shutit))
	# Cache the results of check_ready at the start.
	errs.extend(check_ready(throw_error=False))
	if errs:
		shutit.log(shutit_util.print_modules(), level=logging.ERROR)
		child = None
		for err in errs:
			shutit.log(err[0], level=logging.ERROR)
			if not child and len(err) > 1:
				child = err[1]
		shutit.fail("Encountered some errors, quitting", shutit_pexpect_child=child)

	do_remove()
	do_build()
	do_test()
	do_finalize()
	finalize_target()

	shutit.log(shutit_util.build_report('#Module: N/A (END)'), level=logging.DEBUG)

	# Show final report messages (ie messages to show after standard report).
	if shutit.build['report_final_messages'] != '':
		shutit.log(shutit.build['report_final_messages'], level=logging.INFO)

	if shutit.build['interactive'] >= 3:
		shutit.log('\n' + 'The build is complete. You should now have a target called ' + shutit.target['name'] + ' and a new image if you chose to commit it.\n\nLook and play with the following files from the newly-created module directory to dig deeper:\n\n    configs/build.cnf\n    *.py\n\nYou can rebuild at any time by running the supplied ./build.sh and run with the supplied ./run.sh. These may need tweaking for your particular environment, eg sudo', level=logging.DEBUG)

	# Mark the build as completed
	shutit.build['completed'] = True
	shutit.log('ShutIt run finished',level=logging.INFO)
	shutit_util.handle_exit(0)


def do_phone_home(msg=None,question='Error seen - would you like to inform the maintainers?'):
	"""Report message home.
	msg - message to send home
	question - question to ask - assumes Y/y for send message, else no
	"""
	if msg is None:
		msg = {}
	if shutit_global.shutit.shutit.build['interactive'] == 0:
		return
	msg.update({'shutitrunstatus':'fail','pwd':os.getcwd(),'user':os.environ.get('LOGNAME', '')})
	if question != '' and shutit_util.util_raw_input(prompt=question + ' (Y/n)\n') not in ('y','Y',''):
		return
	try:
		urllib.urlopen("http://shutit.tk?" + urllib.urlencode(msg))
	except Exception as e:
		shutit_global.shutit.log('failed to send message: ' + str(e.message),level=logging.ERROR)


def do_interactive_modules():
	shutit = shutit_global.shutit
	cfg = shutit.cfg
	errs = []
	while True:
		shutit_util.list_modules(long_output=False,sort_order='run_order')
		# Which module do you want to toggle?
		module_id = shutit_util.util_raw_input(prompt='Which module id do you want to toggle?\n(just hit return to continue with build)\n')
		if module_id:
			try:
				_=cfg[module_id]
			except:
				print 'Please input a valid module id'
				continue
			cfg[module_id]['shutit.core.module.build'] = not cfg[module_id]['shutit.core.module.build']
			if not shutit_util.config_collection_for_built(throw_error=False):
				cfg[module_id]['shutit.core.module.build'] = not cfg[module_id]['shutit.core.module.build']
				shutit_util.util_raw_input(prompt='Hit return to continue.\n')
				continue
			# If true, set up config for that module
			if cfg[module_id]['shutit.core.module.build']:
				# TODO: does this catch all the ones switched on? Once done, get configs for all those.
				newcfg_list = []
				while True:
					print shutit_util.print_config(cfg,module_id=module_id)
					name = shutit_util.util_raw_input(prompt='Above is the config for that module. Hit return to continue, or a config item you want to update.\n')
					if name:
						doing_list = False
						while True:
							if doing_list:
								val_type = shutit_util.util_raw_input(prompt='Input the type for the next list item: b(oolean), s(tring).\n')
								if val_type not in ('b','s',''):
									continue
							else:
								val_type = shutit_util.util_raw_input(prompt='Input the type for that config item: b(oolean), s(tring), l(ist).\n')
								if val_type not in ('b','s','l',''):
									continue
							if val_type == 's':
								val = shutit_util.util_raw_input(prompt='Input the value new for that config item.\n')
								if doing_list:
									newcfg_list.append(val)	
								else:
									break
							elif val_type == 'b':
								val = shutit_util.util_raw_input(prompt='Input the value new for the boolean (t/f).\n')
								if doing_list:
									if val == 't':
										newcfg_list.append(True)
									elif val == 'f':
										newcfg_list.append(False)
									else:
										print 'Input t or f please'
										continue
								else:
									break
							elif val_type == 'l':
								doing_list = True
								newcfg_list = []
							elif val_type == '':
								break
						# TODO: handle blank/None
						if doing_list:
							cfg[module_id][name] = newcfg_list
						else:
							cfg[module_id][name] = val
					else:
						break
			else:
				pass
				# TODO: if removing, get any that depend on it, and remove those too
		else:
			break
	return errs

def setup_signals():
	signal.signal(signal.SIGINT, shutit_util.ctrl_c_signal_handler)
	signal.signal(signal.SIGQUIT, shutit_util.ctrl_quit_signal_handler)

shutit_version='...
if __name__ == '__main__':
	setup_signals()
	main()


