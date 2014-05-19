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
	def check_ready(self,shutit):
		return shutit.file_exists('/resources/README.md')

	# is_installed
	#
	# Determines whether the module has been built in this container
	# already.
	#
	# Should return True if it is certain it's there, else False.
	def is_installed(self,shutit):
		return shutit.file_exists('/tmp/container_touched.sh') and shutit.file_exists('/tmp/README.md')

	# build
	#
	# Run the build part of the module, which should ensure the module
	# has been set up.
	# If is_installed determines that the module is already there,
	# this is not run.
	#
	# Should return True if it has succeeded in building, else False.
	def build(self,shutit):
		shutit.set_default_expect(shutit.cfg['expect_prompts']['root_prompt'])
		shutit.install('firefox')
		shutit.install('xautomation')
		shutit.install('vim')
		shutit.install('scrot')
		shutit.send_file('/root/start_win2048.sh',file.read(file('resources/start_win2048.sh')))
		shutit.send_file('/root/tryagain.pat',file.read(file('resources/tryagain.pat')))
		shutit.send_file('/root/tryagain.png',file.read(file('resources/tryagain.png')))
		shutit.send_and_expect('chmod +x /root/start_win2048.sh')
		return True

	# remove
	# 
	# Remove the module, which should ensure the module has been deleted 
	# from the system.
	def remove(self,shutit):
		shutit.send_and_expect('rm -f /root/start_win2048.sh')
		return True

	# test
	#
	# Test the module is OK.
	# Should return True if all is OK, else False.
	# This is run regardless of whether the module is installed or not.
	def test(self,shutit):
		return shutit.package_installed('firefox')


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

