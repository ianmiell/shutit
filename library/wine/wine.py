
# Created from dockerfile: /tmp/b/Dockerfile
# Maintainer:              Brandon R. Stoner <monokrome@monokro.me>
from shutit_module import ShutItModule

class wine(ShutItModule):

	def build(self, shutit):
		shutit.install('python-software-properties')
		shutit.install('software-properties-common')
		shutit.send('add-apt-repository -y ppa:ubuntu-wine/ppa')
		#shutit.send("sed -i 's/main/main universe/' /etc/apt/sources.list")
		shutit.send('apt-get update -y')
		shutit.install('wine1.7')
		shutit.install('winetricks')
		return True

def module():
		return wine(
				'shutit.tk.wine.wine', 0.3512412125135,
				description='Wine on docker',
				maintainer='Brandon R. Stoner <monokrome@monokro.me>',
				depends=['shutit.tk.setup','shutit.tk.vnc.vnc']
		)
