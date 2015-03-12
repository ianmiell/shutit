"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class pigshell(ShutItModule):

	def build(self, shutit):
		shutit.install('apache2')
		shutit.install('git')
		shutit.install('rubygems-integration')
		shutit.install('make')
		shutit.install('libstdc++-4.9-dev')
		shutit.send('npm install marked --save && echo ""')
		shutit.send('npm install jshint && echo ""')
		shutit.install('ruby2.0-dev') # required to get ronn install to work - see http://hire.chrisjlee.net/node/229
		shutit.send('gem install ronn')
		shutit.send('cd /opt')
		shutit.send('git clone https://github.com/ganeshv/pegjs')
		shutit.send('cd pigshell')
		shutit.send('export PATH=${PATH}:/opt/pegjs/bin:/root/node_modules/marked/bin/')
		shutit.send('make')
		return True

def module():
	return pigshell(
		'shutit.tk.pigshell.pigshell', 0.12659153,
		description='Pigshell on your host',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup','shutit.tk.pigshell.psty','shutit.tk.nodejs.nodejs']
	)

