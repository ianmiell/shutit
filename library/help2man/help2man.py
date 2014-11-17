"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class help2man(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('tar')
		shutit.install('gcc')
		shutit.install('wget')
		shutit.send('pushd /opt')
		shutit.send('mkdir -p /opt/help2man')
		shutit.send('pushd /opt/help2man')
		shutit.send('wget http://ftp.gnu.org/gnu/help2man/help2man-' + shutit.cfg[self.module_id]['version'] + '.tar.xz')
		shutit.send('xz -d help2man-' + shutit.cfg[self.module_id]['version'] + '.tar.xz')
		shutit.send('tar -xf help2man-' + shutit.cfg[self.module_id]['version'] + '.tar')
		shutit.send('pushd help2man-' + shutit.cfg[self.module_id]['version'] + '')
		shutit.send('./configure --prefix=/usr')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/help2man')
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id,'version','1.46.4')
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
	return help2man(
		'shutit.tk.help2man.help2man', 0.01324135,
		description='',
		maintainer='',
		depends=['shutit.tk.texinfo.texinfo']
	)

