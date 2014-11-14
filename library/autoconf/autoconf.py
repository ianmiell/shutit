"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class autoconf(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('make')
		shutit.install('tar')
		shutit.install('gcc')
		shutit.send('pushd /opt')
		shutit.send('wget http://ftp.gnu.org/gnu/autoconf/autoconf-2.64.tar.xz')
		shutit.send('xz -d autoconf-2.64.tar.xz')
		shutit.send('tar -xf autoconf-2.64.tar')
		shutit.send('pushd autoconf-2.64')
		shutit.send('./configure')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/autoconf-*')
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
	return autoconf(
		'shutit.tk.autoconf.autoconf', 0.01925156,
		description='',
		maintainer='',
		depends=['shutit.tk.setup','shutit.tk.xz.xz','shutit.tk.m4.m4']
	)

