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

class adduser(ShutItModule):

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
	def check_ready(self,shutit):
		return True

	# is_installed
	#
	# Determines whether the module has been built in this container
	# already.
	#
	# Should return True if it is certain it's there, else False.
	def is_installed(self,shutit):
		return True

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
		cfg = shutit.cfg
		shutit.send_and_expect('useradd -d /home/' + cfg['shutit.tk.adduser.adduser']['user'] + ' -s /bin/bash -m ' + cfg['shutit.tk.adduser.adduser']['user'])
		shutit.send_and_expect('passwd ' + cfg['shutit.tk.adduser.adduser']['user'],'Enter new',check_exit=False)
		shutit.send_and_expect(cfg['shutit.tk.adduser.adduser']['password'],'Retype new',check_exit=False)
		shutit.send_and_expect(cfg['shutit.tk.adduser.adduser']['password'])
		if cfg['']
		shutit.send_and_expect('adduser ' + cfg['host']['real_user'] + ' sudo')
		return True

	# start
	#
	# Run when module should be installed (is_installed() or configured to build is true)
	# Run after repo work.
	def start(self,shutit):
		return True

	# stop
	#
	# Run when module should be stopped.
	# Run before repo work, and before finalize is called.
	def stop(self,shutit):
		return True

	# cleanup
	#
	# Cleanup the module, ie clear up stuff not needed for the rest of the build, eg tar files removed, apt-get cleans.
	# Should return True if all is OK, else False.
	# Note that this is only run if the build phase was actually run.
	def cleanup(self,shutit):
		return True

	# finalize
	#
	# Finalize the module, ie do things that need doing before we exit.
	def finalize(self,shutit):
		return True

	# remove
	# 
	# Remove the module, which should ensure the module has been deleted 
	# from the system.
	def remove(self,shutit):
		return True

	# test
	#
	# Test the module is OK.
	# Should return True if all is OK, else False.
	# This is run regardless of whether the module is installed or not.
	def test(self,shutit):
		return True

	# get_config
	#
	# each object can handle config here
	def get_config(self,shutit):
		cp = shutit.cfg['config_parser']
		# Bring the example config into the config dictionary.
		shutit.cfg['shutit.tk.adduser.adduser']['user']      = cp.get('shutit.tk.adduser.adduser','user')
		shutit.cfg['shutit.tk.adduser.adduser']['password'] = cp.get('shutit.tk.adduser.adduser','password')
		return True


# adduser(string,float)
# string : Any string you believe to identify this module uniquely, 
#          eg com.my_corp.my_module_dir.my_module
# float:   Float value for ordering module builds, must be > 0.0
if not util.module_exists('shutit.tk.adduser.adduser'):
	obj = adduser('shutit.tk.adduser.adduser',0.380)
	obj.add_dependency('shutit.tk.setup')
	util.get_shutit_modules().add(obj)
	ShutItModule.register(adduser)

