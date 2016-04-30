from shutit_module import ShutItModule

class test17(ShutItModule):

	def build(self, shutit):
		return True

def module():
	return test17(
		'test.test17.test17.test17', 101210181.00,
		description='',
		maintainer='',
		depends=['shutit.tk.setup']
	)

