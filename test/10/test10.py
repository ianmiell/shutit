from shutit_module import ShutItModule

class test10(ShutItModule):

	def build(self, shutit):
		if not shutit.send_and_match_output('echo "A STRING"','A STR'):
			shutit.fail('test10.1 failed')
		if not shutit.send_and_match_output('echo "A STRING"','A STRING'):
			shutit.fail('test10.2 failed')
		if shutit.send_and_match_output('echo "A STRING"','NO MATCH'):
			shutit.fail('test10.3 failed')
		if not shutit.send_and_match_output(r'''cat > /dev/stdout << END
A STRING
TWO LINES"
END''','A STRING'):
			shutit.fail('test10.4 failed')
		if shutit.send_and_match_output(r'''cat > /dev/stdout << END
A STRING
TWO LINES
END''','NO MATCH'):
			shutit.fail('test10.5 failed')
		return True

def module():
	return test10(
		'shutit.tk.test10.test10', 782914092.00,
		description='',
		maintainer='',
		depends=['shutit.tk.setup']
	)

