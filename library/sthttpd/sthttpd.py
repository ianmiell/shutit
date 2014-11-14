"""ShutIt module. See http://shutit.tk
"""
from shutit_module import ShutItModule

class sthttpd(ShutItModule):

	def is_installed(self, shutit):
		return False

	def build(self, shutit):
		shutit.install('git')
		shutit.install('gcc')
		shutit.install('make')
		shutit.send('addgroup thttpd')
		shutit.send('pushd /opt')
		shutit.send('git clone git://opensource.dyc.edu/sthttpd sthttpd')
		shutit.send('pushd sthttpd')
		shutit.send('./autogen.sh')
		shutit.send('./configure')
		shutit.send('make')
		shutit.send('make install')
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
	return sthttpd(
		'shutit.tk.sthttpd.sthttpd', 0.1219187350,
		description='Small lightweight web server',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup','shutit.tk.automake.automake']
	)

