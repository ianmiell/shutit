"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class ttygif(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('git')
		shutit.install('imagemagick')
		shutit.install('ttyrec')
		shutit.send('pushd /opt')
		shutit.send('git clone https://github.com/icholy/ttygif.git')
		shutit.send('pushd /opt/ttygif')
		shutit.send('make')
		shutit.send('mv ttygif /usr/bin/')
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
	#	return True

	#def finalize(self, shutit):
	#	return True

	#def remove(self, shutit):
	#	return True

	#def test(self, shutit):
	#	return True

def module():
	return ttygif(
		'shutit.tk.ttygif.ttygif', 0.135136139681,
		description='Turn terminal sessions into gifs',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup','shutit.tk.toolchain.toolchain']
	)

