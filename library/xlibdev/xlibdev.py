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

class xlibdev(ShutItModule):

	def is_installed(self,shutit):
		return False

	def build(self,shutit):
		root_prompt_expect = shutit.cfg['expect_prompts']['root_prompt'] # Set the string we expect to see once commands are done.
		shutit.set_default_expect(shutit.cfg['expect_prompts']['root_prompt'])
		shutit.install('libx11-dev')
		return True


if not util.module_exists('shutit.tk.xlibdev.xlibdev'):
	obj = xlibdev('shutit.tk.xlibdev.xlibdev',0.3225)
	obj.add_dependency('shutit.tk.setup')
	obj.add_dependency('shutit.tk.vnc.vnc')
	util.get_shutit_modules().add(obj)
	ShutItModule.register(xlibdev)

