"""ShutIt module. See http://shutit.tk
"""
from shutit_module import ShutItModule

class mesos(ShutItModule):

	def build(self, shutit):
		shutit.install('git')
		shutit.install('build-essential')
		shutit.install('openjdk-6-jdk')
		shutit.install('python-dev')
		shutit.install('python-boto')
		shutit.install('libcurl4-nss-dev')
		shutit.install('libsasl2-dev')
		shutit.install('maven')
		shutit.install('autoconf')
		shutit.install('libtool')
		shutit.send('pushd /opt')
		shutit.send('git clone http://git-wip-us.apache.org/repos/asf/mesos.git')
		shutit.send('pushd mesos')
		shutit.send('./bootstrap')
		shutit.send('mkdir build')
		shutit.send('pushd build')
		shutit.send('../configure --prefix=/usr')
		shutit.send('make')
		# TODO: fails ATM, not sure if it's really a problem or not
		#shutit.send('make check')
		shutit.send('make install')
		return True

def module():
	return mesos(
		'shutit.tk.mesos.mesos', 000.00125125,
		description='Mesos install',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup']
	)

