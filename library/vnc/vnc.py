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
import base64

#From: https://groups.google.com/forum/#!topic/docker-user/D0n-lURDn0o
# Expose port 5901 and 6080
class vnc(ShutItModule):

	def check_ready(self, shutit):
		# Only apt-based systems are supported support atm
		return shutit.cfg['container']['install_type'] == 'apt'

	def is_installed(self, shutit):
		return shutit.file_exists('/root/start_vnc.sh')

	def build(self, shutit):
		# TODO: distr-independence
		shutit.send('mkdir -p /root/.config/dconf')
		shutit.send_file('/root/.config/dconf/user', base64.standard_b64decode("""
R1ZhcmlhbnQAAAAAAAAAABgAAABwAQAAAAAAKAwAAAAAAAAAAAAAAAAAAAABAAAAAQAAAAIAAAAD
AAAABQAAAAcAAAAKAAAADAAAAAwAAADepzLWAgAAAHABAAAGAHYAeAEAAH4BAADYlUmXBQAAAH4B
AAAGAEwAhAEAAIgBAAAF9HCFAQAAAIgBAAANAEwAmAEAAKABAACSB0ZKCAAAAKABAAAMAEwArAEA
ALABAAB61W5fAwAAALABAAAMAHYAwAEAAMMBAAAnh3h8BwAAAMMBAAADAEwAyAEAAMwBAABLUJAL
BwAAAMwBAAAEAEwA0AEAANQBAADUtQIA/////9QBAAABAEwA2AEAAOABAACMAtigCgAAAOABAAAD
AEwA5AEAAOgBAACwtyQwBgAAAOgBAAAGAEwA8AEAAPQBAAC5iP3aCQAAAPQBAAAIAEwA/AEAAAAC
AACl73eqAgAAAAACAAAFAHYACAIAAA4CAABoZWlnaHQAAFgCAAAAaWRlc3J0LwIAAABkY29uZi1l
ZGl0b3IvAAAAAAAAAAsAAABrZXliaW5kaW5ncy8EAAAAc2hvdy1kZXNrdG9wAAAAAABhc2NhLwAA
AQAAAG9yZy8JAAAALwAAAAUAAAAGAAAAd20vAAMAAABnbm9tZS8AAAoAAABkZXNrdG9wLwgAAAB3
aWR0aAAAACADAAAAaQ=="""))
		shutit.install('gnome-core')
		shutit.install('gnome-terminal')
		shutit.install('openjdk-6-jre')
		shutit.install('xserver-xorg')
		shutit.install('vnc4server')
		shutit.install('novnc')
		shutit.install('apt-utils')
		# apt-utils?
		if shutit.cfg['container']['install_type'] == 'apt':
			send = 'apt-get install -qq -y --no-install-recommends ubuntu-desktop > /tmp/ubuntu-desktop && rm -f /tmp/ubuntu-desktop'
		while True:
			res = shutit.send(send, expect=['Unpacking','Setting up', shutit.cfg['expect_prompts']['root_prompt']], timeout=9999)
			if res == 2:
				break
			elif res == 0 or res == 1:
				send = ''
		send = 'vncserver'
		while True:
			res = shutit.send(send, expect=['assword:','erify', shutit.cfg['expect_prompts']['root_prompt']], fail_on_empty_before=False, echo=False)
			if res == 0 or res == 1:
				send = shutit.cfg['shutit.tk.vnc.vnc']['password']
			elif res == 2:
				break
		shutit.add_line_to_file('# start vnc','/root/start_vnc.sh')
		shutit.add_line_to_file('rm -rf /tmp/.X*','/root/start_vnc.sh')
		shutit.add_line_to_file("""vncserver << END
""" + shutit.cfg['shutit.tk.vnc.vnc']['password'] + """
""" + shutit.cfg['shutit.tk.vnc.vnc']['password'] + """
END""",'/root/start_vnc.sh')
		shutit.add_line_to_file('echo "Did you expose ports 5901 and 6080?"','/root/start_vnc.sh', match_regexp='echo .Did you expose ports 5901 and 6080..')
		shutit.add_line_to_file('echo "If so, then vncviewer localhost:1 should work."','/root/start_vnc.sh', match_regexp='echo .If so, then vncviewer localhost:1 should work..')
		shutit.add_line_to_file('# stop vnc','/root/stop_vnc.sh')
		shutit.add_line_to_file("""ps -ef | grep Xvnc4 | grep -v grep | awk '{print $2}' | xargs kill""",'/root/stop_vnc.sh')
		shutit.add_line_to_file('sleep 10','/root/stop_vnc.sh')
		shutit.add_line_to_file('rm -rf /tmp/.X*-lock','/root/stop_vnc.sh')
		shutit.send('chmod +x /root/start_vnc.sh')
		shutit.send('chmod +x /root/stop_vnc.sh')
		return True

	def start(self, shutit):
		shutit.send('/root/start_vnc.sh', check_exit=False)
		return True

	def stop(self, shutit):
		shutit.send('/root/stop_vnc.sh', check_exit=False)
		return True

	def get_config(self, shutit):
		shutit.get_config('shutit.tk.vnc.vnc','password','vncpass')
		return True

def module():
	return vnc(
		'shutit.tk.vnc.vnc', 0.322,
		description='vnc server. contains instructions for use within /root/start_vnc.sh output.',
		depends=['shutit.tk.setup']
	)


#/root/.config/dconf/user
