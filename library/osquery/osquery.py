"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class osquery(ShutItModule):

	def build(self, shutit):
		shutit.install('software-properties-common')
		shutit.install('apt-transport-https')
		shutit.install('cmake')
		shutit.send('apt-key adv --keyserver keyserver.ubuntu.com --recv-keys C9D8B80B')
		shutit.send('add-apt-repository "deb https://osquery-packages.s3.amazonaws.com/trusty trusty main"')
		shutit.send('apt-get update')
		shutit.install('osquery')
		return True

def module():
	return osquery(
		'shutit.tk.osquery.osquery', 0.11352451,
		description='Facebook\'s OSQuery sql tool',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup']
	)

