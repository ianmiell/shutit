"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class test11(ShutItModule):


	def build(self, shutit):
		# simple insert 
		shutit.send('cat > /tmp/a <<< "a"')
		shutit.insert_text('''
b
c
d''','/tmp/a','a')
		shutit.send('cat /tmp/a')
		if shutit.send_and_get_output('md5sum /tmp/a') != '47ece2e49e5c0333677fc34e044d8257  /tmp/a':
			shutit.fail('test11.1 failed')

		# simple insert with regexp
		shutit.send('cat > /tmp/a <<< "abcde"')
		shutit.insert_text('''
b
c
d''','/tmp/a','b.d')
		if shutit.send_and_get_output('md5sum /tmp/a') != 'f013d5d638b770d166be6a9d1f582b73  /tmp/a':
			shutit.fail('test11.2 failed')


		# non-existent file
		if shutit.insert_text('''
b
c
d
e''','/tmp/nonexistent','^a') != False:
			shutit.fail('test11.3 failed')

		# Insert to non-existent line.
		shutit.send('cat > /tmp/a <<< "a"')
		if shutit.insert_text('''
b
c
d
e''','/tmp/a','^$') != None:
			shutit.send('cat /tmp/a')
			shutit.fail('test11.3 failed')


		# Insert text before
		shutit.send_file('/tmp/a',"""a
d""")
		shutit.insert_text('''b
c
''','/tmp/a','d',before=True)
		shutit.send('cat /tmp/a')
		if shutit.send_and_get_output('md5sum /tmp/a') != 'aedeb9f7ddf76f45747fe5f7f6d211dd  /tmp/a':
			shutit.fail('test11.4 failed')

		# simple insert to end
		shutit.send('cat > /tmp/a <<< "a"')
		shutit.insert_text('''b
c
d
''','/tmp/a')
		shutit.send('cat /tmp/a')
		if shutit.send_and_get_output('md5sum /tmp/a') != '47ece2e49e5c0333677fc34e044d8257  /tmp/a':
			shutit.fail('test11.5 failed')

		# simple replace to end
		shutit.send('cat > /tmp/a <<< "a"')
		shutit.replace_text('''b
c
d
''','/tmp/a','a')
		shutit.send('cat /tmp/a')
		shutit.pause_point('')
		if shutit.send_and_get_output('md5sum /tmp/a') != '4e392c10508f911b8110b5ee5f3e5c76  /tmp/a':
			shutit.fail('test11.5 failed')

		return True

def module():
	return test11(
		'shutit.tk.test11.test11', 782914092.00,
		description='',
		maintainer='',
		depends=['shutit.tk.setup']
	)

