"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class automake(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('tar')
		shutit.install('wget')
		shutit.install('gcc')
		shutit.install('m4')
		shutit.send('pushd /opt')
		shutit.send('mkdir -p automake')
		shutit.send('pushd /opt/automake')
		shutit.send('wget http://ftp.gnu.org/gnu/automake/automake-' + self.cfg[self.module_id]['version'] + '.tar.xz')
		shutit.send('xz -d automake-' + self.cfg[self.module_id]['version'] + '.tar.xz')
		shutit.send('tar -xf automake-' + self.cfg[self.module_id]['version'] + '.tar')
		shutit.send('pushd /opt/automake/automake-' + self.cfg[self.module_id]['version'])
		shutit.send('./configure --prefix=/usr')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/automake')
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id,'version','1.14')
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
	return automake(
		'shutit.tk.automake.automake', 0.011113251352435,
		description='',
		maintainer='',
		depends=['shutit.tk.autoconf.autoconf']
	)

