"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class apache_portable_runtime_util(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.send('mkdir -p /opt/apr')
		shutit.send('pushd /opt/apr')
		shutit.send('wget http://apache.mirrors.timporter.net/apr/apr-util-' + shutit.cfg[self.module_id]['version'] + '.tar.gz')
		shutit.send('tar -zxf apr-util-' + shutit.cfg[self.module_id]['version'] + '.tar.gz')
		shutit.send('pushd apr-util-' + shutit.cfg[self.module_id]['version'])
		shutit.send('./configure --prefix=/usr --with-apr=/usr')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/apr')
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id,'version','1.5.4')
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
	return apache_portable_runtime_util(
		'shutit.tk.apache_portable_runtime_util.apache_portable_runtime_util', 0.0121546246,
		description='',
		maintainer='',
		depends=['shutit.tk.apache_portable_runtime.apache_portable_runtime']
	)

