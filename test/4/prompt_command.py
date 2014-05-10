#Copyright (C) 2014 OpenBet Limited
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from shutit_module import ShutItModule
import util

class prompt_command(ShutItModule):

	def check_ready(self,shutit):
		config_dict = shutit.cfg
		return True

	def is_installed(self,shutit):
		config_dict = shutit.cfg
		return False

	def build(self,shutit):
		config_dict = shutit.cfg
		container_child = util.get_pexpect_child('container_child') # Let's get the container child object from pexpect.
		root_prompt_expect = config_dict['expect_prompts']['root_prompt'] # Set the string we expect to see once commands are done.
		# Breaks unless we set the PROMPT_COMMAND manually on a login
		util.send_and_expect(container_child,"""cat >> /root/.bashrc << END
PROMPT_COMMAND='echo -ne "a"'
END""",root_prompt_expect)
		util.send_and_expect(container_child,'su',config_dict['expect_prompts']['base_prompt'],check_exit=False)
		util.handle_login(container_child,config_dict,'test_tmp_prompt')
		util.handle_revert_prompt(container_child,config_dict['expect_prompts']['base_prompt'],'test_tmp_prompt')
		util.send_and_expect(container_child,'exit',root_prompt_expect)
		return True

	def start(self,shutit):
		config_dict = shutit.cfg
		return True

	def stop(self,shutit):
		config_dict = shutit.cfg
		return True

	def cleanup(self,shutit):
		config_dict = shutit.cfg
		return True

	def finalize(self,shutit):
		config_dict = shutit.cfg
		return True

	def remove(self,shutit):
		config_dict = shutit.cfg
		return True

	def test(self,shutit):
		config_dict = shutit.cfg
		return True

	def get_config(self,shutit):
		config_dict = shutit.cfg
		return True

if not util.module_exists('shutit.tk.prompt_command'):
	obj = prompt_command('shutit.tk.prompt_command',1000.00)
	obj.add_dependency('shutit.tk.setup')
	util.get_shutit_modules().add(obj)
	ShutItModule.register(prompt_command)

