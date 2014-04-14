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

class postgres(ShutItModule):

	def check_ready(self,config_dict):
		return True

	def is_installed(self,config_dict):
		return False

	def build(self,config_dict):
		container_child = util.get_pexpect_child('container_child')
		util.install(container_child,config_dict,'postgresql',config_dict['expect_prompts']['root_prompt'])
		res = util.add_line_to_file(container_child,'# postgres','/root/start_postgres.sh',config_dict['expect_prompts']['root_prompt'])
		if res:
			util.add_line_to_file(container_child,"echo 'Setting shmmax for postgres'",'/root/start_postgres.sh',config_dict['expect_prompts']['root_prompt'],force=True)
			util.add_line_to_file(container_child,'sysctl -w kernel.shmmax=268435456','/root/start_postgres.sh',config_dict['expect_prompts']['root_prompt'],force=True)
			util.add_line_to_file(container_child,'service postgresql start','/root/start_postgres.sh',config_dict['expect_prompts']['root_prompt'],force=True)
		util.send_and_expect(container_child,"""cat > /root/stop_postgres.sh <<< 'service postgresql stop'""",config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'chmod +x /root/start_postgres.sh',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'chmod +x /root/stop_postgres.sh',config_dict['expect_prompts']['root_prompt'])
		return True

	def start(self,config_dict):
		container_child = util.get_pexpect_child('container_child')
		util.send_and_expect(container_child,'/root/start_postgres.sh',config_dict['expect_prompts']['root_prompt'],check_exit=False)
		return True

	def stop(self,config_dict):
		container_child = util.get_pexpect_child('container_child')
		util.send_and_expect(container_child,'/root/stop_postgres.sh',config_dict['expect_prompts']['root_prompt'],check_exit=False)
		return True

	def cleanup(self,config_dict):
		return True

	def finalize(self,config_dict):
		return True

	def test(self,config_dict):
		return True

	def get_config(self,config_dict):
		return True

if not util.module_exists('shutit.tk.postgres.postgres'):
	obj = postgres('shutit.tk.postgres.postgres',0.320)
	obj.add_dependency('shutit.tk.setup')
	util.get_shutit_modules().add(obj)
	ShutItModule.register(postgres)

