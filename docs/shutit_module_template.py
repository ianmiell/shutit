#Copyright (C) 2014 OpenBet Limited
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is furnished
#to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
#FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
#COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
#IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from shutit_module import ShutItModule
import util

class template(ShutItModule):


	# is_installed
	#
	# Determines whether the module has been built in this container
	# already.
	#
	# Should return True if it is certain it's there, else False.
	def is_installed(self,shutit):
		container_child = util.get_pexpect_child('container_child')
		root_prompt_expect = shutit.cfg['expect_prompts']['root_prompt']
		return util.file_exists(container_child,'/tmp/container_touched.sh',root_prompt_expect) and util.file_exists(container_child,'/tmp/README.md',root_prompt_expect)

	# build
	#
	# Run the build part of the module, which should ensure the module
	# has been set up.
	# If is_installed determines that the module is already there,
	# this is not run.
	#
	# Should return True if it has succeeded in building, else False.
	def build(self,shutit):
		container_child = util.get_pexpect_child('container_child') # Let's get the container child object from pexpect.
		root_prompt_expect = shutit.cfg['expect_prompts']['root_prompt'] # Set the string we expect to see once commands are done.
		# Line number 49 should be the next one (so bash scripts can be inserted properly)

		# DELETE THIS SECTION WHEN UNDERSTOOD - BEGIN
		util.send_and_expect(container_child,'touch /tmp/deleteme',root_prompt_expect)
		util.send_and_expect(container_child,'touch /tmp/container_touched.sh',root_prompt_expect)
		util.add_line_to_file(container_child,'#This line should only appear once in the file','/tmp/container_touched.sh',root_prompt_expect)
		util.add_line_to_file(container_child,'#This line should only appear once in the file','/tmp/container_touched.sh',root_prompt_expect)
		# We add the match_regexp because the string has a quote in it.
		util.add_line_to_file(container_child,'echo "hello container"','/tmp/container_touched.sh',root_prompt_expect,match_regexp='echo .hello container.')
		util.add_line_to_file(container_child,'sleep 10000000 &','/tmp/container_touched.sh',root_prompt_expect)
		util.send_and_expect(container_child,'chmod +x /tmp/container_touched.sh',root_prompt_expect)
		# Make sure passwd is installed
		util.install(container_child,shutit.cfg,'passwd',root_prompt_expect)
		# Install mlocate
		util.install(container_child,shutit.cfg,'mlocate',root_prompt_expect)
		# Example of distro-specific password update
		# record_command=False prevents the password being output at the end on debug. However, if it matches a password stored in config, 
		# it will automatically redact it.
		if shutit.cfg['container']['install_type'] == 'apt': # apt-based password update
			# "check_exit" checks the exit code of the command you are running.
			# We can't check the exit code as the command will not return when we see 'Retype new' on the terminal.
			util.send_and_expect(container_child,'passwd','Enter new',check_exit=False)
			util.send_and_expect(container_child,shutit.cfg['container']['password'],'Retype new',check_exit=False,record_command=False)
			util.send_and_expect(container_child,shutit.cfg['container']['password'],root_prompt_expect)
		elif shutit.cfg['container']['install_type'] == 'yum': # yum-based password update
			# Check_exit checks the exit code of the command you are running.
			# We can't check the exit code as the command will not return when we see 'ew password' on the terminal.
			util.send_and_expect(container_child,'passwd','ew password',check_exit=False)
			util.send_and_expect(container_child,shutit.cfg['container']['password'],'ew password',check_exit=False,record_command=False)
			util.send_and_expect(container_child,shutit.cfg['container']['password'],root_prompt_expect)
		# You can put multiple items you might expect in a list and handle accordingly:
		res = util.send_and_expect(container_child,'sudo ls',['assword',root_prompt_expect],check_exit=False)
		if res == 0:
			util.send_and_expect(container_child,shutit.cfg['container']['password'],root_prompt_expect)
		elif res == 1:
			pass
		else:
			# We fail out on this case, as it's not expected.
			util.fail('res: ' + str(res) + ' not handled')
		# example of resource use (simple file, copy the README.md into the container)
		util.send_and_expect(container_child,'cp /resources/README.md /tmp',root_prompt_expect)
		# example of bespoke config use
		if shutit.cfg[GLOBALLY_UNIQUE_STRING]['example_bool']:
			util.add_line_to_file(container_child,'# ' + shutit.cfg[GLOBALLY_UNIQUE_STRING]['example'],'/tmp/container_touched.sh',root_prompt_expect)
		# Example of login/logout handling
		# When logging in, use the base prompt to attempt to match all prompts
		# Note that we don't check_exit, because the exit value won't be meaningful.
		util.send_and_expect(container_child,'su',shutit.cfg['expect_prompts']['base_prompt'],check_exit=False)
		# Then call handle_login to set and get the bespoke prompt for the session
		util.handle_login(container_child,shutit.cfg,'test_tmp_prompt')
		util.send_and_expect(container_child,'echo "a command and some output"',shutit.cfg['expect_prompts']['test_tmp_prompt'])
		# We're about to exit, so handle the reversion of the prompt using the base_prompt again.
		util.handle_revert_prompt(container_child,shutit.cfg['expect_prompts']['base_prompt'],'test_tmp_prompt')
		util.send_and_expect(container_child,'exit',root_prompt_expect)


		# Example of temporary debugging
		orig_debug_val = shutit.cfg['build']['debug']
		shutit.cfg['build']['debug'] = True
		util.send_and_expect(container_child,'echo "Command to look at debug output"',root_prompt_expect)
		util.send_and_expect(container_child,'echo "Another command to look at debug output"',root_prompt_expect)
		shutit.cfg['build']['debug'] = orig_debug_val
		util.pause_point(container_child,"""
				The doubling up of text is expected; try and ignore it :)
				When you're done, "Ctrl" and "]" at the same time.
				You should then see your inputted lines in the output.
				Add them to the module file before the pause_point line as 
				"util.send_and_expect" lines (copy and paste), following
				the examples above this one in the file.
				Then "Ctrl" and "]" at the same time again to return to the script.
				Eventually you'll get a docker export to a tar file in your 
				configured resources folder.""")
		# DELETE THIS SECTION WHEN UNDERSTOOD - DONE
		return True

	# get_config
	#
	# each object can handle config here
	# OPTIONAL part of lifecycle - uncomment to include
	def get_config(self,shutit):
		cp = shutit.cfg['config_parser']
		# Bring the example config into the config dictionary.
		shutit.cfg[GLOBALLY_UNIQUE_STRING]['example']      = cp.get(GLOBALLY_UNIQUE_STRING,'example')
		shutit.cfg[GLOBALLY_UNIQUE_STRING]['example_bool'] = cp.getboolean(GLOBALLY_UNIQUE_STRING,'example_bool')
		return True

	# check_ready
	# 
	# Check whether we are ready to build this module.
	# 
	# This is called before the build, to ensure modules have 
	# their requirements in place (eg files required to be mounted 
	# in /resources). Checking whether the build will happen (and
	# therefore whether the check should take place) will be 
	# determined by the framework.
	# 
	# Should return True if it ready, else False.
	# OPTIONAL part of lifecycle - uncomment to include
	#def check_ready(self,shutit):
	#	container_child = util.get_pexpect_child('container_child')
	#	root_prompt_expect = shutit.cfg['expect_prompts']['root_prompt']
	#	return util.file_exists(container_child,'/resources/README.md',root_prompt_expect)

	# start
	#
	# Run when module should be installed (is_installed() or configured to build is true)
	# Run after repo work.
	# OPTIONAL part of lifecycle - uncomment to include
	#def start(self,shutit):
	#	container_child = util.get_pexpect_child('container_child')
	#	root_prompt_expect = shutit.cfg['expect_prompts']['root_prompt']
	#	# example of starting something
	#	util.send_and_expect(container_child,'cat /tmp/container_touched.sh',root_prompt_expect)
	#	util.send_and_expect(container_child,'sh /tmp/container_touched.sh',root_prompt_expect)
	#	return True

	# stop
	#
	# Run when module should be stopped.
	# Run before repo work, and before finalize is called.
	# OPTIONAL part of lifecycle - uncomment to include
	#def stop(self,shutit):
	#	container_child = util.get_pexpect_child('container_child')
	#	root_prompt_expect = shutit.cfg['expect_prompts']['root_prompt']
	#	# example of stopping something
	#	util.send_and_expect(container_child,"""ps -ef | grep -v grep | grep container_touched.sh | awk '{print $1}' | sed 's/\([0-9][0-9]*\)/kill \\1/' | sh""",root_prompt_expect)
	#	return True

	# cleanup
	#
	# Cleanup the module, ie clear up stuff not needed for the rest of the build, eg tar files removed, apt-get cleans.
	# Should return True if all is OK, else False.
	# Note that this is only run if the build phase was actually run.
	# OPTIONAL part of lifecycle - uncomment to include
	#def cleanup(self,shutit):
	#	container_child = util.get_pexpect_child('container_child')
	#	root_prompt_expect = shutit.cfg['expect_prompts']['root_prompt']
	#	util.send_and_expect(container_child,'rm -f /tmp/deleteme',root_prompt_expect)
	#	return True

	# finalize
	#
	# Finalize the module, ie do things that need doing before we exit.
	# OPTIONAL part of lifecycle - uncomment to include
	#def finalize(self,shutit):
	#	container_child = util.get_pexpect_child('container_child')
	#	root_prompt_expect = shutit.cfg['expect_prompts']['root_prompt']
	#	# Right at the end we want to ensure the locate db is up to date.
	#	util.send_and_expect(container_child,'updatedb',root_prompt_expect)
	#	return True

	# remove
	# 
	# Remove the module, which should ensure the module has been deleted 
	# from the system.
	# OPTIONAL part of lifecycle - uncomment to include
	#def remove(self,shutit):
	#	container_child = util.get_pexpect_child('container_child')
	#	root_prompt_expect = shutit.cfg['expect_prompts']['root_prompt']
	#	util.send_and_expect(container_child,'rm -f /tmp/container_touched.sh',root_prompt_expect)
	#	util.send_and_expect(container_child,'rm -f /tmp/README.md',root_prompt_expect)
	#	# TODO: remove the installed apps DEPENDS on install tracking being available.
	#	return True

	# test
	#
	# Test the module is OK.
	# Should return True if all is OK, else False.
	# This is run regardless of whether the module is installed or not.
	# OPTIONAL part of lifecycle - uncomment to include
	#def test(self,shutit):
	#	container_child = util.get_pexpect_child('container_child')
	#	root_prompt_expect = shutit.cfg['expect_prompts']['root_prompt']
	#	# Check the packages we need are installed.
	#	return util.package_installed(container_child,shutit.cfg,'mlocate',root_prompt_expect) and util.package_installed(container_child,shutit.cfg,'passwd',root_prompt_expect)



# template(string,float)
# string : Any string you believe to identify this module uniquely, 
#          eg com.my_corp.my_module_dir.my_module
# float:   Float value for ordering module builds, must be > 0.0
if not util.module_exists(GLOBALLY_UNIQUE_STRING):
	obj = template(GLOBALLY_UNIQUE_STRING,FLOAT)
	obj.add_dependency('shutit.tk.setup')
	util.get_shutit_modules().add(obj)
	ShutItModule.register(template)

