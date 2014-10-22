"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule

class luakernel(ShutItModule):

	def is_installed(self, shutit):
		return False

	def build(self, shutit):
		shutit.install('git')
		shutit.install('make')
		shutit.install('gcc')
		shutit.install('libc6-dev-i386')
		shutit.install('gcc-multilib')
		shutit.install('xorriso')
		shutit.install('lua5.2')
		shutit.install('grub-common')
		shutit.send('export CPATH=/usr/include/x86_64-linux-gnu:/usr/include')
		shutit.send('export LIBRARY_PATH=/lib:/lib32:/libx32:/lib64')
		shutit.send('git clone https://github.com/ers35/luakernel.git')
		shutit.send('cd luakernel')
		shutit.send('make')
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
	return luakernel(
		'shutit.tk.luakernel.luakernel', 0.125413461,
		description='',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup']
	)

