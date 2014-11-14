"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class yacc(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('tar')
		shutit.install('gcc')
		shutit.install('wget')
		shutit.send('pushd /opt')
		shutit.send('mkdir -p byacc')
		shutit.send('pushd /opt/byacc')
		shutit.send('wget http://invisible-island.net/datafiles/release/byacc.tar.gz')
		shutit.send('tar -zxf byacc.tar.gz')
		shutit.send('pushd byacc-*') # don't know date in dirname
		shutit.send('./configure --prefix=/usr')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/byacc')
		return True

	#def get_config(self, shutit):
	#	return True

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
	return yacc(
		'shutit.tk.yacc.yacc', 0.0121325,
		description='',
		maintainer='',
		depends=['shutit.tk.setup','shutit.tk.make.make']
	)

