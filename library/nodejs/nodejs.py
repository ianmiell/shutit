# Created from dockerfile: /space/git/dockerfiles_repos/dockerfile-examples/nodejs/Dockerfile
from shutit_module import ShutItModule

class nodejs(ShutItModule):

	def build(self, shutit):
		shutit.install('lsb-release')
		shutit.install('software-properties-common')
		shutit.send('add-apt-repository -y ppa:chris-lea/node.js')
		shutit.send('echo "deb http://us.archive.ubuntu.com/ubuntu/ $(lsb_release -c -s) universe" >> /etc/apt/sources.list')
		shutit.send('apt-get update')
		shutit.install('nodejs')
		shutit.send('mkdir /var/www')
		shutit.send_host_file('/var/www/app.js', 'context/app.js')
		return True

def module():
	return nodejs(
		'shutit.tk.nodejs.nodejs', 0.1212353235,
		depends=['shutit.tk.setup']
	)
