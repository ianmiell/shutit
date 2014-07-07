
# Created from dockerfile: /space/git/dockerfiles_repos/Thermionix/Dockerfiles/phpmyadmin/Dockerfile
from shutit_module import ShutItModule

class phpmyadmin(ShutItModule):

        def is_installed(self,shutit):
                return False

        def build(self,shutit):
		shutit.send('export DEBIAN_FRONTEND=noninteractive')
		shutit.send('apt-get install -y --no-install-recommends nginx phpmyadmin mcrypt libmcrypt-dev')
                return True

	def finalize(self,shutit):
		return True

	def test(self,shutit):
		return True

	def is_installed(self,shutit):
		return False

	def get_config(self,shutit):
		return True

def module():
        return phpmyadmin(
                'shutit.tk.phpmyadmin.phpmyadmin', 782914092.00,
                depends=['shutit.tk.setup']
        )
