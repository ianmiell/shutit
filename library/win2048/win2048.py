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

class win2048(ShutItModule):

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
	def check_ready(self,config_dict):
		container_child = util.get_pexpect_child('container_child')
		root_prompt_expect = config_dict['expect_prompts']['root_prompt']
		return util.file_exists(container_child,'/resources/README.md',root_prompt_expect)

	# is_installed
	#
	# Determines whether the module has been built in this container
	# already.
	#
	# Should return True if it is certain it's there, else False.
	def is_installed(self,config_dict):
		container_child = util.get_pexpect_child('container_child')
		root_prompt_expect = config_dict['expect_prompts']['root_prompt']
		return util.file_exists(container_child,'/tmp/container_touched.sh',root_prompt_expect) and util.file_exists(container_child,'/tmp/README.md',root_prompt_expect)

	# build
	#
	# Run the build part of the module, which should ensure the module
	# has been set up.
	# If is_installed determines that the module is already there,
	# this is not run.
	#
	# Should return True if it has succeeded in building, else False.
	def build(self,config_dict):
		container_child = util.get_pexpect_child('container_child') # Let's get the container child object from pexpect.
		root_prompt_expect = config_dict['expect_prompts']['root_prompt'] # Set the string we expect to see once commands are done.
		util.install(container_child,config_dict,'firefox',root_prompt_expect)
		util.install(container_child,config_dict,'xdotool',root_prompt_expect)
		util.install(container_child,config_dict,'vim',root_prompt_expect)
		start_win2048 = """cat > /root/start_win2048.sh << 'END'
# Start
/root/start_vnc.sh
export DISPLAY=:1
xdotool exec firefox
xdotool exec killall gnome-terminal
WID=$(xdotool search --sync --onlyvisible --class firefox)
xdotool sleep 1
xdotool windowraise $WID
xdotool key F6
xdotool type http://gabrielecirulli.github.io/2048/
xdotool key KP_Enter
END"""
		util.send_and_expect(container_child,start_win2048,root_prompt_expect)
		util.send_and_expect(container_child,'chmod +x /root/start_win2048.sh',root_prompt_expect)
		return True

	# start
	#
	# Run when module should be installed (is_installed() or configured to build is true)
	# Run after repo work.
	def start(self,config_dict):
		container_child = util.get_pexpect_child('container_child')
		util.send_and_expect(container_child,'/root/start_win2048.sh',config_dict['expect_prompts']['root_prompt'])
		return True
	# stop
	#
	# Run when module should be stopped.
	# Run before repo work, and before finalize is called.
	def stop(self,config_dict):
		return True

	# cleanup
	#
	# Cleanup the module, ie clear up stuff not needed for the rest of the build, eg tar files removed, apt-get cleans.
	# Should return True if all is OK, else False.
	# Note that this is only run if the build phase was actually run.
	def cleanup(self,config_dict):
		return True

	# finalize
	#
	# Finalize the module, ie do things that need doing before we exit.
	def finalize(self,config_dict):
		return True

	# remove
	# 
	# Remove the module, which should ensure the module has been deleted 
	# from the system.
	def remove(self,config_dict):
		container_child = util.get_pexpect_child('container_child')
		container_child = util.get_pexpect_child('container_child')
		util.send_and_expect(container_child,'rm -f /root/start_win2048.sh',config_dict['expect_prompts']['root_prompt'])
		return True

	# test
	#
	# Test the module is OK.
	# Should return True if all is OK, else False.
	# This is run regardless of whether the module is installed or not.
	def test(self,config_dict):
		container_child = util.get_pexpect_child('container_child')
		root_prompt_expect = config_dict['expect_prompts']['root_prompt']
		# Check the packages we need are installed.
		return util.package_installed(container_child,config_dict,'firefox',root_prompt_expect)

	# get_config
	#
	# each object can handle config here
	def get_config(self,config_dict):
		cp = config_dict['config_parser']
		return True


# win2048(string,float)
# string : Any string you believe to identify this module uniquely, 
#          eg com.my_corp.my_module_dir.my_module
# float:   Float value for ordering module builds, must be > 0.0
if not util.module_exists('shutit.tk.win2048.win2048'):
	obj = win2048('shutit.tk.win2048.win2048',0.326)
	obj.add_dependency('shutit.tk.setup')
	obj.add_dependency('shutit.tk.vnc.vnc')
	util.get_shutit_modules().add(obj)
	ShutItModule.register(win2048)

