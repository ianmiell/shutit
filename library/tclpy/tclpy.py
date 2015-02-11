"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule

class tclpy(ShutItModule):

	def build(self,shutit):
		shutit.install('tcl-dev')
		shutit.install('python-dev')
		shutit.install('git')
		shutit.install('make')
		shutit.install('gcc')
		shutit.send('pushd /opt')
		shutit.send('git clone https://github.com/aidanhs/libtclpy.git')
		shutit.send('pushd libtclpy')
		shutit.send('make')
		# TODO: make install?
		shutit.send('cp libtclpy* /lib')
		shutit.send('popd')
		shutit.send('popd')
		return True

def module():
	return tclpy(
		'shutit.tk.tclpy.tclpy', 0.0125235135315,
		description='',
		maintainer='',
		depends=['shutit.tk.setup']
	)

