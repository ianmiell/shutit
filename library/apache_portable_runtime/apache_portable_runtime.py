"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class apache_portable_runtime(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.send('mkdir -p /opt/apr')
		shutit.send('pushd /opt/apr')
		shutit.send('wget http://apache.mirrors.timporter.net//apr/apr-1.5.1.tar.gz')
		shutit.send('tar -zxf apr-1.5.1.tar.gz')
		shutit.send('pushd apr-1.5.1')
		shutit.send('./configure --prefix=/usr')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/apr')
		return True

	#def get_config(self, shutit):
	#	return True

	#def check_ready(self, shutit):
	#	return True
	
	#def start(self, shutit):
	#	return True

	#def stop(self, shutit):
	#	return True

	#def finalize(self, shutit):
	#	return True

	#def remove(self, shutit):
	#	return True

	#def test(self, shutit):
	#	return True

def module():
	return apache_portable_runtime(
		'shutit.tk.apache_portable_runtime.apache_portable_runtime', 0.01213613624,
		description='',
		maintainer='',
		depends=['shutit.tk.make.make']
	)

