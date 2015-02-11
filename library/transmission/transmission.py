
# Created from dockerfile: /space/git/dockerfiles_repos/Thermionix/Dockerfiles/transmission/Dockerfile
from shutit_module import ShutItModule

class transmission(ShutItModule):

	def build(self, shutit):
		shutit.install('transmission-daemon')
		shutit.send('sed -i -e \'/^OPTION/s/"$/ --foreground"/\' /etc/default/transmission-daemon')
		return True

def module():
		return transmission(
				'shutit.tk.transmission.transmission', 0.15246246246,
				depends=['shutit.tk.setup']
		)
