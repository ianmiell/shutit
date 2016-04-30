from shutit_module import ShutItModule

class test12(ShutItModule):


	def build(self, shutit):
		a = 'a' * 5000
		shutit.send_file('/tmp/a',a)
		if shutit.send_and_get_output('md5sum /tmp/a') != '7aaa7dec709fa4fa82f3746abfd80bdb  /tmp/a':
			shutit.fail('test12 failed')
		return True

def module():
	return test12(
		'shutit.tk.test12.test12', 782914092.00,
		description='',
		maintainer='',
		depends=['shutit.tk.setup']
	)

