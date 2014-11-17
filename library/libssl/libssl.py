"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class libssl(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		#https://www.openssl.org/source/
		shutit.send('mkdir -p /opt/libssl')
		shutit.send('pushd /opt/libssl')
		shutit.send('wget https://www.openssl.org/source/openssl-' + shutit.cfg[self.module_id]['version'] + '.tar.gz')
		shutit.send('tar -zxf openssl-' + shutit.cfg[self.module_id]['version'] + '.tar')
		shutit.send('pushd openssl-' + shutit.cfg[self.module_id]['version'])
		shutit.send('./config --prefix=/usr')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/libssl')
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id,'version','1.0.1j')
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
	return libssl(
		'shutit.tk.libssl.libssl', 0.010125136,
		description='',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.make.make']
	)

