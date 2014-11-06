"""ShutIt module. See http://shutit.tk
In source, line 16 should be blank, within the build def. This doesn't matter except for test builds, so can be removed once in use.
"""

from shutit_module import ShutItModule


class weave(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		#shutit.install('conntracker')
		shutit.install('wget')
		shutit.install('ethtool')
		shutit.send('sudo wget -O /usr/local/bin/weave https://raw.githubusercontent.com/zettio/weave/master/weave')
		shutit.send('sudo chmod a+x /usr/local/bin/weave')
		return True

	#def get_config(self, shutit):
	#	return True

	#def check_ready(self, shutit):
	#	return True
	
	def start(self, shutit):
		# TODO: this is synchronous
		#shutit.send('weave launch')
		return True

	def stop(self, shutit):
		#shutit.send('weave stop')
		return True

	#def finalize(self, shutit):
	#	return True

	#def remove(self, shutit):
	#	return True

	#def test(self, shutit):
	#	return True

def module():
	return weave(
		'shutit.tk.weave.weave', 0.397382568,
		description='',
		maintainer='',
		depends=['shutit.tk.setup','shutit.tk.docker.docker']
	)

