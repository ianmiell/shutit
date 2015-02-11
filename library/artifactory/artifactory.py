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

class artifactory(ShutItModule):

	def build(self,shutit):
		shutit.install('wget')
		shutit.install('zip')
		shutit.install('openjdk-7-jdk')
		shutit.install('net-tools') # required for installservice.sh script
		shutit.send('mkdir -p /opt/artifactory')
		shutit.send('wget -O /opt/artifactory/artifactory.zip http://bit.ly/Hqv9aj')
		shutit.send('pushd /opt/artifactory')
		shutit.send('unzip artifactory.zip')
		shutit.send('rm -f artifactory.zip')
		shutit.send('popd')
		shutit.send('/opt/artifactory/artifactory*/bin/installService.sh')
		return True

	#def get_config(self,shutit):
	#    return True

	#def check_ready(self,shutit):
	#    return True
	
	def start(self,shutit):
		shutit.send('service artifactory start')
		return True

	def stop(self,shutit):
		shutit.send('service artifactory stop')
		return True

	#def finalize(self,shutit):
	#    return True

	def remove(self,shutit):
		shutit.send('rm -rf /opt/artifactory')
		shutit.send('rm -rf /etc/opt/jfrog/artifactory')
		shutit.send('rm -rf /etc/init.d/artifactory')
		return True

	#def test(self,shutit):
	#    return True

def module():
	return artifactory(
		'shutit.tk.artifactory.artifactory', 0.76152,
		description='reference artifactory installation',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup']
	)

