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

from shutit_module import ShutItModule, ShutItException
import util
import shutit_global
import shutit_srv
import setup
import time
import sys

# Gets a list of module ids by run_order
def module_ids(shutit, rev=False):
	shutit_map = shutit.shutit_map
	ids = sorted(shutit_map.keys(), key=lambda mid: shutit_map[mid].run_order)
	if rev:
		ids = list(reversed(ids))
	return ids

def print_modules(shutit):
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

# Stop all apps less than the supplied run_order
# run_order of -1 means 'stop everything'
def stop_all(shutit, run_order=-1):
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	if cfg['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nRunning stop on all modules',print_input=False)
	# sort them to it's stopped in reverse order)
	for mid in module_ids(shutit, rev=True):
		shutit_module_obj = shutit_map[mid]
		if run_order == -1 or shutit_module_obj.run_order <= run_order:
			if is_built(shutit,shutit_module_obj):
				if not shutit_module_obj.stop(shutit):
					util.fail('failed to stop: ' + mid,child=util.get_pexpect_child('container_child'))

# Start all apps less than the supplied run_order
def start_all(shutit, run_order=-1):
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	if cfg['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nRunning start on all modules',print_input=False)
	# sort them to they're started in order)
	for mid in module_ids(shutit):
		shutit_module_obj = shutit_map[mid]
		if run_order == -1 or shutit_module_obj.run_order <= run_order:
			if is_built(shutit,shutit_module_obj):
				if not shutit_module_obj.start(shutit):
					util.fail('failed to start: ' + mid,child=util.get_pexpect_child('container_child'))

# Returns true if this module is configured to be built, or if it is already installed.
def is_built(shutit,shutit_module_obj):
	return shutit.cfg[shutit_module_obj.module_id]['build'] or shutit_module_obj.is_installed(shutit)

def init_shutit_map(shutit):
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	# Check we have modules
	# Check for duplicate module details.
	# Set up common config.
	# Set up map of modules.

	modules = util.get_shutit_modules()

	# Have we got anything to process?
	if len(modules) < 2 :
		util.log(modules)
		util.fail('No ShutIt modules in path:\n\n' +
			':'.join(cfg['host']['shutit_module_paths']) +
			'\n\nor their subfolders. Check your --shutit_module_path setting.')

	util.log('PHASE: base setup',code='31')
	if cfg['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),
			'\nChecking to see whether there are duplicate module ids or run orders in the visible modules.',
			print_input=False)
		util.log(util.get_pexpect_child('container_child'),'\nModules I see are:\n',force_stdout=True)
		for m in modules:
			util.log(m.module_id,force_stdout=True,code='31')
		util.log('\n',force_stdout=True)
		util.pause_point(util.get_pexpect_child('container_child'),'',print_input=False)

	run_orders = {}
	has_core_module = False
	for m in modules:
		assert isinstance(m, ShutItModule)
		if m.module_id in shutit_map:
			util.fail('Duplicated module id: ' + m.module_id)
		if m.run_order in run_orders:
			util.fail('Duplicate run order: ' + str(m.run_order) + ' for ' +
				m.module_id + ' and ' + run_orders[m.run_order].module_id)
		if m.run_order < 0:
			util.fail('Invalid run order ' + str(m.run_order) + ' for ' +
				m.module_id)
		if m.run_order == 0:
			has_core_module = True
		shutit_map[m.module_id] = run_orders[m.run_order] = m

	if not has_core_module:
		util.fail('No module with run_order=0 specified! This is required.')

def config_collection(shutit):
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

def build_core_module(shutit):
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	# Let's go. Run 0 every time, this should set up the container in pexpect.
	core_mid = module_ids(shutit)[0]
	if cfg['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),
			'\nRunning build on the core module (' +
			shutit.shutit_main_dir + '/setup.py)', print_input=False)
	shutit_map[core_mid].build(shutit)

# Once we have all the modules, then we can look at dependencies.
# Dependency validation begins.
def resolve_dependencies(shutit, to_build, depender):
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	for dependee_id in depender.depends_on:
		dependee = shutit_map.get(dependee_id)
		# Don't care if module doesn't exist, we check this later
		if (dependee and dependee not in to_build
				and cfg[dependee_id]['build_ifneeded']):
			to_build.append(dependee)
			cfg[dependee_id]['build'] = True
def check_dependee_exists(shutit, depender, dependee, dependee_id):
	# If the module id isn't there, there's a problem.
	if dependee == None:
		return ('module: \n\n' + dependee_id + '\n\nnot found in paths: ' +
			str(shutit.cfg['host']['shutit_module_paths']) +
			' but needed for ' + depender.module_id +
			'\nCheck your --shutit_module_path setting and ensure that ' +
			'all modules configured to be built are in that path setting, ' +
			'eg "--shutit_module_path /path/to/other/module/:." See also help.')
def check_dependee_build(shutit, depender, dependee, dependee_id):
	# If depender is installed or will be installed, so must the dependee
	if not (shutit.cfg[dependee.module_id]['build'] or dependee.is_installed(shutit)):
		return ('depender module id:\n\n[' + depender.module_id + ']\n\n' +
			'is configured: "build:yes" or is already built ' +
			'but dependee module_id:\n\n[' + dependee_id + ']\n\n' +
			'is not configured: "build:yes"')
def check_dependee_order(shutit, depender, dependee, dependee_id):
	# If it depends on a module id, then the module id should be higher up in the run order.
	if dependee.run_order > depender.run_order:
		return ('depender module id:\n\n' + depender.module_id +
			'\n\n(run order: ' + str(depender.run_order) + ') ' +
			'depends on dependee module_id:\n\n' + dependee_id +
			'\n\n(run order: ' + str(dependee.run_order) + ') ' +
			'but the latter is configured to run after the former')
def make_dep_graph(depender):
	digraph = ''
	for dependee_id in depender.depends_on:
		digraph = digraph + '"' + depender.module_id + '"->"' + dependee_id + '";\n'
	return digraph

def check_deps(shutit):
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	util.log('PHASE: dependencies',code='31')
	if cfg['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nNow checking for dependencies between modules',print_input=False)
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
		util.log('Modules configured to be built (in order) are: ',code='31')
		for mid in module_ids(shutit):
			m = shutit_map[mid]
			if cfg[mid]['build']:
				util.log(mid + '\t' + str(m.run_order),code='31')
		util.log('\n',code='31')

	return []

def check_conflicts(shutit):
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	# Now consider conflicts
	util.log('PHASE: conflicts',code='31')
	errs = []
	if cfg['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nNow checking for conflicts between modules',print_input=False)
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
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	util.log('PHASE: check_ready',code='31')
	errs = []
	if cfg['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),
			'\nNow checking whether we are ready to build modules configured to be built',
			print_input=False)
	for mid in module_ids(shutit):
		m = shutit_map[mid]
		if m.run_order == 0: continue
		util.log('considering check_ready (is it ready to be built?): ' + mid,code='31')
		if cfg[mid]['build'] and not m.is_installed(shutit):
			util.log('checking whether module is ready to build: ' + mid,code='31')
			if not m.check_ready(shutit):
				errs.append((mid + ' not ready to install',util.get_pexpect_child('container_child')))
	return errs

def do_remove(shutit):
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	# Now get the run_order keys in order and go.
	util.log('PHASE: remove',code='31')
	if cfg['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nNow removing any modules that need removing',print_input=False)
	for mid in module_ids(shutit):
		m = shutit_map[mid]
		if m.run_order == 0: continue
		util.log('considering whether to remove: ' + mid,code='31')
		if cfg[mid]['remove']:
			util.log('removing: ' + mid,code='31')
			if not m.remove(shutit):
				util.log(print_modules(shutit),code='31')
				util.fail(mid + ' failed on remove',child=util.get_pexpect_child('container_child'))

def build_module(shutit, module):
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	util.log('building: ' + module.module_id + ' with run order: ' + str(module.run_order),code='31')
	cfg['build']['report'] = cfg['build']['report'] + '\nBuilding: ' + module.module_id + ' with run order: ' + str(module.run_order)
	if not module.build(shutit):
		util.fail(module.module_id + ' failed on build',child=util.get_pexpect_child('container_child'))
	if cfg['build']['interactive']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nPausing to allow inspect of build for: ' + module.module_id,print_input=True)
	if not module.cleanup(shutit):
		util.log('cleaning up: ' + module.module_id + ' with run order: ' + str(module.run_order),code='31')
		util.fail(module.module_id + ' failed on cleanup',child=util.get_pexpect_child('container_child'))
	cfg['build']['report'] = cfg['build']['report'] + '\nCompleted module: ' + module.module_id
	if cfg[module.module_id]['do_repository_work'] or cfg['build']['interactive']:
		util.log(util.build_report('Module:' + module.module_id),code='31')
	if not cfg[module.module_id]['do_repository_work'] and cfg['build']['interactive']:
		cfg[module.module_id]['do_repository_work'] = (
			raw_input('\n\nDo you want to save state now we\'re at the end of this ' +
				'module? (' + module.module_id + ') (in  put y/n)\n' ) == 'y')
	if cfg[module.module_id]['do_repository_work']:
		util.log(module.module_id + ' configured to be tagged, doing repository work')
		# Stop all before we tag to avoid file changing errors, and clean up pid files etc..
		stop_all(shutit, module.run_order)
		util.do_repository_work(cfg,
			cfg['expect_prompts']['base_prompt'],
			str(module.module_id) + '_' + str(module.run_order),
			password=cfg['host']['password'],
			docker_executable=cfg['host']['docker_executable'])
		# Start all after we tag to ensure services are up as expected.
		start_all(shutit, module.run_order)
	if (cfg['build']['interactive'] and
			raw_input('\n\nDo you want to stop debug and/or interactive mode? (input y/n)\n' ) == 'y'):
		cfg['build']['interactive'] = False
		cfg['build']['debug'] = False

def do_build(shutit):
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	util.log('PHASE: build, cleanup, repository work',code='31')
	if cfg['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nNow building any modules that need building',print_input=False)
	for mid in module_ids(shutit):
		module = shutit_map[mid]
		if module.run_order == 0: continue
		util.log('considering whether to build: ' + module.module_id,code='31')
		if cfg[module.module_id]['build']:
			if module.is_installed(shutit):
				cfg['build']['report'] = cfg['build']['report'] + '\nBuilt already: ' + module.module_id + ' with run order: ' + str(module.run_order)
			else:
				build_module(shutit, module)
		if is_built(shutit,module):
			util.log('Starting module')
			if not module.start(shutit):
				util.fail(module.module_id + ' failed on start',child=util.get_pexpect_child('container_child'))

def do_test(shutit):
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	# Test in reverse order
	util.log('PHASE: test',code='31')
	if cfg['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nNow doing test phase',print_input=False)
	stop_all(shutit)
	start_all(shutit)
	for mid in module_ids(shutit, rev=True):
		# Only test if it's thought to be installed.
		if is_built(shutit,shutit_map[mid]):
			util.log('RUNNING TEST ON: ' + mid,code='31')
			if not shutit_map[mid].test(shutit):
				util.fail(mid + ' failed on test',child=util.get_pexpect_child('container_child'))

def do_finalize(shutit):
	cfg = shutit.cfg
	shutit_map = shutit.shutit_map
	# Stop all the modules
	if cfg['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nStopping all modules before finalize phase',print_input=False)
	stop_all(shutit)
	# Finalize in reverse order
	util.log('PHASE: finalize',code='31')
	if cfg['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nNow doing finalize phase, which we do when all builds are complete and modules are stopped',print_input=False)
	for mid in module_ids(shutit, rev=True):
		# Only finalize if it's thought to be installed.
		if is_built(shutit,shutit_map[mid]):
			if not shutit_map[mid].finalize(shutit):
				util.fail(mid + ' failed on finalize',child=util.get_pexpect_child('container_child'))

def tag_and_push(cfg):
	if cfg['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('host_child'),'\nDoing final committing/tagging on the overall container and creating the artifact.',print_input=False)
	# Tag and push etc
	util.do_repository_work(
		cfg,
		cfg['expect_prompts']['base_prompt'],
		cfg['repository']['name'],
		docker_executable=cfg['host']['docker_executable'],
		password=cfg['host']['password'])
	# Final exits
	host_child = util.get_pexpect_child('host_child')
	host_child.sendline('exit') # Exit raw bash
	time.sleep(0.3)

def shutit_main():
	if sys.version_info.major == 2:
		if sys.version_info.minor < 7:
			util.fail('Python version must be 2.7+')
	shutit = shutit_global.shutit
	cfg = shutit.cfg

	util.parse_args(cfg)

	util.load_configs(shutit)
	# Now get base config
	if cfg['action']['show_config']:
		util.log(util.print_config(cfg),force_stdout=True)
		return
	util.load_shutit_modules(shutit)
	init_shutit_map(shutit)
	config_collection(shutit)
	build_core_module(shutit)

	if cfg['action']['serve']:
		shutit_srv.start()
		return

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
		util.log(digraph,force_stdout=True)
		return
	errs.extend(check_conflicts(shutit))
	errs.extend(check_ready(shutit))
	if errs:
		util.log(print_modules(shutit),code='31')
		child = None
		for err in errs:
			util.log(err[0], force_stdout=True,code='31')
			if not child and len(err) > 1:
				child = err[1]
		util.fail("Encountered some errors, quitting", child=child)

	# Dependency validation done.

	do_remove(shutit)
	do_build(shutit)
	do_test(shutit)
	do_finalize(shutit)

	tag_and_push(shutit.cfg)

	util.log(util.build_report('Module: N/A (END)'),prefix=False,force_stdout=True,code='31')

	if shutit.cfg['build']['tutorial']:
		util.log('\nThe build is complete. You should now have a container called ' + shutit.cfg['container']['name'] + ' and a new image if you chose to commit it.\n\nLook and play with the following files from the newly-created module directory to dig deeper:\n\n\tconfigs/default.cnf\n\t*.py\n\nYou can rebuild at any time by running the supplied ./build.sh and run with the supplied ./run.sh.\n\nThere\'s a default test runner in bin/test.sh\n\nYou can inspect the details of the build in the container\'s /root/shutit_build directory.',force_stdout=True,code='31')

if __name__ == '__main__':
	try:
		shutit_main()
	except ShutItException as e:
		print "Error while executing: " + str(e.message)
		sys.exit(1)
