"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class bison(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('tar')
		shutit.install('wget')
		shutit.install('gcc')
		shutit.send('pushd /opt')
		shutit.send('mkdir -p bison')
		shutit.send('pushd /opt/bison')
		version = shutit.cfg[self.module_id]['version']
		shutit.send('wget http://ftp.gnu.org/gnu/bison/bison-' + version + '.tar.gz')
		shutit.send('tar -zxf bison-' + version + '.tar.gz')
		shutit.send('pushd bison-' + version)
		shutit.send('./configure --prefix=/usr/local/bison --with-libiconv-prefix=/usr/local/libiconv/')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/bison')
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id, 'version', '3.0')
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
	return bison(
		'shutit.tk.bison.bison', 0.0191124124756,
		description='Bison compilation',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup','shutit.tk.m4.m4','shutit.tk.make.make']
	)

