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

from shutit_module import ShutItModule
import util
import shutit_global
import setup
import time
import sys

# Sort a list of module ids by run_order, doesn't modify original list
def run_order_modules(shutit_map, rev=False):
	shutit_id_list = shutit_map.keys()
	ids = sorted(shutit_id_list, key=lambda mid: shutit_map[mid].run_order)
	if rev:
		ids = list(reversed(ids))
	return ids

# Stop all apps less than the supplied run_order
# run_order of -1 means 'stop everything'
def stop_all(config_dict, shutit_map, run_order):
	if config_dict['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nRunning stop on all modules',print_input=False)
	# sort them to it's stopped in reverse order)
	for mid in run_order_modules(shutit_map, rev=True):
		shutit_module_obj = shutit_map[mid]
		if run_order == -1 or shutit_module_obj.run_order <= run_order:
			if is_built(config_dict,shutit_module_obj):
				if not shutit_module_obj.stop(config_dict):
					util.fail('failed to stop: ' + mid,child=util.get_pexpect_child('container_child'))

# Start all apps less than the supplied run_order
def start_all(config_dict, shutit_map, run_order):
	if config_dict['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nRunning start on all modules',print_input=False)
	# sort them to they're started in order)
	for mid in run_order_modules(shutit_map):
		shutit_module_obj = shutit_map[mid]
		if run_order == -1 or shutit_module_obj.run_order <= run_order:
			if is_built(config_dict,shutit_module_obj):
				if not shutit_module_obj.start(config_dict):
					util.fail('failed to start: ' + mid,child=util.get_pexpect_child('container_child'))

# Returns true if this module is configured to be built, or if it is already installed.
def is_built(config_dict,shutit_module_obj):
	return config_dict[shutit_module_obj.module_id]['build'] or shutit_module_obj.is_installed(config_dict)

def shutit_init(config_dict):
	shutit_map = {}
	util.parse_args(config_dict)
	cfg_parser = util.load_configs(config_dict)
	# Now get base config
	util.get_base_config(config_dict, cfg_parser)
	if config_dict['build']['show_config_only']:
		util.log(util.print_config(config_dict),force_stdout=True)
		sys.exit()
	util.load_shutit_modules(config_dict)
	init_shutit_map(config_dict, shutit_map)
	return shutit_map

def init_shutit_map(config_dict, shutit_map):
	# Check for duplicate module details.
	# Set up common config.
	# Set up map of modules.
	util.log(util.red('PHASE: base setup'))
	if config_dict['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),
			'\nChecking to see whether there are duplicate module ids or run orders in the visible modules.',
			print_input=False)
		util.log(util.get_pexpect_child('container_child'),'\nModules I see are:\n',force_stdout=True)
		for m in util.get_shutit_modules():
			util.log(util.red(m.module_id),force_stdout=True)
		util.log('\n',force_stdout=True)
		util.pause_point(util.get_pexpect_child('container_child'),'',print_input=False)

	run_orders = {}
	for m in util.get_shutit_modules():
		assert isinstance(m, ShutItModule)
		if m.module_id in shutit_map:
			util.fail('Duplicated module id: ' + m.module_id)
		if m.run_order in run_orders:
			util.fail('Duplicate run order: ' + str(m.run_order) + ' for ' +
				m.module_id + ' and ' + run_orders[m.run_order].module_id)
		shutit_map[m.module_id] = run_orders[m.run_order] = m

def config_collection(config_dict, shutit_map):
	for mid in run_order_modules(shutit_map):

		# Default to None so we can interpret as ifneeded
		util.get_config(config_dict,mid,'build',None,boolean=True)
		util.get_config(config_dict,mid,'remove',False,boolean=True)
		util.get_config(config_dict,mid,'do_repository_work',False,boolean=True)

		# ifneeded will (by default) only take effect if 'build' is not specified
		# It can, however, be forced to a value, but this should be unusual
		if config_dict[mid]['build'] is None:
			util.get_config(config_dict,mid,'build_ifneeded',True,boolean=True)
			config_dict[mid]['build'] = False
		else:
			util.get_config(config_dict,mid,'build_ifneeded',False,boolean=True)

		if not shutit_map[mid].get_config(config_dict):
			util.fail(mid + ' failed on get_config')

def build_core_module(config_dict, shutit_map):
	# Begin build core module
	_core_module = False
	for mid in run_order_modules(shutit_map):
		# Let's go. Run 0 every time, this should set up the container in pexpect.
		m = shutit_map[mid]
		if m.run_order == 0:
			if config_dict['build']['tutorial']:
				util.pause_point(util.get_pexpect_child('container_child'),
					'\nRunning build on the core module (' + shutit_global.shutit_main_dir + '/setup.py)',
					print_input=False)
			_core_module = True
			m.build(config_dict)
	# Once we have all the modules and the children set up, then we can look at dependencies.
	if not _core_module:
		util.fail('No module with run_order=0 specified! This is required.')
	_core_module = None
	# Finished build core module

# Once we have all the modules, then we can look at dependencies.
# Dependency validation begins.
def resolve_dependencies(config_dict, shutit_map, to_build, depender):
	for dependee_id in depender.depends_on:
		dependee = shutit_map.get(dependee_id)
		# Don't care if module doesn't exist, we check this later
		if (dependee and dependee not in to_build
				and config_dict[dependee_id]['build_ifneeded']):
			to_build.append(dependee)
			config_dict[dependee_id]['build'] = True
def check_dependee_exists(config_dict, depender, dependee, dependee_id):
	# If the module id isn't there, there's a problem.
	if dependee == None:
		return (dependee_id + ' module not found in paths: ' +
			str(config_dict['host']['shutit_module_paths']) +
			' but needed for ' + depender.module_id +
			'\nCheck your --shutit_module_path setting and ensure that ' +
			'all modules configured to be built are in that path setting, ' +
			'eg "--shutit_module_path /path/to/other/module/:." See also help.')
def check_dependee_build(config_dict, depender, dependee, dependee_id):
	# If depender is installed or will be installed, so must the dependee
	if not (config_dict[dependee.module_id]['build'] or dependee.is_installed(config_dict)):
		return ('depender module id: [' + depender.module_id + '] ' +
			'is configured: "build:yes" or is already built ' +
			'but dependee module_id: [' + dependee_id + '] ' +
			'is not configured: "build:yes"')
def check_dependee_order(config_dict, depender, dependee, dependee_id):
	# If it depends on a module id, then the module id should be higher up in the run order.
	if dependee.run_order > depender.run_order:
		return ('depender module id: ' + depender.module_id +
			' (run order: ' + str(depender.run_order) + ') ' +
			'depends on dependee module_id: ' + dependee_id +
			' (run order: ' + str(dependee.run_order) + ') ' +
			'but the latter is configured to run after the former')
def make_dep_graph(config_dict, depender):
	digraph = ''
	for dependee_id in depender.depends_on:
		if config_dict['build']['show_depgraph_only']:
			digraph = digraph + '"' + depender.module_id + '"->"' + dependee_id + '";\n'
	return digraph

def check_deps(config_dict, shutit_map):
	util.log(util.red('PHASE: dependencies'))
	if config_dict['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nNow checking for dependencies between modules',print_input=False)
	# Get modules we're going to build
	to_build = [
		shutit_map[mid] for mid in shutit_map
		if mid in config_dict and config_dict[mid]['build']
	]
	# Add any deps we may need by extending to_build and altering config_dict
	[resolve_dependencies(config_dict, shutit_map, to_build, module) for module in to_build]

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
		check_dependee_exists(config_dict, depender, dependee, dependee_id)
		for depender, dependee, dependee_id in triples
	], triples)
	triples = err_checker([
		check_dependee_build(config_dict, depender, dependee, dependee_id)
		for depender, dependee, dependee_id in triples
	], triples)
	triples = err_checker([
		check_dependee_order(config_dict, depender, dependee, dependee_id)
		for depender, dependee, dependee_id in triples
	], triples)

	if found_errs:
		return found_errs

	# Show dependency graph
	if config_dict['build']['show_depgraph_only']:
		digraph = 'digraph depgraph {\n'
		digraph = digraph + '\n'.join([make_dep_graph(config_dict, module) for module in to_build])
		digraph = digraph + '\n}'
		util.log(digraph,force_stdout=True)
		sys.exit()

	if config_dict['build']['debug']:
		util.log(util.red('Modules configured to be built (in order) are: '))
		for mid in run_order_modules(shutit_map):
			m = shutit_map[mid]
			if config_dict[mid]['build']:
				util.log(util.red(mid + '\t' + str(m.run_order)))
		util.log(util.red('\n'))

	return []

def check_conflicts(config_dict, shutit_map):
	# Now consider conflicts
	util.log(util.red('PHASE: conflicts'))
	if config_dict['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nNow checking for conflicts between modules',print_input=False)
	for mid in run_order_modules(shutit_map):
		if not config_dict[mid]['build']:
			continue
		conflicter = shutit_map[mid]
		for conflictee in conflicter.conflicts_with:
			# If the module id isn't there, there's no problem.
			conflictee_obj = shutit_map.get(conflictee)
			if conflictee_obj == None:
				continue
			if ((config_dict[conflicter.module_id]['build'] or conflicter.is_installed(config_dict)) and
					(config_dict[conflictee_obj.module_id]['build'] or conflictee_obj.is_installed(config_dict))):
				return [('conflicter module id: ' + conflicter.module_id +
					' is configured to be built or is already built but ' +
					'conflicts with module_id: ' + conflictee_obj.module_id,)]
	return []

def check_ready(config_dict, shutit_map):
	util.log(util.red('PHASE: check_ready'))
	if config_dict['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),
			'\nNow checking whether we are ready to build modules configured to be built',
			print_input=False)
	for mid in run_order_modules(shutit_map):
		m = shutit_map[mid]
		if m.run_order == 0: continue
		util.log(util.red('considering check_ready (is it ready to be built?): ' + mid))
		if config_dict[mid]['build'] and not m.is_installed(config_dict):
			util.log(util.red('checking whether module is ready to build: ' + mid))
			if not m.check_ready(config_dict):
				return [(mid + ' not ready to install',util.get_pexpect_child('container_child'))]
	return []


def do_remove(config_dict, shutit_map):
	# Now get the run_order keys in order and go.
	shutit_id_list = run_order_modules(shutit_map)
	util.log(util.red('PHASE: remove'))
	if config_dict['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nNow removing any modules that need removing',print_input=False)
	for mid in shutit_id_list:
		m = shutit_map[mid]
		if m.run_order == 0: continue
		util.log(util.red('considering whether to remove: ' + mid))
		if config_dict[mid]['remove']:
			util.log(util.red('removing: ' + mid))
			if not m.remove(config_dict):
				util.log(util.red(util.print_modules(shutit_map,shutit_id_list,config_dict)))
				util.fail(mid + ' failed on remove',child=util.get_pexpect_child('container_child'))

def build_module(config_dict, shutit_map, module):
	util.log(util.red('building: ' + module.module_id + ' with run order: ' + str(module.run_order)))
	config_dict['build']['report'] = config_dict['build']['report'] + '\nBuilding: ' + module.module_id + ' with run order: ' + str(module.run_order)
	if not module.build(config_dict):
		util.fail(module.module_id + ' failed on build',child=util.get_pexpect_child('container_child'))
	if config_dict['build']['interactive']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nPausing to allow inspect of build for: ' + module.module_id,print_input=True)
	if not module.cleanup(config_dict):
		util.log(util.red('cleaning up: ' + module.module_id + ' with run order: ' + str(module.run_order)))
		util.fail(module.module_id + ' failed on cleanup',child=util.get_pexpect_child('container_child'))
	config_dict['build']['report'] = config_dict['build']['report'] + '\nCompleted module: ' + module.module_id
	if config_dict[module.module_id]['do_repository_work'] or config_dict['build']['interactive']:
		util.log(util.red(util.build_report('Module:' + module.module_id)))
	if (config_dict[module.module_id]['do_repository_work'] or
			(config_dict['build']['interactive'] and raw_input(util.red('\n\nDo you want to save state now we\'re at the ' + 'end of this module? (' + module.module_id + ') (input y/n)\n' )) == 'y')):
		util.log(module.module_id + ' configured to be tagged, doing repository work')
		# Stop all before we tag to avoid file changing errors, and clean up pid files etc..
		stop_all(config_dict, shutit_map, module.run_order)
		util.do_repository_work(config_dict,
			config_dict['expect_prompts']['base_prompt'],
			str(module.module_id) + '_' + str(module.run_order),
			password=config_dict['host']['password'],
			docker_executable=config_dict['host']['docker_executable'],
			force=True)
		# Start all after we tag to ensure services are up as expected.
		start_all(config_dict, shutit_map, module.run_order)
	if (config_dict['build']['interactive'] and
			raw_input(util.red('\n\nDo you want to stop debug and/or interactive mode? (input y/n)\n' )) == 'y'):
		config_dict['build']['interactive'] = False
		config_dict['build']['debug'] = False

def do_build(config_dict, shutit_map):
	util.log(util.red('PHASE: build, cleanup, repository work'))
	if config_dict['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nNow building any modules that need building',print_input=False)
	for mid in run_order_modules(shutit_map):
		module = shutit_map[mid]
		if module.run_order == 0: continue
		util.log(util.red('considering whether to build: ' + module.module_id))
		if config_dict[module.module_id]['build']:
			if module.is_installed(config_dict):
				config_dict['build']['report'] = config_dict['build']['report'] + '\nBuilt already: ' + module.module_id + ' with run order: ' + str(module.run_order)
			else:
				build_module(config_dict, shutit_map, module)
		if is_built(config_dict,module):
			util.log('Starting module')
			if not module.start(config_dict):
				util.fail(module.module_id + ' failed on start',child=util.get_pexpect_child('container_child'))

def do_test(config_dict, shutit_map):
	# Test in reverse order
	util.log(util.red('PHASE: test'))
	if config_dict['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nNow doing test phase',print_input=False)
	stop_all(config_dict, shutit_map, -1)
	start_all(config_dict, shutit_map, -1)
	for mid in run_order_modules(shutit_map, rev=True):
		# Only test if it's thought to be installed.
		if is_built(config_dict,shutit_map[mid]):
			util.log(util.red('RUNNING TEST ON: ' + mid))
			if not shutit_map[mid].test(config_dict):
				util.fail(mid + ' failed on test',child=util.get_pexpect_child('container_child'))

def do_finalize(config_dict, shutit_map):
	# Stop all the modules
	if config_dict['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nStopping all modules before finalize phase',print_input=False)
	stop_all(config_dict, shutit_map, -1)
	# Finalize in reverse order
	util.log(util.red('PHASE: finalize'))
	if config_dict['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nNow doing finalize phase, which we do when all builds are complete and modules are stopped',print_input=False)
	for mid in run_order_modules(shutit_map, rev=True):
		# Only finalize if it's thought to be installed.
		if is_built(config_dict,shutit_map[mid]):
			if not shutit_map[mid].finalize(config_dict):
				util.fail(mid + ' failed on finalize',child=util.get_pexpect_child('container_child'))

def tag_and_push(config_dict):
	if config_dict['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('host_child'),'\nDoing final committing/tagging on the overall container and creating the artifact.',print_input=False)
	# Tag and push etc
	util.do_repository_work(
		config_dict,
		config_dict['expect_prompts']['base_prompt'],
		config_dict['repository']['name'],
		docker_executable=config_dict['host']['docker_executable'],
		password=config_dict['host']['password'])
	# Final exits
	host_child = util.get_pexpect_child('host_child')
	host_child.sendline('exit') # Exit raw bash
	time.sleep(0.3)

def shutit_main():
	config_dict = shutit_global.config_dict
	shutit_map = shutit_init(config_dict)
	shutit_id_list = shutit_map.keys()
	config_collection(config_dict, shutit_map)
	build_core_module(config_dict, shutit_map)

	errs = []
	if not errs: errs = check_deps(config_dict, shutit_map)
	if not errs: errs = check_conflicts(config_dict, shutit_map)
	if not errs: errs = check_ready(config_dict, shutit_map)
	if errs:
		util.log(util.red(util.print_modules(shutit_map,shutit_id_list,config_dict)))
		child = None
		for err in errs:
			util.log(util.red(err[0]), force_stdout=True)
			if not child and len(err) > 1:
				child = err[1]
		util.fail("Encountered some errors, quitting", child=child)

	# Dependency validation done.

	do_remove(config_dict, shutit_map)
	do_build(config_dict, shutit_map)
	do_test(config_dict, shutit_map)
	do_finalize(config_dict, shutit_map)

	tag_and_push(config_dict)

	util.log(util.red(util.build_report('Module: N/A (END)')),prefix=False,force_stdout=True)

	if config_dict['build']['tutorial']:
		util.log(util.red('\nThe build is complete. You should now have a container called ' + config_dict['container']['name'] + ' and a new image if you chose to commit it.\n\nLook and play with the following files from the newly-created module directory to dig deeper:\n\n\tconfigs/default.cnf\n\t*.py\n\nYou can rebuild at any time by running the supplied ./build.sh and run with the supplied ./run.sh.\n\nThere\'s a default test runner in bin/test.sh\n\nYou can inspect the details of the build in the container\'s /root/shutit_build directory.'),force_stdout=True)

if __name__ == '__main__':
	shutit_main()
