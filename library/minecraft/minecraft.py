
# Created from dockerfile: /space/git/dockerfiles_repos/Dockerfiles/minecraft/Dockerfile
from shutit_module import ShutItModule

class minecraft(ShutItModule):

        def is_installed(self,shutit):
                return False

        def build(self,shutit):
		shutit.send('echo "deb http://archive.ubuntu.com/ubuntu precise main universe" > /etc/apt/sources.list')
		shutit.send('apt-get update')
		shutit.send('apt-get install -y python-software-properties')
		shutit.send('add-apt-repository ppa:webupd8team/java -y')
		shutit.send('apt-get update')
		shutit.send('echo oracle-java7-installer shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections')
		shutit.install('oracle-java7-installer')
		shutit.install('wget')
		shutit.send('mkdir /minecraft')
		shutit.send('wget -O /minecraft/minecraft.jar https://s3.amazonaws.com/Minecraft.Download/versions/1.7.4/minecraft_server.1.7.4.jar')
		shutit.send('pushd /minecraft')
		shutit.send('popd')
                return True

	def finalize(self,shutit):
		return True

	def test(self,shutit):
		return True

	def is_installed(self,shutit):
		return False

	def get_config(self,shutit):
		return True

def module():
        return minecraft(
                'shutit.tk.minecraft.minecraft', 0.12153353,
                depends=['shutit.tk.setup']
        )
