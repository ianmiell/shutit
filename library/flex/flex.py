"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class flex(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('wget')
		shutit.install('m4') # reqiured
		shutit.send('mkdir -p /opt/flex')
		shutit.send('pushd /opt/flex')
		shutit.send('wget http://prdownloads.sourceforge.net/flex/flex-' + shutit.cfg[self.module_id]['version'] + '.tar.bz2')
		shutit.send('bunzip2 flex-' + shutit.cfg[self.module_id]['version'] + '.tar.bz2')
		shutit.send('tar -xf flex-' + shutit.cfg[self.module_id]['version'] + '.tar')
		shutit.send('pushd flex-' + shutit.cfg[self.module_id]['version'])
		shutit.send('./configure --prefix=/usr')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/flex')
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id,'version','2.5.39')
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
	return flex(
		'shutit.tk.flex.flex', 0.0122515332,
		description='Flex',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.bzip2.bzip2']
	)

