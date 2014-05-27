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

class win2048(ShutItModule):

	def is_installed(self,shutit):
		return self.test(shutit)

	def build(self,shutit):
		shutit.install('firefox')
		shutit.install('xdotool')
		shutit.install('xautomation')
		shutit.install('vim')
		shutit.install('scrot')
		shutit.send_file('/root/start_win2048.sh',file.read(file(os.path.abspath(os.path.dirname(__file__)) + '/files/start_win2048.sh')))
		#shutit.send_file('/root/tryagain.png',file.read(file(os.path.abspath(os.path.dirname(__file__)) + '/files/tryagain.png')))
		shutit.send_and_expect('pushd /root')
		shutit.send_and_expect('wget https://raw.githubusercontent.com/ianmiell/shutit/master/library/win2048/files/tryagain.png')
		shutit.send_and_expect('patextract /root/tryagain.png 0 0 69 20 > /root/tryagain.pat')
		shutit.send_and_expect('chmod +x /root/start_win2048.sh')
		shutit.send_and_expect('popd')
		return True

	def remove(self,shutit):
		shutit.send_and_expect('rm -f /root/start_win2048.sh')
		return True

	def test(self,shutit):
		return shutit.package_installed('firefox') and shutit.package_installed('scrot')

def module():
	return win2048(
		'shutit.tk.win2048.win2048', 0.326,
		description='win at 2048',
		depends=['shutit.tk.setup', 'shutit.tk.vnc.vnc']
	)

