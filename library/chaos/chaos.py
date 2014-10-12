"""ShutIt module. See http://shutit.tk
In source, line 16 should be blank, within the build def. This doesn't matter except for test builds, so can be removed once in use.
"""

from shutit_module import ShutItModule


class chaos(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('bzip2')
		shutit.send_host_file('/root/work.sh','context/work.sh')
		shutit.send_host_file('/root/words.txt.bz2','context/words.txt.bz2')
		shutit.send('bunzip2 /root/words.txt.bz2')
		shutit.send('chmod +x /root/work.sh')
		return True

	#def get_config(self, shutit):
	#	return True

	#def check_ready(self, shutit):
	#	return True
	
	#def start(self, shutit):
	#	return True

	#def stop(self, shutit):
	#    return True
	#def finalize(self, shutit):
	#	return True

	#def remove(self, shutit):
	#	return True

	#def test(self, shutit):
	#	return True

def module():
	return chaos(
		'shutit.tk.chaos.chaos', 0.011213525,
		description='Illustrative container that starts process and produces output at random',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup']
	)

