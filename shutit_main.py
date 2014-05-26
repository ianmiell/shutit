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

"""ShutIt is
"""

from shutit_module import ShutItModule, ShutItException
import util
import shutit_global
import setup
import time
import sys

def module_ids(shutit, rev=False):
	"""Gets a list of module ids by run_order, ignoring conn modules (run order < 0)
	"""
	shutit_map = shutit.shutit_map
	ids = sorted(shutit_map.keys(), key=lambda mid: shutit_map[mid].run_order)
	if rev:
		ids = list(reversed(ids))
	return ids

def print_modules(shutit):
	"""Returns a string table representing the modules in the ShutIt module map.
	"""
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	s = ''
	s = s + 'Modules: \n'
	s = s + '\tRun order\tBuild\tRemove\tModule ID\n'
	for mid in module_ids(shutit):
		s = s + ('\t' + str(shutit_map[mid].run_order) + '\t\t' +
			str(cfg[mid]['build']) + '\t' +
			str(cfg[mid]['remove']) + '\t' +
			mid + '\n')
	return s

# run_order of -1 means 'stop everything'
def stop_all(shutit, run_order=-1):
	"""Runs stop method on all modules less than the passed-in run_order.
	Used when container is exporting itself mid-build, so we clean up state before committing run files etc.
	"""
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	if cfg['build']['interactive'] >= 2:
		shutit.pause_point('\nRunning stop on all modules',print_input=False)
	# sort them to it's stopped in reverse order)
	for mid in module_ids(shutit, rev=True):
		shutit_module_obj = shutit_map[mid]
		if run_order == -1 or shutit_module_obj.run_order <= run_order:
			if is_built(shutit,shutit_module_obj):
				if not shutit_module_obj.stop(shutit):
					util.fail('failed to stop: ' + mid,child=shutit.pexpect_children['container_child'])

# Start all apps less than the supplied run_order
def start_all(shutit, run_order=-1):
	"""Runs start method on all modules less than the passed-in run_order.
	Used when container is exporting itself mid-build, so we can export a clean
	container and still depended-on modules running if necessary.
	"""
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	if cfg['build']['interactive'] >= 2:
		shutit.pause_point('\nRunning start on all modules',print_input=False)
	# sort them to they're started in order)
	for mid in module_ids(shutit):
		shutit_module_obj = shutit_map[mid]
		if run_order == -1 or shutit_module_obj.run_order <= run_order:
			if is_built(shutit,shutit_module_obj):
				if not shutit_module_obj.start(shutit):
					util.fail('failed to start: ' + mid,child=shutit.pexpect_children['container_child'])

def is_built(shutit,shutit_module_obj):
	"""Returns true if this module is configured to be built, or if it is already installed.
	"""
	return shutit.cfg[shutit_module_obj.module_id]['build'] or shutit_module_obj.is_installed(shutit)

def init_shutit_map(shutit):
	"""Initializes the module map of shutit based on the modules we have gathered.

	Checks we have core modules
	Checks for duplicate module details.
	Sets up common config.
	Sets up map of modules.
	"""
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map

	modules = shutit.shutit_modules

	# Have we got anything to process outside of special modules?
	if len([mod for mod in modules if mod.run_order > 0]) < 1:
		shutit.log(modules)
		util.fail('No ShutIt modules in path:\n\n' +
			':'.join(cfg['host']['shutit_module_paths']) +
			'\n\nor their subfolders. Check your --shutit_module_path setting.')

	shutit.log('PHASE: base setup',code='31')
	if cfg['build']['interactive'] >= 2:
		shutit.pause_point('\nChecking to see whether there are duplicate module ids or run orders in the visible modules.',
			print_input=False)
		shutit.log('\nModules I see are:\n',force_stdout=True)
		for m in modules:
			shutit.log(m.module_id,force_stdout=True,code='31')
		shutit.log('\n',force_stdout=True)
		shutit.pause_point('',print_input=False)

	run_orders = {}
	has_core_module = False
	for m in modules:
		assert isinstance(m, ShutItModule)
		if m.module_id in shutit_map:
			util.fail('Duplicated module id: ' + m.module_id)
		if m.run_order in run_orders:
			util.fail('Duplicate run order: ' + str(m.run_order) + ' for ' +
				m.module_id + ' and ' + run_orders[m.run_order].module_id)
		if m.run_order == 0:
			has_core_module = True
		shutit_map[m.module_id] = run_orders[m.run_order] = m

	if not has_core_module:
		util.fail('No module with run_order=0 specified! This is required.')

def config_collection(shutit):
	"""Collect core config from config files for all seen modules.
	"""
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	for mid in module_ids(shutit):

		# Default to None so we can interpret as ifneeded
		util.get_config(cfg,mid,'build',None,boolean=True)
		util.get_config(cfg,mid,'remove',False,boolean=True)
		util.get_config(cfg,mid,'do_repository_work',False,boolean=True)

		# ifneeded will (by default) only take effect if 'build' is not specified
		# It can, however, be forced to a value, but this should be unusual
		if cfg[mid]['build'] is None:
			util.get_config(cfg,mid,'build_ifneeded',True,boolean=True)
			cfg[mid]['build'] = False
		else:
			util.get_config(cfg,mid,'build_ifneeded',False,boolean=True)

		if not shutit_map[mid].get_config(shutit):
			util.fail(mid + ' failed on get_config')

def conn_container(shutit):
	"""Connect to the container.
	"""
	assert len(shutit.conn_modules) == 1
	# Set up the container in pexpect.
	if shutit.cfg['build']['interactive'] >= 2:
		shutit.pause_point('\nRunning the conn module (' +
			shutit.shutit_main_dir + '/setup.py)', print_input=False)
	list(shutit.conn_modules)[0].build(shutit)

def finalize_container(shutit):
	"""Finalize the container using the core finalize method.
	"""
	assert len(shutit.conn_modules) == 1
	# Set up the container in pexpect.
	if shutit.cfg['build']['interactive'] >= 2:
		shutit.pause_point('\nFinalizing the conntainer module (' +
			shutit.shutit_main_dir + '/setup.py)', print_input=False)
	list(shutit.conn_modules)[0].finalize(shutit)

# Once we have all the modules, then we can look at dependencies.
# Dependency validation begins.
def resolve_dependencies(shutit, to_build, depender):
	"""Add any required dependencies.
	"""
	cfg = shutit.cfg
	for dependee_id in depender.depends_on:
		dependee = shutit.shutit_map.get(dependee_id)
		# Don't care if module doesn't exist, we check this later
		if (dependee and dependee not in to_build
				and cfg[dependee_id]['build_ifneeded']):
			to_build.append(dependee)
			cfg[dependee_id]['build'] = True

def check_dependee_exists(shutit, depender, dependee, dependee_id):
	"""Checks whether a depended-on module is available.
	"""
	# If the module id isn't there, there's a problem.
	if dependee == None:
		return ('module: \n\n' + dependee_id + '\n\nnot found in paths: ' +
			str(shutit.cfg['host']['shutit_module_paths']) +
			' but needed for ' + depender.module_id +
			'\nCheck your --shutit_module_path setting and ensure that ' +
			'all modules configured to be built are in that path setting, ' +
			'eg "--shutit_module_path /path/to/other/module/:." See also help.')

def check_dependee_build(shutit, depender, dependee, dependee_id):
	"""Checks whether a depended on module is configured to be built.
	"""
	# If depender is installed or will be installed, so must the dependee
	if not (shutit.cfg[dependee.module_id]['build'] or dependee.is_installed(shutit)):
		return ('depender module id:\n\n[' + depender.module_id + ']\n\n' +
			'is configured: "build:yes" or is already built ' +
			'but dependee module_id:\n\n[' + dependee_id + ']\n\n' +
			'is not configured: "build:yes"')

def check_dependee_order(shutit, depender, dependee, dependee_id):
	"""Checks whether run orders are in the appropriate order.
	"""
	# If it depends on a module id, then the module id should be higher up in the run order.
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
		digraph = digraph + '"' + depender.module_id + '"->"' + dependee_id + '";\n'
	return digraph

def check_deps(shutit):
	"""Dependency checking phase is performed in this method.
	"""
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	shutit.log('PHASE: dependencies',code='31')
	if cfg['build']['interactive'] >= 2:
		shutit.pause_point('\nNow checking for dependencies between modules',print_input=False)
	# Get modules we're going to build
	to_build = [
		shutit_map[mid] for mid in shutit_map
		if mid in cfg and cfg[mid]['build']
	]
	# Add any deps we may need by extending to_build and altering cfg
	[resolve_dependencies(shutit, to_build, module) for module in to_build]

	# Dep checking
	def err_checker(errs, triples):
		new_triples = []
		for err, m in zip(errs, triples):
			if not err:
				new_triples.append(m)
				continue
			found_errs.append(err)
		return new_triples

	found_errs = []
	triples = []
	for depender in to_build:
		for dependee_id in depender.depends_on:
			triples.append((depender, shutit_map.get(dependee_id), dependee_id))

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
		shutit.log('Modules configured to be built (in order) are: ',code='31')
		for mid in module_ids(shutit):
			m = shutit_map[mid]
			if cfg[mid]['build']:
				shutit.log(mid + '\t' + str(m.run_order),code='31')
		shutit.log('\n',code='31')

	return []

def check_conflicts(shutit):
	"""Checks for any conflicts between modules configured to be built.
	"""
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	# Now consider conflicts
	shutit.log('PHASE: conflicts',code='31')
	errs = []
	if cfg['build']['interactive'] >= 2:
		shutit.pause_point('\nNow checking for conflicts between modules',print_input=False)
	for mid in module_ids(shutit):
		if not cfg[mid]['build']:
			continue
		conflicter = shutit_map[mid]
		for conflictee in conflicter.conflicts_with:
			# If the module id isn't there, there's no problem.
			conflictee_obj = shutit_map.get(conflictee)
			if conflictee_obj == None:
				continue
			if ((cfg[conflicter.module_id]['build'] or conflicter.is_installed(shutit)) and
					(cfg[conflictee_obj.module_id]['build'] or conflictee_obj.is_installed(shutit))):
				errs.append(('conflicter module id: ' + conflicter.module_id +
					' is configured to be built or is already built but ' +
					'conflicts with module_id: ' + conflictee_obj.module_id,))
	return errs

def check_ready(shutit):
	"""Check that all modules are ready to be built, calling check_ready on each of those
	configured to be built and not already installed (see is_installed).
	"""
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	shutit.log('PHASE: check_ready',code='31')
	errs = []
	if cfg['build']['interactive'] >= 2:
		shutit.pause_point('\nNow checking whether we are ready to build modules configured to be built',
			print_input=False)
	for mid in module_ids(shutit):
		m = shutit_map[mid]
		shutit.log('considering check_ready (is it ready to be built?): ' + mid,code='31')
		if cfg[mid]['build'] and not m.is_installed(shutit):
			shutit.log('checking whether module is ready to build: ' + mid,code='31')
			if not m.check_ready(shutit):
				errs.append((mid + ' not ready to install',shutit.pexpect_children['container_child']))
	return errs

def do_remove(shutit):
	"""Remove modules by calling remove method on those configured for removal.
	"""
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	# Now get the run_order keys in order and go.
	shutit.log('PHASE: remove',code='31')
	if cfg['build']['interactive'] >= 2:
		shutit.pause_point('\nNow removing any modules that need removing',print_input=False)
	for mid in module_ids(shutit):
		m = shutit_map[mid]
		shutit.log('considering whether to remove: ' + mid,code='31')
		if cfg[mid]['remove']:
			shutit.log('removing: ' + mid,code='31')
			if not m.remove(shutit):
				shutit.log(print_modules(shutit),code='31')
				util.fail(mid + ' failed on remove',child=shutit.pexpect_children['container_child'])

def build_module(shutit, module):
	"""Build passed-in module.
	"""
	cfg = shutit.cfg
	shutit.log('building: ' + module.module_id + ' with run order: ' + str(module.run_order),code='31')
	cfg['build']['report'] = cfg['build']['report'] + '\nBuilding: ' + module.module_id + ' with run order: ' + str(module.run_order)
	if not module.build(shutit):
		util.fail(module.module_id + ' failed on build',child=shutit.get_pexpect_children['container_child'])
	if cfg['build']['interactive'] >= 1:
		shutit.pause_point('\nPausing to allow inspect of build for: ' + module.module_id,print_input=True)
	if not module.cleanup(shutit):
		shutit.log('cleaning up: ' + module.module_id + ' with run order: ' + str(module.run_order),code='31')
		util.fail(module.module_id + ' failed on cleanup',child=shutit.pexpect_children['container_child'])
	cfg['build']['report'] = cfg['build']['report'] + '\nCompleted module: ' + module.module_id
	if cfg[module.module_id]['do_repository_work'] or cfg['build']['interactive'] >= 1:
		shutit.log(util.build_report('Module:' + module.module_id),code='31')
	if not cfg[module.module_id]['do_repository_work'] and cfg['build']['interactive'] >= 1:
		cfg[module.module_id]['do_repository_work'] = (
			raw_input('\n\nDo you want to save state now we\'re at the end of this ' +
				'module? (' + module.module_id + ') (in  put y/n)\n' ) == 'y')
	if cfg[module.module_id]['do_repository_work']:
		shutit.log(module.module_id + ' configured to be tagged, doing repository work')
		# Stop all before we tag to avoid file changing errors, and clean up pid files etc..
		stop_all(shutit, module.run_order)
		shutit.do_repository_work(str(module.module_id) + '_' + str(module.run_order),password=cfg['host']['password'],docker_executable=cfg['host']['docker_executable'])
		# Start all after we tag to ensure services are up as expected.
		start_all(shutit, module.run_order)
	if (cfg['build']['interactive'] >= 1 and
			raw_input('\n\nDo you want to stop interactive mode? (input y/n)\n' ) == 'y'):
		cfg['build']['interactive'] = 0

def do_build(shutit):
	"""Runs build phase, building any modules that we've determined need building.
	"""
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	shutit.log('PHASE: build, cleanup, repository work',code='31')
	util.log(util.print_config(shutit.cfg))
	if cfg['build']['interactive'] >= 2:
		shutit.pause_point('\nNow building any modules that need building',print_input=False)
	for mid in module_ids(shutit):
		module = shutit_map[mid]
		shutit.log('considering whether to build: ' + module.module_id,code='31')
		if cfg[module.module_id]['build']:
			if module.is_installed(shutit):
				cfg['build']['report'] = cfg['build']['report'] + '\nBuilt already: ' + module.module_id + ' with run order: ' + str(module.run_order)
			else:
				build_module(shutit, module)
		if is_built(shutit,module):
			shutit.log('Starting module')
			if not module.start(shutit):
				util.fail(module.module_id + ' failed on start',child=shutit.pexpect_children['container_child'])

def do_test(shutit):
	"""Runs test phase, erroring if any return false.
	"""
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	# Test in reverse order
	shutit.log('PHASE: test',code='31')
	if cfg['build']['interactive'] >= 2:
		shutit.pause_point('\nNow doing test phase',print_input=False)
	stop_all(shutit)
	start_all(shutit)
	for mid in module_ids(shutit, rev=True):
		# Only test if it's thought to be installed.
		if is_built(shutit,shutit_map[mid]):
			shutit.log('RUNNING TEST ON: ' + mid,code='31')
			if not shutit_map[mid].test(shutit):
				util.fail(mid + ' failed on test',child=shutit.pexpect_children['container_child'])

def do_finalize(shutit):
	"""Runs finalize phase; run after all builds are complete and all modules have been stopped.
	"""
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	# Stop all the modules
	if cfg['build']['interactive'] == 2:
		shutit.pause_point('\nStopping all modules before finalize phase',print_input=False)
	stop_all(shutit)
	# Finalize in reverse order
	shutit.log('PHASE: finalize',code='31')
	if cfg['build']['interactive'] >= 2:
		shutit.pause_point('\nNow doing finalize phase, which we do when all builds are complete and modules are stopped',print_input=False)
	for mid in module_ids(shutit, rev=True):
		# Only finalize if it's thought to be installed.
		if is_built(shutit,shutit_map[mid]):
			if not shutit_map[mid].finalize(shutit):
				util.fail(mid + ' failed on finalize',child=shutit.pexpect_children['container_child'])

def shutit_module_init(shutit):
	"""Initialize.
	"""
	util.load_from_py_module(shutit, setup)
	util.load_shutit_modules(shutit)
	init_shutit_map(shutit)
	config_collection(shutit)

def shutit_main():
	"""Main ShutIt function.
	
	Handles the configured actions:

	- skeleton    - create skeleton module
	- serve       - run as a server
	- sc          - output computed configuration
	- depgraph    - output digraph of module dependencies
	"""
	if sys.version_info.major == 2:
		if sys.version_info.minor < 7:
			util.fail('Python version must be 2.7+')
	shutit = shutit_global.shutit
	cfg = shutit.cfg

	util.parse_args(cfg)

	if cfg['action']['skeleton']:
		util.create_skeleton(shutit)
		return

	if cfg['action']['serve']:
		import shutit_srv
		shutit_srv.start()
		return

	util.load_configs(shutit)

	if cfg['action']['show_config']:
		shutit.log(util.print_config(cfg),force_stdout=True)
		return

	shutit_module_init(shutit)

	conn_container(shutit)

	errs = []
	errs.extend(check_deps(shutit))
	# Show dependency graph
	if cfg['action']['show_depgraph']:
		digraph = 'digraph depgraph {\n'
		digraph = digraph + '\n'.join([
			make_dep_graph(module) for mid, module in shutit.shutit_map.items()
			if mid in shutit.cfg and shutit.cfg[mid]['build']
		])
		digraph = digraph + '\n}'
		shutit.log(digraph,force_stdout=True)
		return
	errs.extend(check_conflicts(shutit))
	errs.extend(check_ready(shutit))
	if errs:
		shutit.log(print_modules(shutit),code='31')
		child = None
		for err in errs:
			shutit.log(err[0], force_stdout=True,code='31')
			if not child and len(err) > 1:
				child = err[1]
		util.fail("Encountered some errors, quitting", child=child)

	# Dependency validation done.

	do_remove(shutit)
	do_build(shutit)
	do_test(shutit)
	do_finalize(shutit)

	finalize_container(shutit)

	shutit.log(util.build_report('Module: N/A (END)'),prefix=False,force_stdout=True,code='31')

	if shutit.cfg['build']['interactive'] >= 2:
		shutit.log('\nThe build is complete. You should now have a container called ' + shutit.cfg['container']['name'] + ' and a new image if you chose to commit it.\n\nLook and play with the following files from the newly-created module directory to dig deeper:\n\n\tconfigs/default.cnf\n\t*.py\n\nYou can rebuild at any time by running the supplied ./build.sh and run with the supplied ./run.sh.\n\nThere\'s a default test runner in bin/test.sh\n\nYou can inspect the details of the build in the container\'s /root/shutit_build directory.',force_stdout=True,code='31')

if __name__ == '__main__':
	try:
		shutit_main()
	except ShutItException as e:
		print "Error while executing: " + str(e.message)
		sys.exit(1)
