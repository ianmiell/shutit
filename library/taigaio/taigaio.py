"""ShutIt module. See http://shutit.tk
"""
from shutit_module import ShutItModule

class taigaio(ShutItModule):

	def is_installed(self, shutit):
		return False

	def build(self, shutit):
		shutit.install('adduser')
		shutit.install('git')
		shutit.install('sudo')
		shutit.send('adduser --gecos "" --disabled-password taiga')
		shutit.send('echo taiga:taiga | chpasswd')
		shutit.send('adduser taiga sudo')
		shutit.login('taiga')
		shutit.send('git clone https://github.com/taigaio/taiga-scripts.git')
		shutit.send('pushd taiga-scripts')
		shutit.multisend('bash setup-server.sh',{'Scheme':'http','Hostname':'8000','assword for':'taiga'})
		shutit.send('sudo -u postgres createuser --superuser $USER')
		shutit.send('sudo -u postgres createdb $USER')
		shutit.send('python manage.py migrate --noinput')
		shutit.send('python manage.py loaddata initial_user')
		shutit.send('python manage.py loaddata initial_project_templates')
		shutit.send('python manage.py loaddata initial_role')
		shutit.send('logout')
		return True

	#def get_config(self, shutit):
	#    return True

	#def check_ready(self, shutit):
	#    return True
	
	#def start(self, shutit):
	#    return True

	#def stop(self, shutit):
	#    return True
	#def finalize(self, shutit):
	#    return True

	#def remove(self, shutit):
	#    return True

	def test(self, shutit):
		shutit.send('python manage.py runserver 0.0.0.0:8000 > /dev/null 2>&1 &')
		shutit.send('deactivate')
		shutit.send('curl localhost:8000')
		shutit.send('kill %1')
		return True

def module():
	return taigaio(
		'shutit.tk.taigaio.taigaio', 0.313652837652,
		description='Taigaio install',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup','shutit.tk.postgres.postgres']
	)

