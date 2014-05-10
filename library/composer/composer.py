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


class composer(ShutItModule):

	def is_installed(self,shutit):
		config_dict = shutit.cfg
		return False

	def build(self,shutit):
		config_dict = shutit.cfg
		container_child = util.get_pexpect_child('container_child')
		util.install(container_child,config_dict,'curl',config_dict['expect_prompts']['root_prompt'])
		util.install(container_child,config_dict,'php5',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'curl -sS https://getcomposer.org/installer | php',config_dict['expect_prompts']['root_prompt'],check_exit=False)
		return True

if not util.module_exists('shutit.tk.composer.composer'):
	obj = composer('shutit.tk.composer.composer',0.315,'Dependency manager for php: https://getcomposer.org/')
	obj.add_dependency('shutit.tk.setup')
	util.get_shutit_modules().add(obj)
	ShutItModule.register(composer)

