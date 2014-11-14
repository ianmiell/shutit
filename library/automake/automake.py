"""ShutIt module. See http://shutit.tk
In source, line 16 should be blank, within the build def. This doesn't matter except for test builds, so can be removed once in use.
"""

from shutit_module import ShutItModule


class automake(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('tar')
		shutit.install('bzip2')
		shutit.install('wget')
		shutit.install('gcc')
		shutit.send('pushd /opt')
		shutit.send('wget http://ftp.gnu.org/gnu/automake/automake-1.14.tar.xz')
		shutit.send('xz -d automake-1.14.tar.xz')
		shutit.send('tar -xf automake-1.14.tar')
		shutit.send('pushd /opt/automake-1.14')
		shutit.send('./configure')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/automake-*')
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
	return automake(
		'shutit.tk.automake.automake', 0.013251352435,
		description='',
		maintainer='',
		depends=['shutit.tk.setup','shutit.tk.xz.xz','shutit.tk.make.make','shutit.tk.autoconf.autoconf']
	)

