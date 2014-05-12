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
import pexpect
import util

#cf http://www.spinellis.gr/blog/20130619/

class git_server(ShutItModule):

	def is_installed(self,shutit):
		return False

	def build(self,shutit):
		shutit.set_default_expect(shutit.cfg['expect_prompts']['root_prompt'])
 		shutit.install('apache2')
 		shutit.install('git-core')
 		shutit.install('vim')
 		shutit.install('telnet')
		shutit.send_and_expect('git daemon --base-path=/var/cache/git --detach --syslog --export-all')
		# TODO: turn into start/stop script
		shutit.add_to_bashrc('git daemon --base-path=/var/cache/git --detach --syslog --export-all')
		return True

	def start(self,shutit):
		cfg = shutit.cfg
		# TODO
		return True

	def stop(self,shutit):
		cfg = shutit.cfg
		# TODO
		return True

if not util.module_exists('shutit.tk.git_server.git_server'):
	obj = git_server('shutit.tk.git_server.git_server',0.316,'ShutIt module that sets up a minimal git server.')
	util.get_shutit_modules().add(obj)
	ShutItModule.register(git_server)

