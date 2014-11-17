"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class texinfo(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('tar')
		shutit.install('gcc')
		shutit.install('wget')
		shutit.send('pushd /opt')
		shutit.send('mkdir -p texinfo')
		shutit.send('pushd /opt/texinfo')
		shutit.send('wget http://ftp.gnu.org/gnu/texinfo/texinfo-' + shutit.cfg[self.module_id]['version'] + '.tar.xz')
		shutit.send('xz -d texinfo-' + shutit.cfg[self.module_id]['version'] + '.tar.xz ')
		shutit.send('tar -xf texinfo-' + shutit.cfg[self.module_id]['version'] + '.tar')
		shutit.send('pushd /opt/texinfo/texinfo-' + shutit.cfg[self.module_id]['version'])
		shutit.send('./configure --prefix=/usr')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/texinfo')
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id,'version','5.2')
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
	return texinfo(
		'shutit.tk.texinfo.texinfo', 0.012515332,
		description='',
		maintainer='',
		depends=['shutit.tk.xz.xz']
	)

