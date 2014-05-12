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

class jenkins(ShutItModule):

	def is_installed(self,shutit):
		return False

	def build(self,shutit):
		shutit.set_default_expect(shutit.cfg['expect_prompts']['root_prompt'])
		shutit.install('jenkins')
		# TODO start script
		return True

	def start(self,shutit):
		# TODO start jenkins
		#shutit.send_and_expect('/root/start_jenkins.sh')
		return True

	def stop(self,shutit):
		# TODO stop jenkins
		#shutit.send_and_expect('/root/stop_jenkins.sh')
		return True

if not util.module_exists('shutit.tk.jenkins'):
	obj = jenkins('shutit.tk.jenkins.jenkins',0.323,'ShutIt Jenkins module')
	obj.add_dependency('shutit.tk.setup')
	obj.add_dependency('shutit.tk.vnc.vnc')
	util.get_shutit_modules().add(obj)
	ShutItModule.register(jenkins)

