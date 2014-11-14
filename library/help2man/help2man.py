"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class help2man(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('wget')
		shutit.install('xz-utils')
		shutit.install('tar')
		shutit.install('gcc')
		shutit.install('make')
		shutit.send('pushd /opt')
		shutit.send('wget http://ftp.gnu.org/gnu/help2man/help2man-1.46.4.tar.xz')
		shutit.send('xz -d help2man-1.46.4.tar.xz')
		shutit.send('tar -xf help2man-1.46.4.tar')
		shutit.send('pushd help2man-1.46.4')
		shutit.send('./configure')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/help2man*')
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
	return help2man(
		'shutit.tk.help2man.help2man', 0.01124135,
		description='',
		maintainer='',
		depends=['shutit.tk.setup']
	)

