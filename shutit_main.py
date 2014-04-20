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

# Prevent shutit being imported unless people really know what they're doing
if __name__ == 'shutit_main' and '_import_shutit' not in globals():
	raise Exception('ShutIt should be used as a command line tool')

from shutit_module import ShutItModule
import util
import shutit_global
import setup
import time
import sys

# Sort a list of module ids by run_order, doesn't modify original list
def run_order_modules(shutit_id_list):
	return sorted(shutit_id_list, key=lambda mid: shutit_map[mid].run_order)

# Stop all apps less than the supplied run_order
# run_order of -1 means 'stop everything'
def stop_all(shutit_id_list,config_dict,run_order):
	if config_dict['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nRunning stop on all modules',print_input=False)
	# sort them to it's stopped in reverse order)
	for mid in reversed(run_order_modules(shutit_id_list)):
		shutit_module_obj = shutit_map[mid]
		if run_order == -1 or shutit_module_obj.run_order <= run_order:
			if is_built(config_dict,shutit_module_obj):
				if not shutit_module_obj.stop(config_dict):
					util.fail('failed to stop: ' + mid,child=util.get_pexpect_child('container_child'))

# Start all apps less than the supplied run_order
def start_all(shutit_id_list,config_dict,run_order):
	if config_dict['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nRunning start on all modules',print_input=False)
	# sort them to they're started in order)
	for mid in run_order_modules(shutit_id_list):
		shutit_module_obj = shutit_map[mid]
		if shutit_module_obj.run_order <= run_order:
			if is_built(config_dict,shutit_module_obj):
				if not shutit_module_obj.start(config_dict):
					util.fail('failed to start: ' + mid,child=util.get_pexpect_child('container_child'))

# Returns true if this module is configured to be built, or if it is already installed.
def is_built(config_dict,shutit_module_obj):
	return config_dict[shutit_module_obj.module_id]['build'] or shutit_module_obj.is_installed(config_dict)


shutit_map = {}
config_dict = shutit_global.config_dict
util.parse_args(config_dict)
cfg_parser = util.load_configs(config_dict)
# Now get base config
util.get_base_config(config_dict, cfg_parser)
if config_dict['build']['show_config_only']:
	util.log(util.print_config(config_dict),force_stdout=True)
	sys.exit()
util.load_shutit_modules(config_dict)

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

for m in util.get_shutit_modules():
	assert isinstance(m, ShutItModule)
	# module_id should be unique
	for n in util.get_shutit_modules():
		if n == m:
			continue
		if m.module_id == n.module_id:
			util.fail('Duplicate module ids! ' + m.module_id + ' for ' + m.module_id + ' and ' + n.module_id)
		if m.run_order == n.run_order:
			util.fail('Duplicate run order! ' + str(m.run_order) + ' for ' + m.module_id + ' and ' + n.module_id)
	# map the module id to the object
	shutit_map.update({m.module_id:m})

shutit_id_list = shutit_map.keys()
# Now sort the list by run order
shutit_id_list = run_order_modules(shutit_id_list)

# Begin config collection
for mid in shutit_id_list:
	util.get_config(config_dict,mid,'build',False,boolean=True)
	util.get_config(config_dict,mid,'remove',False,boolean=True)
	util.get_config(config_dict,mid,'do_repo_work',False,boolean=True)

for mid in shutit_id_list:
	m = shutit_map[mid]
	if not m.get_config(config_dict):
		util.fail(mid + ' failed on get_config')

if config_dict['build']['debug']:
	util.log(util.red('Modules configured to be built (in order) are: '))
	for mid in shutit_id_list:
		m = shutit_map[mid]
		if config_dict[mid]['build']:
			util.log(util.red(mid + '\t' + str(m.run_order)))
	util.log(util.red('\n'))
# Finished config collection


# Begin build core module
_core_module = False
for mid in shutit_id_list:
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

to_build = [
	shutit_map[mid] for mid in shutit_map
	if mid in config_dict and config_dict[mid]['build']
]

# Once we have all the modules, then we can look at dependencies.
# Dependency validation begins.
util.log(util.red('PHASE: dependencies'))
if config_dict['build']['tutorial']:
	util.pause_point(util.get_pexpect_child('container_child'),'\nNow checking for dependencies between modules',print_input=False)
def check_dependees_exist(depender, shutit_map):
	for dependee_id in depender.depends_on:
		dependee = shutit_map.get(dependee_id)
		# If the module id isn't there, there's a problem.
		if dependee == None:
			util.log(util.red(util.print_modules(shutit_map,shutit_id_list,config_dict)))
			util.fail(dependee_id + ' module not found in paths: ' + str(config_dict['host']['shutit_module_paths']) +
				'\nCheck your --shutit_module_path setting and ensure that ' +
				'all modules configured to be built are in that path setting, ' +
				'eg "--shutit_module_path /path/to/other/module/:." See also help.')
def check_dependees_build(depender, shutit_map):
	depender_is_installed = depender.is_installed(config_dict)
	for dependee_id in depender.depends_on:
		dependee = shutit_map.get(dependee_id)
		# If depender is installed or will be installed, so must the dependee
		if ((config_dict[depender.module_id]['build'] or depender_is_installed) and not
				config_dict[dependee.module_id]['build'] and not dependee.is_installed(config_dict)):
			util.log(util.red(util.print_modules(shutit_map,shutit_id_list,config_dict)))
			util.fail('depender module id: [' + depender.module_id + '] ' +
				'is configured: "build:yes" or is already built ' +
				'but dependee module_id: [' + dependee_id + '] ' +
				'is not configured: "build:yes"')
def check_dependees_order(depender, shutit_map):
	for dependee_id in depender.depends_on:
		dependee = shutit_map.get(dependee_id)
		# If it depends on a module id, then the module id should be higher up in the run order.
		if dependee.run_order > depender.run_order:
			util.log(util.red(util.print_modules(shutit_map,shutit_id_list,config_dict)))
			util.fail('depender module id: ' + depender.module_id +
				' (run order: ' + str(depender.run_order) + ') ' +
				'depends on dependee module_id: ' + dependee_id +
				' (run order: ' + str(dependee.run_order) + ') ' +
				'but the latter is configured to run after the former')
def make_dep_graph(depender):
	digraph = ''
	for dependee_id in depender.depends_on:
		if config_dict['build']['show_depgraph_only']:
			digraph = digraph + '"' + depender.module_id + '"->"' + dependee_id + '";\n'
	return digraph
# Do dep checking
[check_dependees_exist(module, shutit_map) for module in to_build]
[check_dependees_build(module, shutit_map) for module in to_build]
[check_dependees_order(module, shutit_map) for module in to_build]
# Show dependency graph
if config_dict['build']['show_depgraph_only']:
	digraph = 'digraph depgraph {\n'
	digraph = digraph + '\n'.join([make_dep_graph(module) for module in to_build])
	digraph = digraph + '\n}'
	util.log('\n',digraph,force_stdout=True)
	sys.exit()

# Now consider conflicts
util.log(util.red('PHASE: conflicts'))
if config_dict['build']['tutorial']:
	util.pause_point(util.get_pexpect_child('container_child'),'\nNow checking for conflicts between modules',print_input=False)
for conflicter in to_build:
	for conflictee in conflicter.conflicts_with:
		# If the module id isn't there, there's no problem.
		conflictee_obj = shutit_map.get(conflictee)
		if conflictee_obj == None:
			continue
		if ((config_dict[conflicter.module_id]['build'] or conflicter.is_installed(config_dict)) and
				(config_dict[conflictee_obj.module_id]['build'] or conflictee_obj.is_installed(config_dict))):
			util.log(util.red(util.print_modules(shutit_map,shutit_id_list,config_dict)))
			util.fail('conflicter module id: ' + conflicter.module_id +
				' is configured to be built or is already built but ' +
				'conflicts with module_id: ' + conflictee_obj.module_id)

util.log(util.red('PHASE: check_ready'))
if config_dict['build']['tutorial']:
	util.pause_point(util.get_pexpect_child('container_child'),
		'\nNow checking whether we are ready to build modules configured to be built',
		print_input=False)
for mid in shutit_id_list:
	m = shutit_map[mid]
	if m.run_order == 0: continue
	util.log(util.red('considering check_ready (is it ready to be built?): ' + mid))
	if config_dict[mid]['build'] and not m.is_installed(config_dict):
		util.log(util.red('checking whether module is ready to build: ' + mid))
		if not m.check_ready(config_dict):
			util.log(util.red(util.print_modules(shutit_map,shutit_id_list,config_dict)))
			util.fail(mid + ' not ready to install',child=util.get_pexpect_child('container_child'))
# Dependency validation done.

# Now get the run_order keys in order and go.
shutit_id_list = run_order_modules(shutit_id_list)
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
shutit_id_list = run_order_modules(shutit_id_list)
util.log(util.red('PHASE: build, cleanup, repository work'))
if config_dict['build']['tutorial']:
	util.pause_point(util.get_pexpect_child('container_child'),'\nNow building any modules that need building',print_input=False)
for mid in shutit_id_list:
	module = shutit_map[mid]
	if module.run_order == 0: continue
	util.log(util.red('considering whether to build: ' + module.module_id))
	if config_dict[module.module_id]['build'] and not module.is_installed(config_dict):
		util.log(util.red('building: ' + module.module_id + ' with run order: ' + str(module.run_order)))
		config_dict['build']['report'] = config_dict['build']['report'] + '\nBuilding: ' + module.module_id + ' with run order: ' + str(module.run_order)
		if not module.build(config_dict):
			util.log(util.red('building: ' + module.module_id + ' with run order: ' + str(module.run_order)))
			util.fail(module.module_id + ' failed on build',child=util.get_pexpect_child('container_child'))
		if config_dict['build']['interactive']:
			util.pause_point(util.get_pexpect_child('container_child'),'\nPausing to allow inspect of build for: ' + module.module_id,print_input=True)
		if not module.cleanup(config_dict):
			util.log(util.red('cleaning up: ' + module.module_id + ' with run order: ' + str(module.run_order)))
			util.fail(module.module_id + ' failed on cleanup',child=util.get_pexpect_child('container_child'))
		config_dict['build']['report'] = config_dict['build']['report'] + '\nCompleted module: ' + module.module_id
		if config_dict[module.module_id]['do_repo_work'] or config_dict['build']['interactive']:
			util.log(util.red(util.build_report('Module:' + module.module_id)))
		if (config_dict[module.module_id]['do_repo_work'] or
				(config_dict['build']['interactive'] and raw_input(util.red('\n\nDo you want to save state now we\'re at the ' + 'end of this module? (' + module.module_id + ') (input y/n)\n' )) == 'y')):
			util.log(module.module_id + ' configured to be tagged, doing repository work')
			# Stop all before we tag to avoid file changing errors, and clean up pid files etc..
			stop_all(shutit_id_list,config_dict,module.run_order)
			util.do_repository_work(config_dict,
				config_dict['expect_prompts']['base_prompt'],
				str(module.module_id),
				repo_suffix=str(module.run_order),
				password=config_dict['host']['password'],
				docker_executable=config_dict['host']['docker_executable'],
				force=True)
			# Start all before we tag to ensure services are up as expected.
			start_all(shutit_id_list,config_dict,module.run_order)
		if (config_dict['build']['interactive'] and
				raw_input(util.red('\n\nDo you want to stop debug and/or interactive mode? (input y/n)\n' )) == 'y'):
			config_dict['build']['interactive'] = False
			config_dict['build']['debug'] = False
	if is_built(config_dict,module):
		util.log('Starting module')
		if not module.start(config_dict):
			util.fail(module.module_id + ' failed on start',child=util.get_pexpect_child('container_child'))

# Test in reverse order
shutit_id_list = reversed(run_order_modules(shutit_id_list))
util.log(util.red('PHASE: test'))
if config_dict['build']['tutorial']:
	util.pause_point(util.get_pexpect_child('container_child'),'\nNow doing test phase',print_input=False)
stop_all(shutit_id_list,config_dict,module.run_order)
start_all(shutit_id_list,config_dict,module.run_order)
for mid in shutit_id_list:
	# Only test if it's thought to be installed.
	if is_built(config_dict,shutit_map[mid]):
		util.log(util.red('RUNNING TEST ON: ' + mid))
		if not shutit_map[mid].test(config_dict):
			util.fail(mid + ' failed on test',child=util.get_pexpect_child('container_child'))

# Stop all the modules
if config_dict['build']['tutorial']:
	util.pause_point(util.get_pexpect_child('container_child'),'\nStopping all modules before finalize phase',print_input=False)
stop_all(shutit_id_list,config_dict,-1)

# Finalize in reverse order
shutit_id_list = reversed(run_order_modules(shutit_id_list))
util.log(util.red('PHASE: finalize'))
if config_dict['build']['tutorial']:
	util.pause_point(util.get_pexpect_child('container_child'),'\nNow doing finalize phase, which we do when all builds are complete and modules are stopped',print_input=False)
for mid in shutit_id_list:
	# Only finalize if it's thought to be installed.
	if is_built(config_dict,shutit_map[mid]):
		if not shutit_map[mid].finalize(config_dict):
			util.fail(mid + ' failed on finalize',child=util.get_pexpect_child('container_child'))

# Tag and push etc
util.do_repository_work(config_dict,config_dict['expect_prompts']['base_prompt'],config_dict['repository']['name'],docker_executable=config_dict['host']['docker_executable'],password=config_dict['host']['password'])
# Final exits
host_child = util.get_pexpect_child('host_child')
host_child.sendline('exit') # Exit raw bash
time.sleep(0.3)

# Finally, do repo work on the core module.
for module in shutit_map.values():
	if module.run_order == 0:
		core_module = module
		break
if config_dict[core_module.module_id]['do_repo_work']:
	if config_dict['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('host_child'),'\nDoing final committing/tagging on the overall container and creating the artifact.',print_input=False)
	util.log(util.red('doing repo work: ' + core_module.module_id + ' with run order: ' + str(core_module.run_order)))
	util.do_repository_work(config_dict,
		config_dict['expect_prompts']['base_prompt'],
		str(core_module.run_order),
		password=config_dict['host']['password'],
		docker_executable=config_dict['host']['docker_executable'])

util.log(util.red(util.build_report('Module: N/A (END)')),prefix=False,force_stdout=True)

if config_dict['build']['tutorial']:
	util.log(util.red('\nThe build is complete. You should now have a container called ' + config_dict['container']['name'] + ' and a new image if you chose to commit it.\n\nLook and play with the following files from the newly-created module directory to dig deeper:\n\n\tconfigs/default.cnf\n\t*.py\n\nYou can rebuild at any time by running the supplied ./build.sh and run with the supplied ./run.sh.\n\nThere\'s a default test runner in bin/test.sh\n\nYou can inspect the details of the build in the container\'s /root/shutit_build directory.'),force_stdout=True)
