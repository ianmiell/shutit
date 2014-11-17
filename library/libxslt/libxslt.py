"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class libxslt(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.send('mkdir -p /opt/libxslt')
		shutit.send('pushd /opt/libxslt')
		shutit.send('wget ftp://xmlsoft.org/libxslt/libxslt-1.1.28.tar.gz')
		shutit.send('gunzip libxslt-1.1.28.tar.gz')
		shutit.send('tar -xf libxslt-1.1.28.tar')
		shutit.send('pushd libxslt-1.1.28')
		shutit.send('./configure --prefix=/usr')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/libxslt')
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
	return libxslt(
		'shutit.tk.libxslt.libxslt', 0.0113125125,
		description='',
		maintainer='',
		depends=['shutit.tk.libxml2.libxml2']
	)

