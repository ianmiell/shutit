"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class tcl(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('gcc')
		shutit.install('wget')
		shutit.install('gzip')
		shutit.send('mkdir -p /opt/tcl')
		shutit.send('pushd /opt/tcl')
		shutit.send('wget http://prdownloads.sourceforge.net/tcl/tcl8.6.3-src.tar.gz')
		shutit.send('gunzip tcl8.6.3-src.tar.gz')
		shutit.send('tar -xf tcl8.6.3-src.tar')
		shutit.send('pushd tcl8.6.3/unix')
		shutit.send('./configure')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('rm -rf /opt/tcl')
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
	return tcl(
		'shutit.tk.tcl.tcl', 0.19125135,
		description='',
	
maintainer='',
		depends=['shutit.tk.yacc.yacc']
	)

