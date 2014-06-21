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

class adduser(ShutItModule):

	def is_installed(self,shutit):
		return False

	def build(self,shutit):
		# Does something odd with the terminal which makes pexpect think the commands failed
		shutit.send_and_expect('useradd -d /home/' + shutit.cfg['shutit.tk.adduser.adduser']['user'] + ' -s /bin/bash -m ' + shutit.cfg['shutit.tk.adduser.adduser']['user'],check_exit=False)
		shutit.install('passwd')
		shutit.install('sudo')
		shutit.install('adduser')
		shutit.send_and_expect('passwd ' + shutit.cfg['shutit.tk.adduser.adduser']['user'],'Enter new',check_exit=False)
		shutit.send_and_expect(shutit.cfg['shutit.tk.adduser.adduser']['password'],'Retype new',check_exit=False)
		shutit.send_and_expect(shutit.cfg['shutit.tk.adduser.adduser']['password'],check_exit=False)
		shutit.send_and_expect('adduser ' + shutit.cfg['shutit.tk.adduser.adduser']['user'] + ' sudo')
		return True

	def get_config(self,shutit):
		cp = shutit.cfg['config_parser']
		# Bring the example config into the config dictionary.
		shutit.get_config('shutit.tk.adduser.adduser','user','auser')
		shutit.get_config('shutit.tk.adduser.adduser','password','apassword')
		return True

def module():
	return adduser(
		'shutit.tk.adduser.adduser', 0.380,
		description='add a user',
		depends=['shutit.tk.setup']
	)

