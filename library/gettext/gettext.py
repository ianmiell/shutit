"""ShutIt module. See http://shutit.tk
In source, line 16 should be blank, within the build def. This doesn't matter except for test builds, so can be removed once in use.
"""

from shutit_module import ShutItModule


class gettext(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('tar')
		shutit.install('bzip2')
		shutit.install('wget')
		shutit.install('gcc')
		shutit.send('pushd /opt')
		shutit.send('wget http://ftp.gnu.org/pub/gnu/gettext/gettext-0.19.3.tar.xz')
		shutit.send('xz -d gettext-0.19.3.tar.xz')
		shutit.send('tar -xf gettext-0.19.3.tar')
		shutit.send('pushd /opt/gettext-0.19.3')
		shutit.send('./configure')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/gettext-*')
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
	return gettext(
		'shutit.tk.gettext.gettext', 0.019531361436,
		description='',
		maintainer='',
		depends=['shutit.tk.setup','shutit.tk.xz.xz','shutit.tk.autoconf.autoconf','shutit.tk.make.make']
	)

