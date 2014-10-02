"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule

class devstack(ShutItModule):

	def is_installed(self, shutit):
		return False

	def build(self, shutit):
		shutit.install('git')
		shutit.send('git clone https://github.com/openstack-dev/devstack.git')
		shutit.send('pushd devstack')
		shutit.send('./stack.sh')
		shutit.send('popd')
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
	return devstack(
		'shutit.tk.devstack.devstack', 782914092.00,
		description='',
		maintainer='',
		depends=['shutit.tk.setup']
	)

