
# Created from dockerfile: ./Dockerfile
from shutit_module import ShutItModule

class plex(ShutItModule):

        def is_installed(self, shutit):
                return False

        def build(self, shutit):
		shutit.install('wget')
		shutit.send('apt-get -q update && apt-get install -qy --force-yes avahi-daemon avahi-utils')
		shutit.send('wget -O /plexmediaserver.deb http://downloads.plexapp.com/plex-media-server/0.9.9.12.504-3e7f93c/plexmediaserver_0.9.9.12.504-3e7f93c_amd64.deb')
		shutit.send('dpkg -i /plexmediaserver.deb')
		shutit.send('rm /plexmediaserver.deb')
		shutit.send('sed -i "s/rlimit-nproc=3/#rlimit-nproc=3/" /etc/avahi/avahi-daemon.conf')
		shutit.send_host_file('/start.sh','context/./start.sh')
		shutit.send('chmod u+x /start.sh')
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
        return plex(
                'shutit.tk.plex.plex', 0.156123464246,
                depends=['shutit.tk.setup']
        )
