"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class toolchain(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('gcc')
		shutit.install('make')
		shutit.install('autoconf')
		shutit.install('automake')
		shutit.install('flex')
		shutit.install('bison')
		shutit.install('m4')
		shutit.install('g++')
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
	return toolchain(
		'shutit.tk.toolchain.toolchain', 0.01212513461,
		description='Helper module for tools needed for compilation etc..',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup']
	)

