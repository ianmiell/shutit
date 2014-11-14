"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class texinfo(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('tar')
		shutit.install('gcc')
		shutit.install('wget')
		shutit.send('pushd /opt')
		shutit.send('mkdir -p texinfo')
		shutit.send('pushd /opt/texinfo')
		shutit.send('wget http://ftp.gnu.org/gnu/texinfo/texinfo-5.2.tar.xz') # appears to be no "latest"
		shutit.send('xz -d texinfo-5.2.tar.xz ')
		shutit.send('tar -xf texinfo-5.2.tar')
		shutit.send('pushd /opt/texinfo/texinfo-5.2')
		shutit.send('./configure')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/texinfo')
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
	return texinfo(
		'shutit.tk.texinfo.texinfo', 0.012515332,
		description='',
		maintainer='',
		depends=['shutit.tk.xz.xz']
	)

