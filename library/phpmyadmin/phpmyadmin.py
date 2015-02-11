# Created from dockerfile: /space/git/dockerfiles_repos/Thermionix/Dockerfiles/phpmyadmin/Dockerfile
from shutit_module import ShutItModule

class phpmyadmin(ShutItModule):

	def build(self, shutit):
		shutit.install('nginx phpmyadmin mcrypt libmcrypt-dev')
		return True

def module():
		return phpmyadmin(
				'shutit.tk.phpmyadmin.phpmyadmin', 0.1561234737,
				depends=['shutit.tk.setup']
		)
