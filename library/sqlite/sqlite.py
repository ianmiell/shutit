"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class sqlite(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.send('mkdir -p /opt/sqlite')
		shutit.send('pushd /opt/sqlite')
		shutit.send('wget http://www.sqlite.org/2014/sqlite-autoconf-3080701.tar.gz')
		shutit.send('tar -zxf sqlite-autoconf-3080701.tar.gz')
		shutit.send('pushd sqlite-autoconf-3080701')
		shutit.send('./configure --prefix=/usr')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/sqlite')
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
	return sqlite(
		'shutit.tk.sqlite.sqlite', 0.01215246246,
		description='',
		maintainer='',
		depends=['shutit.tk.make.make']
	)

