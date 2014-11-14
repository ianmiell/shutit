"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class xz(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('tar')
		shutit.install('bzip2')
		shutit.install('wget')
		shutit.install('gcc')
		shutit.install('make')
		shutit.send('pushd /opt')
		shutit.send('wget http://tukaani.org/xz/xz-5.0.7.tar.bz2')
		shutit.send('bunzip2 xz-5.0.7.tar.bz2')
		shutit.send('tar -xf xz-5.0.7.tar')
		shutit.send('pushd /opt/xz-5.0.7')
		shutit.send('./configure')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/xz-*')
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
	return xz(
		'shutit.tk.xz.xz', 0.012513624735,
		description='',
		maintainer='',
		depends=['shutit.tk.setup']
	)

