"""ShutIt module. See http://shutit.tk
"""
from shutit_module import ShutItModule

class fpm(ShutItModule):

	def is_installed(self, shutit):
		return False

	def build(self, shutit):
		shutit.install('ruby')
		shutit.install('rubygems')
		shutit.install('ruby-dev')
		shutit.install('gcc')
		shutit.send('gem install fpm')
		return True

	#def get_config(self, shutit):
	#    return True

	#def check_ready(self, shutit):
	#    return True
	
	#def start(self, shutit):
	#    return True

	#def stop(self, shutit):
	#    return True
	#def finalize(self, shutit):
	#    return True

	#def remove(self, shutit):
	#    return True

	#def test(self, shutit):
	#    return True

def module():
	return fpm(
		'shutit.tk.fpm.fpm', 0.1592387529835,
		description='Flippant package manager',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup']
	)

