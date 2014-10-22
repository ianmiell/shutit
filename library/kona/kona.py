"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class kona(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('git')
		shutit.install('gcc')
		shutit.install('make')
		shutit.send('pushd /opt')
		shutit.send('git clone https://github.com/kevinlawler/kona.git')
		shutit.send('pushd kona')
		shutit.send('make')
		shutit.send('popd')
		shutit.send('popd')
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
	return kona(
		'shutit.tk.kona.kona', 782914092.00,
		description='Open source K interpreter',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup']
	)

