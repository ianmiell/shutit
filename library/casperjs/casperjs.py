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

	def check_ready(self,shutit):
		config_dict = shutit.cfg
		return True

	def is_installed(self,shutit):
		config_dict = shutit.cfg
		container_child = util.get_pexpect_child('container_child')
		res = util.file_exists(container_child,'/opt/casperjs',config_dict['expect_prompts']['root_prompt'],directory=True)
		return res

	def build(self,shutit):
		config_dict = shutit.cfg
		container_child = util.get_pexpect_child('container_child')
		util.send_and_expect(container_child,'pushd /opt',config_dict['expect_prompts']['root_prompt'])
		util.install(container_child,config_dict,'git',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'git clone git://github.com/n1k0/casperjs.git',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'pushd casperjs',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'git checkout tags/1.0.2',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'popd',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'popd',config_dict['expect_prompts']['root_prompt'])
		return True

	def start(self,shutit):
		config_dict = shutit.cfg
		container_child = util.get_pexpect_child('container_child')
		return True

	def stop(self,shutit):
		config_dict = shutit.cfg
		container_child = util.get_pexpect_child('container_child')
		return True


	def cleanup(self,shutit):
		config_dict = shutit.cfg
		container_child = util.get_pexpect_child('container_child')
		util.send_and_expect(container_child,'pushd /opt',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'popd /opt',config_dict['expect_prompts']['root_prompt'])
		return True

	def remove(self,shutit):
		config_dict = shutit.cfg
		container_child = util.get_pexpect_child('container_child')
		util.send_and_expect(container_child,'rm -rf /opt/casperjs',config_dict['expect_prompts']['root_prompt'])
		return True

	def test(self,shutit):
		config_dict = shutit.cfg
		container_child = util.get_pexpect_child('container_child')
		return True

	def finalize(self,shutit):
		config_dict = shutit.cfg
		return True

	def get_config(self,shutit):
		config_dict = shutit.cfg
		cp = config_dict['config_parser']
		return True

if not util.module_exists('shutit.tk.casperjs.casperjs'):
	obj = casperjs('shutit.tk.casperjs.casperjs',0.314,'casperjs ShutIt module. See http://casperjs.org/')
	util.get_shutit_modules().add(obj)
	ShutItModule.register(casperjs)

