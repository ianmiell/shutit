"""puppet module from Pro Puppet book.
"""
# Created from dockerfile: /space/git/dockerfiles_repos/puppet/Dockerfile
# Maintainer:              James Turnbull "james@lovedthanlost.net"
from shutit_module import ShutItModule

class puppet(ShutItModule):

    def is_installed(self, shutit):
        return False

    def build(self, shutit):
        shutit.install('puppet')
        shutit.install('puppetmaster') # Only for master
        shutit.install('librarian-puppet')
        shutit.install('ruby')
        shutit.install('libshadow-ruby1.8')
        shutit.install('facter')
        if 'puppet.conf' not in shutit.ls('/etc/puppet'):
        	shutit.send('puppetmasterd --genconfig > puppet.conf')
        # TODO: add:
	#[master]
	#certname=localhost

        #
        shutit.send('mkdir -p /etc/puppet/manifests')
        shutit.send('touch /etc/puppet/manifests/site.pp')

        # TODO: p 14 
        # service puppetmaster start (non-debian)
        # invoke-rc.d puppetmaster start (debian)
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
        depends=['shutit.tk.setup','shutit.tk.ssh_keys']
    )
