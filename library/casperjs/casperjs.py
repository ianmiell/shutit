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

class casperjs(ShutItModule):

	def is_installed(self,shutit):
		return shutit.file_exists('/opt/casperjs',shutit.cfg['expect_prompts']['root_prompt'],directory=True)

	def build(self,shutit):
		shutit.set_default_expect(shutit.cfg['expect_prompts']['root_prompt'])
		shutit.install('git')
		shutit.run_script("""
			pushd /opt
			git clone git://github.com/n1k0/casperjs.git
			pushd casperjs
			git checkout tags/1.0.2
			popd
			popd
		""")
		return True

	def remove(self,shutit):
		shutit.send_and_expect('rm -rf /opt/casperjs',shutit.cfg['expect_prompts']['root_prompt'])
		return True

if not util.module_exists('shutit.tk.casperjs.casperjs'):
	obj = casperjs('shutit.tk.casperjs.casperjs',0.314,'casperjs ShutIt module. See http://casperjs.org/')
	util.get_shutit_modules().add(obj)
	ShutItModule.register(casperjs)

