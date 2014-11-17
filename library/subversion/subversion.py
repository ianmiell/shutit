"""ShutIt module. See http://shutit.tk
In source, line 16 should be blank, within the build def. This doesn't matter except for test builds, so can be removed once in use.
"""

from shutit_module import ShutItModule


class subversion(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.send('mkdir -p /opt/subversion')
		shutit.send('pushd /opt/subversion')
		shutit.send('wget http://mirror.gopotato.co.uk/apache/subversion/subversion-' + shutit.cfg[self.module_id]['version'] + '.tar.gz')
		shutit.send('tar -zxf subversion-' + shutit.cfg[self.module_id]['version'] + '.tar.gz')
		shutit.send('pushd subversion-' + shutit.cfg[self.module_id]['version'])
		shutit.send('./configure --prefix=/usr')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/subversion')
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id,'version','1.8.10')
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
	return subversion(
		'shutit.tk.subversion.subversion', 0.012532473,
		description='',
		maintainer='',
		depends=['shutit.tk.apache_portable_runtime_util.apache_portable_runtime_util','shutit.tk.sqlite.sqlite']
	)

