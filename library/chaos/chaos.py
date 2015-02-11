"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class chaos(ShutItModule):

	def build(self, shutit):
		shutit.install('bzip2')
		shutit.send_host_file('/root/work.sh','context/work.sh')
		shutit.send_host_file('/root/words.txt.bz2','context/words.txt.bz2')
		shutit.send('bunzip2 /root/words.txt.bz2')
		shutit.send('chmod +x /root/work.sh')
		return True

def module():
	return chaos(
		'shutit.tk.chaos.chaos', 0.011213525,
		description='Illustrative module that starts process and produces output at random',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup']
	)

