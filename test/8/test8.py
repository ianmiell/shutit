"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class test8(ShutItModule):


	def build(self, shutit):
		# Some useful API calls for reference see shutit's docs for more info and options:
		# shutit.send(send) - send a command
		# shutit.multisend(send,send_dict) - send a command, dict contains {expect1:response1,expect2:response2,...}
		# shutit.log(msg) - send a message to the log
		# shutit.run_script(script) - run the passed-in string as a script
		# shutit.send_file(path, contents) - send file to path on target with given contents as a string
		# shutit.send_host_file(path, hostfilepath) - send file from host machine to path on the target
		# shutit.send_host_dir(path, hostfilepath) - send directory and contents to path on the target
		# shutit.host_file_exists(filename, directory=False) - returns True if file exists on host
		# shutit.file_exists(filename, directory=False) - returns True if file exists on target
		# shutit.add_to_bashrc(line) - add a line to bashrc
		# shutit.get_url(filename, locations) - get a file via url from locations specified in a list
		# shutit.user_exists(user) - returns True if the user exists on the target
		# shutit.package_installed(package) - returns True if the package exists on the target
		# shutit.pause_point(msg='') - give control of the terminal to the user
		# shutit.step_through(msg='') - give control to the user and allow them to step through commands
		# shutit.send_and_get_output(send) - returns the output of the sent command
		# shutit.install(package) - install a package
		# shutit.remove(package) - remove a package
		# shutit.login(user='root', command='su -') - log user in with given command, and set up prompt and expects
		# shutit.logout() - clean up from a login
		# shutit.set_password(password, user='') - set password for a given user on target
		# shutit.get_config(module_id,option,default=None) - get configuration value
		# shutit.get_ip_address() - returns the ip address of the target
		shutit.add_line_to_file(['asd'],'/tmp/asd')
		shutit.add_line_to_file('asd2','/tmp/asd2')
		shutit.add_line_to_file('asd2','/tmp/asd2')
		shutit.add_line_to_file(['asd3','asd4'],'/tmp/asd2')
		res = shutit.send_and_get_output("""wc -l /tmp/asd2 | awk '{print $1}'""")
		if res != '3':
			shutit.fail('expected 3')
		return True

def module():
	return test8(
		'shutit.tk.test8.test8', 782914092.00,
		description='',
		maintainer='',
		depends=['shutit.tk.setup']
	)

