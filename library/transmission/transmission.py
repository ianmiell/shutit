
# Created from dockerfile: /space/git/dockerfiles_repos/Thermionix/Dockerfiles/transmission/Dockerfile
from shutit_module import ShutItModule

class transmission(ShutItModule):

    def is_installed(self, shutit):
        return False

    def build(self, shutit):
        shutit.send('export DEBIAN_FRONTEND=noninteractive')
        shutit.send('apt-get update && apt-get install -y transmission-daemon')
        shutit.send('sed -i -e \'/^OPTION/s/"$/ --foreground"/\' /etc/default/transmission-daemon')
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
        return transmission(
                'shutit.tk.transmission.transmission', 0.15246246246,
                depends=['shutit.tk.setup']
        )
