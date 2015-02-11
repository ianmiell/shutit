"""ShutIt module. See http://shutit.tk
"""
#Copyright (C) 2014 OpenBet Limited
#
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

class apt_mirror(ShutItModule):

	def build(self, shutit):
		#http://unixrob.blogspot.co.uk/2012/05/create-apt-mirror-with-ubuntu-1204-lts.html
		shutit.install('apt-mirror')
		shutit.install('apache2')
		shutit.send('/var/spool/apt-mirror/var/clean.sh')
		shutit.send('ln -s /var/spool/apt-mirror/mirror/gb.archive.ubuntu.com/ubuntu/ /var/www/ubuntu')
		shutit.send('ln -s /var/spool/apt-mirror/mirror/apt.puppetlabs.com /var/www/puppet')
		shutit.send('apt-mirror')
		return True

def module():
	return apt_mirror(
		'shutit.tk.apt_mirror.apt_mirror', 0.801,
		description='apt mirror builder',
		depends=['shutit.tk.setup']
	)

