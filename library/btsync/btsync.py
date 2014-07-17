
# Created from dockerfile: /space/git/dockerfiles_repos/billt2006/docker-btsync/Dockerfile
from shutit_module import ShutItModule

class btsync(ShutItModule):

        def is_installed(self, shutit):
                return False

        def build(self, shutit):
		shutit.send('apt-get update && apt-get install -y curl')
		shutit.send('curl -o /usr/bin/btsync.tar.gz http://download-lb.utorrent.com/endpoint/btsync/os/linux-x64/track/stable')
		shutit.send('cd /usr/bin && tar -xzvf btsync.tar.gz && rm btsync.tar.gz')
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
        return btsync(
                'shutit.tk.btsync.btsync', 0.15673135,
                depends=['shutit.tk.setup']
        )
