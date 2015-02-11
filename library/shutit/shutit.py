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

class shutit(ShutItModule):

	def build(self, shutit):
		shutit.install('git')
		shutit.install('python-pip')
		shutit.send('cd /opt')
		shutit.send('git clone https://github.com/ianmiell/shutit.git')
		shutit.send('cd shutit')
		shutit.send('pip install -r requirements.txt')
		shutit.send('find . | grep cnf | xargs chmod 0600')
		shutit.add_to_bashrc('export PATH=$PATH:/opt/shutit')
		return True

def module():
	# Shutit needs a user to work
	return shutit(
		'shutit.tk.shutit.shutit', 0.397,
		description='shutit in a container',
		depends=['shutit.tk.setup', 'shutit.tk.docker.docker']
	)

