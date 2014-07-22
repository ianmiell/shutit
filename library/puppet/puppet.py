
# Created from dockerfile: /space/git/dockerfiles_repos/puppet/Dockerfile
# Maintainer:              James Turnbull "james@lovedthanlost.net"
from shutit_module import ShutItModule

class puppet(ShutItModule):

    def is_installed(self, shutit):
        return False

    def build(self, shutit):
        shutit.install('puppet librarian-puppet')
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
    return puppet(
        'shutit.tk.puppet.puppet', 0.012412487,
        description='Puppet reference build',
        depends=['shutit.tk.setup']
    )
