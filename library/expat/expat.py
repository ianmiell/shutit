"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class expat(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.send('mkdir -p /opt/expat')
		shutit.send('pushd /opt/expat')
		shutit.send('wget -O expat.tar.gz http://downloads.sourceforge.net/project/expat/expat/' + shutit.cfg[self.module_id]['version'] + '/expat-' + shutit.cfg[self.module_id]['version'] + '.tar.gz')
		shutit.send('tar -zxf expat.tar')
		shutit.send('pushd expat-' + shutit.cfg[self.module_id]['version'])
		shutit.send('./configure --prefix=/usr')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/expat')
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id,'version','2.1.0')
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
	return expat(
		'shutit.tk.expat.expat', 0.0125163462346,
		description='',
		maintainer='',
		depends=['shutit.tk.make.make']
	)

