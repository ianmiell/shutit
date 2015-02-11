"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class laravel(ShutItModule):


	def build(self, shutit):
		shutit.install('php5-json')
		shutit.add_to_bashrc('PATH=${PATH}:~/.composer/vendor/bin')
		shutit.send('composer global require "laravel/installer=~1.1"')
		return True

def module():
	return laravel(
		'shutit.tk.laravel.laravel', 0.37,
		description='http://laravel.com',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup','shutit.tk.composer.composer']
	)

