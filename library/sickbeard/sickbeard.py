
# Created from dockerfile: /space/git/dockerfiles_repos/Thermionix/Dockerfiles/sickbeard/Dockerfile
from shutit_module import ShutItModule

class sickbeard(ShutItModule):

	def build(self, shutit):
		shutit.install('git python python-cheetah')
		shutit.send('git clone https://github.com/midgetspy/Sick-Beard.git sickbeard')
		return True

def module():
		return sickbeard(
				'shutit.tk.sickbeard.sickbeard', 0.1561537357,
				depends=['shutit.tk.setup']
		)
