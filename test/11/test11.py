"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class test11(ShutItModule):


	def build(self, shutit):

		################################################################################
		# NON-LINE-ORIENTED TESTS
		################################################################################
		# simple insert 
		shutit.send('cat > /tmp/a <<< "a"')
		shutit.insert_text('''
b
c
d''','/tmp/a','a',line_oriented=False)
		shutit.send('cat /tmp/a')
		if shutit.send_and_get_output('md5sum /tmp/a') != '47ece2e49e5c0333677fc34e044d8257  /tmp/a':
			shutit.fail('test11.1 failed')

		# simple insert with regexp
		shutit.send('cat > /tmp/a <<< "abcde"')
		shutit.insert_text('''
b
c
d''','/tmp/a','b.d',line_oriented=False)
		if shutit.send_and_get_output('md5sum /tmp/a') != 'f013d5d638b770d166be6a9d1f582b73  /tmp/a':
			shutit.fail('test11.2 failed')


		# Insert to non-existent line.
		shutit.send('cat > /tmp/a <<< "a"')
		if shutit.insert_text('''
b
c
d
e''','/tmp/a','^asfasfa$',line_oriented=False) != None:
			shutit.send('cat /tmp/a')
			shutit.fail('test11.3 failed')


		# Insert text before
		shutit.send_file('/tmp/a',"""a
d""")
		shutit.insert_text('''b
c
''','/tmp/a','d',before=True,line_oriented=False)
		shutit.send('cat /tmp/a')
		if shutit.send_and_get_output('md5sum /tmp/a') != 'aedeb9f7ddf76f45747fe5f7f6d211dd  /tmp/a':
			shutit.fail('test11.4 failed')

		# simple insert to end
		shutit.send('cat > /tmp/a <<< "a"')
		shutit.insert_text('''b
c
d
''','/tmp/a',line_oriented=False)
		shutit.send('cat /tmp/a')
		if shutit.send_and_get_output('md5sum /tmp/a') != '47ece2e49e5c0333677fc34e044d8257  /tmp/a':
			shutit.fail('test11.5 failed')

		# simple replace
		shutit.send('cat > /tmp/11.6 <<< "a"')
		shutit.replace_text('''b
c
d
''','/tmp/11.6','^a$',line_oriented=False)
		shutit.send('cat /tmp/11.6')
		if shutit.send_and_get_output('md5sum /tmp/11.6') != '4e392c10508f911b8110b5ee5f3e5c76  /tmp/11.6':
			shutit.fail('test11.6 failed')

		# simple replace with non-matching pattern
		shutit.send('cat > /tmp/11.7 <<< "a"')
		shutit.replace_text('''b
c
d
''','/tmp/11.7','willnotmatch',line_oriented=False)
		if shutit.send_and_get_output('md5sum /tmp/11.7') != '47ece2e49e5c0333677fc34e044d8257  /tmp/11.7':
			shutit.fail('test11.7 failed')

		################################################################################
		# LINE ORIENTED TESTS
		################################################################################
		# simple insert 
		shutit.send('cat > /tmp/a <<< "a"')
		shutit.insert_text('''b
c
d''','/tmp/a','a')
		shutit.send('cat /tmp/a')
		if shutit.send_and_get_output('md5sum /tmp/a') != '47ece2e49e5c0333677fc34e044d8257  /tmp/a':
			shutit.fail('test11.1.1 failed')

		# simple insert with regexp
		shutit.send('cat > /tmp/a <<< "abcde"')
		shutit.insert_text('''b
c
d''','/tmp/a','b.d')
		if shutit.send_and_get_output('md5sum /tmp/a') != 'fd5505764070ee318d08b5ca03b46075  /tmp/a':
			shutit.fail('test11.1.2 failed')


		# Insert to non-existent line.
		shutit.send('cat > /tmp/a <<< "a"')
		if shutit.insert_text('''b
c
d
e''','/tmp/a','^asfasfa$') != None:
			shutit.send('cat /tmp/a')
			shutit.fail('test11.4.2 failed')


		# Insert text before
		shutit.send_file('/tmp/a',"""a
d""")
		shutit.insert_text('''b
c''','/tmp/a','^d$',before=True)
		shutit.send('cat /tmp/a')
		if shutit.send_and_get_output('md5sum /tmp/a') != 'aedeb9f7ddf76f45747fe5f7f6d211dd  /tmp/a':
			shutit.fail('test11.5.2 failed')

		# simple insert to end
		shutit.send('cat > /tmp/a <<< "a"')
		shutit.insert_text('''b
c
d''','/tmp/a')
		shutit.send('cat /tmp/a')
		if shutit.send_and_get_output('md5sum /tmp/a') != '47ece2e49e5c0333677fc34e044d8257  /tmp/a':
			shutit.fail('test11.6.2 failed')

		# simple replace
		shutit.send('cat > /tmp/11.7 <<< "a"')
		shutit.replace_text('''b
c
d''','/tmp/11.7','^a$')
		shutit.send('cat /tmp/11.7')
		if shutit.send_and_get_output('md5sum /tmp/11.7') != '621998bb3ef787c4ac1408b5b9c8bef5  /tmp/11.7':
			shutit.fail('test11.7.2 failed')

		# simple replace with non-matching pattern
		shutit.send('cat > /tmp/11.8 <<< "a"')
		shutit.replace_text('''b
c
d''','/tmp/11.8','willnotmatch')
		if shutit.send_and_get_output('md5sum /tmp/11.8') != '47ece2e49e5c0333677fc34e044d8257  /tmp/11.8':
			shutit.fail('test11.8.2 failed')


		# double send
		shutit.send('''cat > /tmp/11.9 << END
a line
another line
END''')
		shutit.replace_text('a new line','/tmp/11.9','new')
		shutit.replace_text('a new line','/tmp/11.9','new')
		if shutit.send_and_get_output('md5sum /tmp/11.9') != 'a9caca3131db43f6edb241c898d1ba69  /tmp/11.9':
			shutit.fail('test11.9.2 failed')

		# replace (append), replace, insert, replace, delete
		shutit.send('''cat > /tmp/11.10 << END
a line
another line
END''')
		shutit.replace_text('a new line','/tmp/11.10','new')
		shutit.replace_text('a new line','/tmp/11.10','new')
		shutit.insert_text('yet another line','/tmp/11.10')
		shutit.replace_text('a new line','/tmp/11.10','new')
		shutit.delete_text('yet another line','/tmp/11.10')
		if shutit.send_and_get_output('md5sum /tmp/11.10') != 'a9caca3131db43f6edb241c898d1ba69  /tmp/11.10':
			shutit.fail('test11.10.2 failed')

		# everything we can think of
		shutit.send('''cat > /tmp/11.11 << END
first line
second line
fourth line
END''')
		shutit.insert_text('third line','/tmp/11.11','^sec')
		shutit.insert_text('third line','/tmp/11.11','second line')
		shutit.insert_text('fifth line','/tmp/11.11','fourth line')
		if shutit.send_and_get_output('md5sum /tmp/11.11') != '3538d04b11225ee34267767861c7e60c  /tmp/11.11':
			shutit.fail('test11.11.2.1 failed')
		shutit.replace_text('fifth line','/tmp/11.11','^fif')
		if shutit.send_and_get_output('md5sum /tmp/11.11') != '3538d04b11225ee34267767861c7e60c  /tmp/11.11':
			shutit.fail('test11.11.2.2 failed')
		shutit.replace_text('third line','/tmp/11.11','^thi')
		if shutit.send_and_get_output('md5sum /tmp/11.11') != '3538d04b11225ee34267767861c7e60c  /tmp/11.11':
			shutit.fail('test11.11.2.3 failed')
		return True

def module():
	return test11(
		'shutit.tk.test11.test11', 782914092.00,
		description='',
		maintainer='',
		depends=['shutit.tk.setup']
	)

