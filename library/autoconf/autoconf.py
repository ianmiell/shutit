"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class autoconf(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('tar')
		shutit.install('gcc')
		shutit.install('m4') # required
		shutit.send('pushd /opt')
		shutit.send('mkdir -p autoconf')
		shutit.send('pushd autoconf')
		shutit.send('wget http://ftp.gnu.org/gnu/autoconf/autoconf-latest.tar.xz')
		shutit.send('xz -d autoconf-latest.tar.xz')
		shutit.send('tar -xf autoconf-latest.tar')
		shutit.send('pushd autoconf-[0-9]*')
		shutit.send('./configure')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/autoconf')
		shutit.remove('m4') # required
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
		'shutit.tk.autoconf.autoconf', 0.010925156,
		description='',
		maintainer='',
		depends=['shutit.tk.setup','shutit.tk.xz.xz','shutit.tk.make.make']
	)

