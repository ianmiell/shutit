
# Created from dockerfile: https://raw.githubusercontent.com/tianon/dockerfiles/master/steam/Dockerfile
from shutit_module import ShutItModule

class steam(ShutItModule):

	def is_installed(self, shutit):
		return False

	def build(self, shutit):
		shutit.install('steam-launcher')
		shutit.send('echo \'deb http://repo.steampowered.com/steam $(lsb_release -s -c) steam\' > /etc/apt/sources.list.d/steam.list && dpkg --add-architecture i386')
		shutit.send('apt-get update')
		shutit.install('libgl1-mesa-dri:i386')
		shutit.install('libgl1-mesa-glx:i386')
		shutit.install('libc6:i386')
		shutit.install('sudo')
		shutit.send('echo \'steam ALL = NOPASSWD: ALL\' > /etc/sudoers.d/steam')
		shutit.send('chmod 0440 /etc/sudoers.d/steam')
		shutit.send('adduser --disabled-password --gecos \'Steam\' steam')
		shutit.send('adduser steam video')
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
	return steam(
		'shutit.tk.steam.steam', 0.12135315,
		depends=['shutit.tk.setup']
	)
