"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class thrift(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('git')
		shutit.install('automake')
		shutit.install('autoconf')
		shutit.install('libtool')
		shutit.install('libqt4-dev')
		shutit.install('pkg-config')
		shutit.install('flex')
		shutit.install('libevent-dev')
		shutit.install('bison')
		shutit.install('make')
		shutit.install('libboost1.55-all-dev')
		shutit.install('libssl-dev')
		shutit.send('pushd /opt')
		shutit.send('git clone https://github.com/apache/thrift.git')
		shutit.send('pushd /opt/thrift')
		shutit.send('./bootstrap.sh')
		shutit.send('./configure')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		return True

	#def get_config(self, shutit):
	#	return True

	#def check_ready(self, shutit):
	#	return True
	
	#def start(self, shutit):
	#	return True

	#def stop(self, shutit):
	#    return True
	#def finalize(self, shutit):
	#	return True

	#def remove(self, shutit):
	#	return True

	#def test(self, shutit):
	#	return True

def module():
	return thrift(
		'shutit.tk.thrift.thrift', 0.1124125,
		description='',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup']
	)

