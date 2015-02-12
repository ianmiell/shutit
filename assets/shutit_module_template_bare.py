"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class template(ShutItModule):


	def build(self, shutit):

		return True

def module():
	return template(
		GLOBALLY_UNIQUE_STRING, FLOAT,
		description='',
		maintainer='',
		depends=[DEPENDS]
	)

