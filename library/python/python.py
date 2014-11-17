"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class python(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.send('mkdir -p /opt/python')
		shutit.send('pushd /opt/python')
		shutit.send('wget https://www.python.org/ftp/python/2.7.8/Python-2.7.8.tgz')
		shutit.send('tar -zxf Python-2.7.8.tgz')
		shutit.send('pushd Python-2.7.8')
		shutit.send('./configure --prefix=/usr')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/python')
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
	return python(
		'shutit.tk.python.python', 0.012513613613,
		description='',
		maintainer='',
		depends=['shutit.tk.make.make']
	)

