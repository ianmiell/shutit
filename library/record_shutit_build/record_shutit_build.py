"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class record_shutit_build(ShutItModule):

	def is_installed(self, shutit):
		# Always run this
		return False


	def build(self, shutit):
		# default the delivery to bash here
		shutit.add_to_bashrc('''export SHUTIT_OPTIONS="$SHUTIT_OPTIONS --delivery bash"''')
		return True

def module():
	return record_shutit_build(
		'shutit.tk.record_shutit_build.record_shutit_build', 0.39952141313136,
		description='Module to record a shutit build. See README.md in the source folder.',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup','shutit.tk.shutit.shutit','shutit.tk.ttygif.ttygif','shutit.tk.docker.docker']
	)

