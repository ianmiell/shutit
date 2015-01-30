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
		"""Only apt-based systems are supported support atm
		"""
		return shutit.cfg['target']['install_type'] == 'apt'

	def is_installed(self, shutit):
		return shutit.file_exists('/root/start_vnc.sh')

	def build(self, shutit):
		#shutit.install('gnome-core')
		#shutit.install('gnome-terminal')
		#shutit.install('openjdk-6-jre')
		#shutit.install('xserver-xorg')
		#shutit.install('vnc4server')
		#shutit.install('novnc')
		if shutit.cfg['target']['distro'] == 'ubuntu':
			shutit.install('ubuntu-desktop')
			shutit.send('rm -rf /tmp/ubuntu-desktop')
		send = 'vncserver'
		shutit.multisend(send, {'assword:':shutit.cfg['shutit.tk.vnc.vnc']['password'], 'erify':shutit.cfg['shutit.tk.vnc.vnc']['password']}, fail_on_empty_before=False, echo=False)
		shutit.add_line_to_file('#!/bin/bash','/root/start_vnc.sh')
		shutit.add_line_to_file('# start vnc', '/root/start_vnc.sh')
		shutit.add_line_to_file('rm -rf /tmp/.X*', '/root/start_vnc.sh')
		shutit.add_line_to_file("""vncserver << END
""" + shutit.cfg['shutit.tk.vnc.vnc']['password'] + """
""" + shutit.cfg['shutit.tk.vnc.vnc']['password'] + """
END""", '/root/start_vnc.sh')
		shutit.add_line_to_file('echo "Did you expose ports 5901 and 6080?"', '/root/start_vnc.sh', match_regexp='echo .Did you expose ports 5901 and 6080..')
		shutit.add_line_to_file('echo "If so, then vncviewer localhost:1 should work."', '/root/start_vnc.sh', match_regexp='echo .If so, then vncviewer localhost:1 should work..')
		shutit.send('pwd && ls context')
		shutit.send_host_file('/root/stop_vnc.sh','context/stop_vnc.sh')
		shutit.send('chmod +x /root/start_vnc.sh')
		shutit.send('chmod +x /root/stop_vnc.sh')

		# Ridiculous hack to make the "s" and various other keys work. cf: http://broderick-tech.com/vnc-broken-s-key/
		shutit.send('/root/start_vnc.sh', check_exit=False)
		shutit.send('export DISPLAY=:1', check_exit=False)
		shutit.send('''gsettings list-recursively org.gnome.desktop.wm.keybindings  | grep -v "@as" | awk '{print $2}' | xargs -IXXX gsettings set org.gnome.desktop.wm.keybindings XXX []''')
		shutit.send('/root/stop_vnc.sh', check_exit=False)
		return True

	def start(self, shutit):
		shutit.send('/root/start_vnc.sh', check_exit=False)
		return True

	def stop(self, shutit):
		shutit.send('/root/stop_vnc.sh', check_exit=False)
		return True

	def get_config(self, shutit):
		shutit.get_config('shutit.tk.vnc.vnc', 'password','vncpass')
		return True

def module():
	return vnc(
		'shutit.tk.vnc.vnc', 0.322,
		description='vnc server. contains instructions for use within /root/start_vnc.sh output.',
		depends=['shutit.tk.setup']
	)


