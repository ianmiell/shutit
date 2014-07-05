
# Created from dockerfile: https://raw.githubusercontent.com/x3tech/dockerfiles/master/supervisord/Dockerfile
from shutit_module import ShutItModule

class supervisord(ShutItModule):

        def is_installed(self,shutit):
                return False

        def build(self,shutit):
		shutit.install('pacman')
		shutit.send('pacman -Sy && pacman -S --noconfirm supervisor && pacman -Scc --noconfirm')
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
        return supervisord(
                'shutit.tk.supervisord.supervisord', 782914092.00,
                depends=['shutit.tk.setup']
        )
