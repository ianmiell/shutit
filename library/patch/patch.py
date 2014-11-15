"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class patch(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('wget')
		shutit.send('mkdir -p /opt/patch')
		shutit.send('pushd /opt/patch')
		shutit.send('wget http://ftp.gnu.org/gnu/patch/patch-2.7.tar.gz')
		shutit.send('gunzip patch-2.7.tar.gz')
		shutit.send('tar -xf patch-2.7.tar')
		shutit.send('pushd patch-2.7')
		shutit.send('./configure --prefix=/usr')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/patch')
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
	return patch(
		'shutit.tk.patch.patch', 0.01315136,
		description='',
		maintainer='',
		depends=['shutit.tk.make.make']
	)

