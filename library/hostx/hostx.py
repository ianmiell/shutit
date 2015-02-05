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
import os

class hostx(ShutItModule):

	def is_installed(self, shutit):
		return shutit.file_exists('/root/shutit_build/module_record/' + self.module_id + '/built')

	def build(self, shutit):
		shutit.send('groupadd -g ' + shutit.cfg[self.module_id]['gid'] + ' ' + shutit.cfg[self.module_id]['username'])
		shutit.send('useradd -d /home/' + shutit.cfg[self.module_id]['username'] + ' -s /bin/bash -m ' + shutit.cfg[self.module_id]['username'] + ' -u ' + shutit.cfg[self.module_id]['uid'] + ' -g ' + shutit.cfg[self.module_id]['gid'])
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id, 'username', str(os.getlogin()))
		shutit.get_config(self.module_id, 'uid', str(os.getuid()))
		shutit.get_config(self.module_id, 'gid', str(os.getgid()))
		return True


def module():
	return hostx(
		'shutit.tk.hostx.hostx', 0.3265,
		description='Share your host X server with the container',
		depends=['shutit.tk.setup']
	)

