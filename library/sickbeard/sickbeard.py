
# Created from dockerfile: /space/git/dockerfiles_repos/Thermionix/Dockerfiles/sickbeard/Dockerfile
from shutit_module import ShutItModule

class sickbeard(ShutItModule):

    def is_installed(self, shutit):
        return False

    def build(self, shutit):
        shutit.install('git python python-cheetah')
        shutit.send('git clone https://github.com/midgetspy/Sick-Beard.git sickbeard')
        return True

    def finalize(self, shutit):
        return True

    def test(self, shutit):
        return True

    def is_installed(self, shutit):
        return False

    def get_config(self, shutit):
        return True

def module():
        return sickbeard(
                'shutit.tk.sickbeard.sickbeard', 0.1561537357,
                depends=['shutit.tk.setup']
        )
