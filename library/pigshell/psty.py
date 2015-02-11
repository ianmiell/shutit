"""ShutIt module. See http://shutit.tk

Runs a psty server
"""

from shutit_module import ShutItModule


class psty(ShutItModule):

	def build(self, shutit):
		shutit.install('python')
		shutit.install('git')
		shutit.send('pushd /opt')
		shutit.send('git clone https://github.com/pigshell/pigshell.git')
		shutit.send('mkdir -p /var/psty_dir')
		return True

	def start(self, shutit):
		shutit.send('pushd /opt/pigshell')
		shutit.send('nohup python psty.py -a -d /var/psty_dir &')
		return True

	def stop(self, shutit):
		shutit.send('''ps -ef | grep "python psty -a -d /var/psty_dir" | grep -v grep | awk '{print $1}' | xargs -r kill''')
		return True

def module():
	return psty(
		'shutit.tk.pigshell.psty', 0.12659152,
		description='Runs a local psty server for pigshell.com',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup']
	)

