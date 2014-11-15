"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class asciidoc(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		#http://www.methods.co.nz/asciidoc/INSTALL.html#X1
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
	return asciidoc(
		'shutit.tk.asciidoc.asciidoc', 782914092.00,
		description='',
		maintainer='',
		depends=['shutit.tk.setup']
	)

