
# Created from dockerfile: /space/git/dockerfiles_repos/dockerfile-examples/nodejs/Dockerfile
from shutit_module import ShutItModule

class nodejs(ShutItModule):

        def is_installed(self,shutit):
                return False

        def build(self,shutit):
		shutit.send('apt-get install -y python-software-properties python')
		shutit.send('add-apt-repository ppa:chris-lea/node.js')
		shutit.send('echo "deb http://us.archive.ubuntu.com/ubuntu/ precise universe" >> /etc/apt/sources.list')
		shutit.send('apt-get update')
		shutit.send('apt-get install -y nodejs')
		shutit.send('mkdir /var/www')
		shutit.send_host_file('/var/www/app.js','context/app.js')
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
        return nodejs(
                'shutit.tk.nodejs.nodejs', 0.1212353235,
                depends=['shutit.tk.setup']
        )
