"""ShutIt module. See http://shutit.tk
In source, line 16 should be blank, within the build def. This doesn't matter except for test builds, so can be removed once in use.
"""

from shutit_module import ShutItModule


class nightmare(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('unzip')
		shutit.send('brew update')
		shutit.send('brew install phantomjs')
		shutit.send('npm install --save nightmare')
		return True

	#def get_config(self, shutit):
	#	return True

	#def check_ready(self, shutit):
	#	return True
	
	#def start(self, shutit):
	#	return True

	#def stop(self, shutit):
	#    return True
	#def finalize(self, shutit):
	#	return True

	#def remove(self, shutit):
	#	return True

	#def test(self, shutit):
	#	return True

def module():
	return nightmare(
		'shutit.tk.nightmare.nightmare', 0.35151351,
		description='nightmarejs',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup','shutit.tk.linuxbrew.linuxbrew']
	)

