"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class mesos(ShutItModule):


	def build(self, shutit):
		shutit.install('build-essential openjdk-6-jdk python-dev python-boto libcurl4-nss-dev libsasl2-dev maven libapr1-dev libsvn-dev wget')
		shutit.send('wget -qO- http://www.apache.org/dist/mesos/0.20.1/mesos-0.20.1.tar.gz | tar -zxf -')
		shutit.send('cd mesos*')
		shutit.send('mkdir build')
		shutit.send('cd build')
		shutit.send('../configure')
		shutit.send('make')
		shutit.send('make check')
		shutit.send('make install')
		return True

def module():
	return mesos(
		'shutit.tk.mesos.mesos', 0.41251365,
		description='',
		maintainer='',
		depends=['shutit.tk.setup']
	)

