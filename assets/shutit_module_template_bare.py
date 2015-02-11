"""ShutIt module. See http://shutit.tk
In source, line 11 should be blank, within the build def. This doesn't matter except for test builds, so can be removed once in use.
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
		depends=['shutit.tk.setup']
	)

