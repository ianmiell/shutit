"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class gettext(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('tar')
		shutit.install('gcc')
		shutit.send('pushd /opt')
		shutit.send('mkdir -p /opt/gettext')
		shutit.send('pushd /opt/gettext')
		shutit.send('wget http://ftp.gnu.org/pub/gnu/gettext/gettext-' + shutit.cfg[self.module_id]['version'] + '.tar.xz')
		shutit.send('xz -d gettext-' + shutit.cfg[self.module_id]['version'] + '.tar.xz')
		shutit.send('tar -xf gettext-' + shutit.cfg[self.module_id]['version'] + '.tar')
		shutit.send('pushd /opt/gettext/gettext-' + shutit.cfg[self.module_id]['version'])
		shutit.send('./configure --prefix=/usr')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/gettext')
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id,'version','0.19.3')
		return True

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
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.autoconf.autoconf']
	)

