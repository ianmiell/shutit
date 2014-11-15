"""ShutIt module. See http://shutit.tk
In source, line 16 should be blank, within the build def. This doesn't matter except for test builds, so can be removed once in use.
"""

from shutit_module import ShutItModule


class flex(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('wget')
		shutit.install('m4') # reqiured
		shutit.send('mkdir -p /opt/flex')
		shutit.send('pushd /opt/flex')
		shutit.send('wget http://prdownloads.sourceforge.net/flex/flex-2.5.39.tar.bz2')
		shutit.send('bunzip2 flex-2.5.39.tar.bz2')
		shutit.send('tar -xvf flex-2.5.39.tar')
		shutit.send('pushd flex-2.5.39')
		shutit.send('./configure')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.remove('m4') # reqiured
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
	return flex(
		'shutit.tk.flex.flex', 0.0122515332,
		description='',
		maintainer='',
		depends=['shutit.tk.bzip2.bzip2']
	)

