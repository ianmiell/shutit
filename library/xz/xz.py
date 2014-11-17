"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class xz(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('tar')
		shutit.install('gcc')
		shutit.install('wget')
		shutit.send('pushd /opt')
		shutit.send('mkdir -p /opt/xz')
		shutit.send('pushd /opt/xz')
		shutit.send('wget http://tukaani.org/xz/xz-' + shutit.cfg[self.module_id]['version'] + '.tar.bz2')
		shutit.send('bunzip2 xz-' + shutit.cfg[self.module_id]['version'] + '.tar.bz2')
		shutit.send('tar -xf xz-' + shutit.cfg[self.module_id]['version'] + '.tar')
		shutit.send('pushd /opt/xz/xz-' + shutit.cfg[self.module_id]['version'])
		shutit.send('./configure --prefix=/usr')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/xz')
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id,'version','5.0.7')
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
	return xz(
		'shutit.tk.xz.xz', 0.0102513624735,
		description='',
		maintainer='',
		depends=['shutit.tk.bzip2.bzip2']
	)

