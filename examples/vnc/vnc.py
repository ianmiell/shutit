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
import pexpect


#From: https://groups.google.com/forum/#!topic/docker-user/D0n-lURDn0o
# Expose port 5901 and 6080
class vnc(ShutItModule):

	def check_ready(self,config_dict):
		return True

	def is_installed(self,config_dict):
		return False

	def build(self,config_dict):
		# TODO: distr-independence
		container_child = util.get_pexpect_child('container_child')
		util.send_and_expect(container_child,'echo "deb http://archive.ubuntu.com/ubuntu precise main universe multiverse" > /etc/apt/sources.list',config_dict['expect_prompts']['root_prompt'])
		util.add_line_to_file(container_child,'deb http://archive.ubuntu.com/ubuntu/ precise-updates main restricted','/etc/apt/sources.list',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'apt-get update -qq',config_dict['expect_prompts']['root_prompt'],timeout=10000)
		util.install(container_child,config_dict,'gnome-terminal',config_dict['expect_prompts']['root_prompt'])
		util.install(container_child,config_dict,'openjdk-6-jre',config_dict['expect_prompts']['root_prompt'])
		util.install(container_child,config_dict,'xserver-xorg',config_dict['expect_prompts']['root_prompt'])
		util.install(container_child,config_dict,'vnc4server',config_dict['expect_prompts']['root_prompt'],timeout=10000)
		util.install(container_child,config_dict,'novnc',config_dict['expect_prompts']['root_prompt'],timeout=10000)
		send = 'apt-get install -qq -y --no-install-recommends ubuntu-desktop > /tmp/ubuntu-desktop && rm -f /tmp/ubuntu-desktop'
		while True:
			res = util.send_and_expect(container_child,send,['Unpacking','Setting up',config_dict['expect_prompts']['root_prompt']],timeout=9999,check_exit=False)
			if res == 2:
				break
			elif res == 0 or res == 1:
				send = ''
		send = 'vncserver'
		while True:
			res = util.send_and_expect(container_child,send,['assword','erify',config_dict['expect_prompts']['root_prompt']],check_exit=False,fail_on_empty_before=False,record_command=False)
			if res == 0 or res == 1:
				send = config_dict['com.ian.miell.vnc.vnc']['password']
			elif res == 2:
				break
		util.add_line_to_file(container_child,'# start vnc','/root/start_vnc.sh',config_dict['expect_prompts']['root_prompt'])
		util.add_line_to_file(container_child,'rm -rf /tmp/.X*','/root/start_vnc.sh',config_dict['expect_prompts']['root_prompt'])
		util.add_line_to_file(container_child,"""vncserver << END
""" + config_dict['com.ian.miell.vnc.vnc']['password'] + """
""" + config_dict['com.ian.miell.vnc.vnc']['password'] + """
END""",'/root/start_vnc.sh',config_dict['expect_prompts']['root_prompt'])
		util.add_line_to_file(container_child,'echo "Did you expose ports 5901 and 6080?"','/root/start_vnc.sh',config_dict['expect_prompts']['root_prompt'])
		util.add_line_to_file(container_child,'echo "If so, then vnclient localhost:1 should work."','/root/start_vnc.sh',config_dict['expect_prompts']['root_prompt'])
		util.add_line_to_file(container_child,'# stop vnc','/root/stop_vnc.sh',config_dict['expect_prompts']['root_prompt'])
		util.add_line_to_file(container_child,"""ps -ef | grep vncserver | grep -v grep | awk '{print $2}' | xargs kill""",'/root/stop_vnc.sh',config_dict['expect_prompts']['root_prompt'])
		util.add_line_to_file(container_child,'sleep 10','/root/stop_vnc.sh',config_dict['expect_prompts']['root_prompt'])
		util.add_line_to_file(container_child,'rm -rf /tmp/.X*-lock','/root/stop_vnc.sh',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'chmod +x /root/start_vnc.sh',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'chmod +x /root/stop_vnc.sh',config_dict['expect_prompts']['root_prompt'])
		return True

	def start(self,config_dict):
		container_child = util.get_pexpect_child('container_child')
		util.send_and_expect(container_child,'/root/start_vnc.sh',config_dict['expect_prompts']['root_prompt'],check_exit=False)
		return True

	def stop(self,config_dict):
		container_child = util.get_pexpect_child('container_child')
		util.send_and_expect(container_child,'/root/stop_vnc.sh',config_dict['expect_prompts']['root_prompt'],check_exit=False)
		return True

	def cleanup(self,config_dict):
		return True

	def finalize(self,config_dict):
		return True

	def test(self,config_dict):
		return True

	def get_config(self,config_dict):
		cp = config_dict['config_parser']
		config_dict['com.ian.miell.vnc.vnc']['password'] = cp.get('com.ian.miell.vnc.vnc','password')
		return True

if not util.module_exists('com.ian.miell.vnc.vnc'):
	obj = vnc('com.ian.miell.vnc.vnc',0.322)
	util.get_shutit_modules().add(obj)
	ShutItModule.register(vnc)

