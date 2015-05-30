"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class test11(ShutItModule):


	def build(self, shutit):
		shutit.send('cat > /tmp/a <<< "a"')
		shutit.insert_text('''b
c
d
e''','/tmp/a','a')
		shutit.insert_text('''b
c
d
e''','/tmp/a','^a')
		if shutit.insert_text('''b
c
d
e''','/tmp/nonexistent','^a') != False:
			shutit.fail('test11.3 failed')
		shutit.insert_text('''b
c
d
e''','/tmp/a','^$')
		shutit.insert_text('''b
c
d
e''','/tmp/a','^d$',before=True)
		return True

def module():
	return test11(
		'shutit.tk.test11.test11', 782914092.00,
		description='',
		maintainer='',
		depends=['shutit.tk.setup']
	)

