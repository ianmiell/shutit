"""ShutIt module. See http://shutit.tk
"""
from shutit_module import ShutItModule

class sthttpd(ShutItModule):

	def is_installed(self, shutit):
		return False

	def build(self, shutit):
		shutit.install('git')
		shutit.send('pushd /opt')
		shutit.send('git clone git://opensource.dyc.edu/sthttpd sthttpd')
		shutit.send('pushd sthttpd')

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
		'shutit.tk.sthttpd.sthttpd', 782914092.00,
		description='',
		maintainer='',
		depends=['shutit.tk.setup']
	)

