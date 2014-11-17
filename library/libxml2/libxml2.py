"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class libxml2(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.send('mkdir -p /opt/libxml2')
		shutit.send('pushd /opt/libxml2')
		shutit.send('wget ftp://xmlsoft.org/libxslt/libxml2-sources-' + shutit.cfg[self.module_id]['version'] + '.tar.gz')
		shutit.send('tar -zxf libxml2-sources-' + shutit.cfg[self.module_id]['version'] + '.tar.gz')
		shutit.send('pushd libxml2-' + shutit.cfg[self.module_id]['version'])
		shutit.send('./configure --prefix=/usr')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/libxml2')
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id,'version','2.9.2')
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
	return libxml2(
		'shutit.tk.libxml2.libxml2', 0.011125135,
		description='',
		maintainer='',
		depends=['shutit.tk.make.make']
	)

