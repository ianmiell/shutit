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

class shutit(ShutItModule):

	# is_installed
	#
	# Determines whether the module has been built in this container
	# already.
	#
	# Should return True if it is certain it's there, else False.
	def is_installed(self,shutit):
		return shutit.file_exists('/shutit',directory=True)

	# build
	#
	# Run the build part of the module, which should ensure the module
	# has been set up.
	# If is_installed determines that the module is already there,
	# this is not run.
	#
	# Should return True if it has succeeded in building, else False.
	def build(self,shutit):
		root_prompt_expect = shutit.cfg['expect_prompts']['root_prompt'] # Set the string we expect to see once commands are done.
		shutit.set_default_expect(shutit.cfg['expect_prompts']['root_prompt'])
		shutit.install('git')
		shutit.send_and_expect('pushd /')
		shutit.send_and_expect('git clone https://github.com/ianmiell/shutit.git')
		shutit.send_and_expect('popd')
		return True

if not util.module_exists('shutit.tk.shutit.shutit'):
	obj = shutit('shutit.tk.shutit.shutit',0.397)
	obj.add_dependency('shutit.tk.setup')
	obj.add_dependency('shutit.tk.docker.docker')
	# We need to create a user to get shutit to work
	obj.add_dependency('shutit.tk.adduser.adduser')
	util.get_shutit_modules().add(obj)
	ShutItModule.register(shutit)

