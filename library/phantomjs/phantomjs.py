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

class phantomjs(ShutItModule):

	def is_installed(self,shutit):
		config_dict = shutit.cfg
		container_child = util.get_pexpect_child('container_child')
		res = util.file_exists(container_child,'/opt/phantomjs',config_dict['expect_prompts']['root_prompt'],directory=True)
		return res

	def build(self,shutit):
		config_dict = shutit.cfg
		container_child = util.get_pexpect_child('container_child')
		util.send_and_expect(container_child,'pushd /opt',config_dict['expect_prompts']['root_prompt'])
		# TODO: latest version?
		util.install(container_child,config_dict,'curl',config_dict['expect_prompts']['root_prompt'])
		util.install(container_child,config_dict,'bzip2',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'curl --insecure https://phantomjs.googlecode.com/files/phantomjs-1.9.0-linux-x86_64.tar.bz2 > phantomjs-1.9.0-linux-x86_64.tar.bz2',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'bunzip2 phantomjs-1.9.0-linux-x86_64.tar.bz2',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'tar -xvf phantomjs-1.9.0-linux-x86_64.tar',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'ln -s phantomjs-1.9.0-linux-x86_64 phantomjs',config_dict['expect_prompts']['root_prompt'],check_exit=False)
		util.send_and_expect(container_child,'popd',config_dict['expect_prompts']['root_prompt'])
		return True

	def cleanup(self,shutit):
		config_dict = shutit.cfg
		container_child = util.get_pexpect_child('container_child')
		util.send_and_expect(container_child,'pushd /opt',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'rm phantomjs-*.tar',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'popd /opt',config_dict['expect_prompts']['root_prompt'])
		return True

	def remove(self,shutit):
		config_dict = shutit.cfg
		container_child = util.get_pexpect_child('container_child')
		util.send_and_expect(container_child,'rm -rf /opt/phantomjs',config_dict['expect_prompts']['root_prompt'])
		return True

if not util.module_exists('shutit.tk.phantomjs.phantomjs'):
	obj = phantomjs('shutit.tk.phantomjs.phantomjs',0.319,'ShutIt phantomjs module. See http://phantomjs.org/')
	util.get_shutit_modules().add(obj)
	ShutItModule.register(phantomjs)

