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
import decimal

# Stop all apps less than the supplied run_order
# run_order of -1 means 'stop everything'
def stop_all(shutit_map_list,config_dict,run_order):
	if config_dict['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nRunning stop on all modules',print_input=False)
	# sort them to it's stopped in reverse order)
	shutit_map_list.sort()
	shutit_map_list.reverse()
	for k in shutit_map_list:
		if run_order == -1 or k <= run_order:
			shutit_module_obj = shutit_map.get(k)
			if is_built(config_dict,shutit_module_obj):
				if not shutit_module_obj.stop(config_dict):
					util.fail('failed to stop: ' + shutit_module_obj.module_id,child=util.get_pexpect_child('container_child'))

# Start all apps less than the supplied run_order
def start_all(shutit_map_list,config_dict,run_order):
	if config_dict['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('container_child'),'\nRunning start on all modules',print_input=False)
	# sort them to they're started in order)
	shutit_map_list.sort()
	for k in shutit_map_list:
		if k <= run_order:
			shutit_module_obj = shutit_map.get(k)
			if is_built(config_dict,shutit_module_obj):
				if not shutit_module_obj.start(config_dict):
					util.fail('failed to start: ' + shutit_module_obj.module_id,child=util.get_pexpect_child('container_child'))

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
	# map the module id and the run_order to the object
	# Since one should be an integer and one a string they should not overlap.
	shutit_map.update({m.module_id:m})
	shutit_map.update({m.run_order:m})

shutit_map_list = []
# We only want the decimals in this list
for i in shutit_map.keys():
	if isinstance(i,decimal.Decimal):
		shutit_map_list.append(i)
# Now sort the list by decimal order
shutit_map_list.sort()

# Begin config collection
for k in shutit_map_list:
	m = shutit_map.get(k)
	util.get_config(config_dict,m.module_id,'build',False,boolean=True)
	util.get_config(config_dict,m.module_id,'remove',False,boolean=True)
	util.get_config(config_dict,m.module_id,'do_repo_work',False,boolean=True)

for k in shutit_map_list:
	m = shutit_map.get(k)
	if not m.get_config(config_dict):
		util.fail(m.module_id + ' failed on get_config')

if config_dict['build']['debug']:
	util.log(util.red('Modules configured to be built (in order) are: '))
	for k in shutit_map_list:
		m = shutit_map.get(k)
		if config_dict[m.module_id]['build']:
			util.log(util.red(m.module_id + '\t' + str(m.run_order)))
	util.log(util.red('\n'))
# Finished config collection


# Begin build core module
_core_module = False
for k in shutit_map_list:
	# Let's go. Run 0 every time, this should set up the container in pexpect.
	m = shutit_map.get(k)
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
util.log(util.red('PHASE: dependencies'))
if config_dict['build']['show_depgraph_only']:
	digraph = 'digraph depgraph {\n'
if config_dict['build']['tutorial']:
	util.pause_point(util.get_pexpect_child('container_child'),'\nNow checking for dependencies between modules',print_input=False)
to_build = [
	shutit_map[mid] for mid in shutit_map
	if isinstance(mid, str) and # filter out run orders
		mid in config_dict and
		config_dict[mid]['build']
]
for depender in to_build:
	depender_is_installed = depender.is_installed(config_dict)
	for dependee in depender.depends_on:
		dependee_obj = shutit_map.get(dependee)
		if config_dict['build']['show_depgraph_only']:
			digraph = digraph + '"' + depender.module_id + '"->"' + dependee_obj.module_id + '";\n'
		# If the module id isn't there, there's a problem.
		if dependee_obj == None:
			util.log(util.red(util.print_modules(shutit_map,shutit_map_list,config_dict)))
			util.fail(dependee + ' module not found in paths: ' + str(config_dict['host']['shutit_module_paths']) +
				'\nCheck your --shutit_module_path setting and ensure that ' +
				'all modules configured to be built are in that path setting, ' +
				'eg "--shutit_module_path /path/to/other/module/:." See also help.')
		# If it depends on a module id, then the module id should be higher up in the run order.
		if dependee_obj.run_order > depender.run_order:
			util.log(util.red(util.print_modules(shutit_map,shutit_map_list,config_dict)))
			util.fail('depender module id: ' + depender.module_id +
				' (run order: ' + str(depender.run_order) + ') ' +
				'depends on dependee module_id: ' + dependee_obj.module_id +
				' (run order: ' + str(dependee_obj.run_order) + ') ' +
				'but the latter is configured to run after the former')
		# If depender is installed or will be installed, so must the dependee
		if ((config_dict[depender.module_id]['build'] or depender_is_installed) and not
				config_dict[dependee_obj.module_id]['build'] and not dependee_obj.is_installed(config_dict)):
			util.log(util.red(util.print_modules(shutit_map,shutit_map_list,config_dict)))
			util.fail('depender module id: [' + depender.module_id + '] ' +
				'is configured: "build:yes" or is already built ' +
				'but dependee module_id: [' + dependee_obj.module_id + '] ' +
				'is not configured: "build:yes"')
# Show dependency graph
if config_dict['build']['show_depgraph_only']:
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
			util.log(util.red(util.print_modules(shutit_map,shutit_map_list,config_dict)))
			util.fail('conflicter module id: ' + conflicter.module_id +
				' is configured to be built or is already built but ' +
				'conflicts with module_id: ' + conflictee_obj.module_id)

util.log(util.red('PHASE: check_ready'))
if config_dict['build']['tutorial']:
	util.pause_point(util.get_pexpect_child('container_child'),
		'\nNow checking whether we are ready to build modules configured to be built',
		print_input=False)
for k in shutit_map_list:
	if k == 0: continue
	util.log(util.red('considering check_ready (is it ready to be built?): ' + shutit_map.get(k).module_id))
	if config_dict[shutit_map.get(k).module_id]['build'] and not shutit_map.get(k).is_installed(config_dict):
		util.log(util.red('checking whether module is ready to build: ' + shutit_map.get(k).module_id))
		if not shutit_map.get(k).check_ready(config_dict):
			util.log(util.red(util.print_modules(shutit_map,shutit_map_list,config_dict)))
			util.fail(shutit_map.get(k).module_id + ' not ready to install',child=util.get_pexpect_child('container_child'))
# Dependency validation done.

# Now get the run_order keys in order and go.
shutit_map_list.sort()
util.log(util.red('PHASE: remove'))
if config_dict['build']['tutorial']:
	util.pause_point(util.get_pexpect_child('container_child'),'\nNow removing any modules that need removing',print_input=False)
for k in shutit_map_list:
	if k == 0: continue
	util.log(util.red('considering whether to remove: ' + shutit_map.get(k).module_id))
	if config_dict[shutit_map.get(k).module_id]['remove']:
		util.log(util.red('removing: ' + shutit_map.get(k).module_id))
		if not shutit_map.get(k).remove(config_dict):
			util.log(util.red(util.print_modules(shutit_map,shutit_map_list,config_dict)))
			util.fail(shutit_map.get(k).module_id + ' failed on remove',child=util.get_pexpect_child('container_child'))
shutit_map_list.sort()
util.log(util.red('PHASE: build, cleanup, repository work'))
if config_dict['build']['tutorial']:
	util.pause_point(util.get_pexpect_child('container_child'),'\nNow building any modules that need building',print_input=False)
for k in shutit_map_list:
	if k == 0: continue
	module = shutit_map.get(k)
	util.log(util.red('considering whether to build: ' + module.module_id))
	if config_dict[module.module_id]['build']:
		print module.is_installed(config_dict)
		if not module.is_installed(config_dict):
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
				stop_all(shutit_map_list,config_dict,module.run_order)
				util.do_repository_work(config_dict,
					config_dict['expect_prompts']['base_prompt'],
					str(module.module_id),
					repo_suffix=str(module.run_order),
					password=config_dict['host']['password'],
					docker_executable=config_dict['host']['docker_executable'],
					force=True)
				# Start all before we tag to ensure services are up as expected.
				start_all(shutit_map_list,config_dict,module.run_order)
			if (config_dict['build']['interactive'] and
					raw_input(util.red('\n\nDo you want to stop debug and/or interactive mode? (input y/n)\n' )) == 'y'):
				config_dict['build']['interactive'] = False
				config_dict['build']['debug'] = False
	if is_built(config_dict,shutit_map.get(k)):
		util.log('Starting module')
		if not module.start(config_dict):
			util.fail(module.module_id + ' failed on start',child=util.get_pexpect_child('container_child'))

# Test in reverse order
shutit_map_list.sort()
shutit_map_list.reverse()
util.log(util.red('PHASE: test'))
if config_dict['build']['tutorial']:
	util.pause_point(util.get_pexpect_child('container_child'),'\nNow doing test phase',print_input=False)
stop_all(shutit_map_list,config_dict,module.run_order)
start_all(shutit_map_list,config_dict,module.run_order)
for k in shutit_map_list:
	# Only test if it's thought to be installed.
	if is_built(config_dict,shutit_map.get(k)):
		util.log(util.red('RUNNING TEST ON: ' + shutit_map.get(k).module_id))
		if not shutit_map.get(k).test(config_dict):
			util.fail(shutit_map.get(k).module_id + ' failed on test',child=util.get_pexpect_child('container_child'))

# Stop all the modules
if config_dict['build']['tutorial']:
	util.pause_point(util.get_pexpect_child('container_child'),'\nStopping all modules before finalize phase',print_input=False)
stop_all(shutit_map_list,config_dict,-1)

# Finalize in reverse order
shutit_map_list.sort()
shutit_map_list.reverse()
util.log(util.red('PHASE: finalize'))
if config_dict['build']['tutorial']:
	util.pause_point(util.get_pexpect_child('container_child'),'\nNow doing finalize phase, which we do when all builds are complete and modules are stopped',print_input=False)
for k in shutit_map_list:
	# Only finalize if it's thought to be installed.
	if is_built(config_dict,shutit_map.get(k)):
		if not shutit_map.get(k).finalize(config_dict):
			util.fail(shutit_map.get(k).module_id + ' failed on finalize',child=util.get_pexpect_child('container_child'))

# Tag and push etc
util.do_repository_work(config_dict,config_dict['expect_prompts']['base_prompt'],config_dict['repository']['name'],docker_executable=config_dict['host']['docker_executable'],password=config_dict['host']['password'])
# Final exits
host_child = util.get_pexpect_child('host_child')
host_child.sendline('exit') # Exit raw bash
time.sleep(0.3)

# Finally, do repo work on the core module.
if config_dict[shutit_map.get(0).module_id]['do_repo_work']:
	if config_dict['build']['tutorial']:
		util.pause_point(util.get_pexpect_child('host_child'),'\nDoing final committing/tagging on the overall container and creating the artifact.',print_input=False)
	util.log(util.red('doing repo work: ' + shutit_map.get(0).module_id + ' with run order: ' + str(shutit_map.get(0.0).run_order)))
	util.do_repository_work(config_dict,
		config_dict['expect_prompts']['base_prompt'],
		str(shutit_map.get(0.0).run_order),
		password=config_dict['host']['password'],
		docker_executable=config_dict['host']['docker_executable'])

util.log(util.red(util.build_report('Module: N/A (END)')),prefix=False,force_stdout=True)

if config_dict['build']['tutorial']:
	util.log(util.red('\nThe build is complete. You should now have a container called ' + config_dict['container']['name'] + ' and a new image if you chose to commit it.\n\nLook and play with the following files from the newly-created module directory to dig deeper:\n\n\tconfigs/default.cnf\n\t*.py\n\nYou can rebuild at any time by running the supplied ./build.sh and run with the supplied ./run.sh.\n\nThere\'s a default test runner in bin/test.sh\n\nYou can inspect the details of the build in the container\'s /root/shutit_build directory.'),force_stdout=True)
