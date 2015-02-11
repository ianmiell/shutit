"""ShutIt module. See http://shutit.tk
"""
from shutit_module import ShutItModule

class taigaio(ShutItModule):

	def build(self, shutit):
		shutit.install('adduser')
		shutit.install('git')
		shutit.install('sudo')
		shutit.install('python3-pip')
		shutit.install('weblint-perl') #for bower
		shutit.run_script('''
			echo "LANG=en_US.UTF-8" > /etc/default/locale
			echo "LC_MESSAGES=POSIX" >> /etc/default/locale
			echo "LANGUAGE=en" >> /etc/default/locale
			locale-gen en_US.UTF-8
		''')
		shutit.send('adduser --gecos "" --disabled-password taiga')
		shutit.send('echo taiga:taiga | chpasswd')
		shutit.send('adduser taiga sudo')
		shutit.login(user='taiga')
		shutit.send('cd /home/taiga')
		shutit.send('git clone https://github.com/taigaio/taiga-scripts.git')
		shutit.send('pushd taiga-scripts')
		shutit.multisend('bash setup-server.sh', {
			'Scheme':'http',
			'Hostname':'localhost:8000',
			'assword for':'taiga',
			'anonymously report usage statistics to improve the tool over time':'n'
		})
		shutit.logout()
		shutit.run_script('''
			cat >/root/start_taiga.sh <<EOF
			/usr/local/bin/circusd --daemon /home/taiga/conf/circus.ini
			service nginx start
			EOF
			cat >/root/stop_taiga.sh <<EOF
			circusctl stop
			circusctl quit
			service nginx stop
			EOF
		'''
		)
		shutit.send('chmod +x /root/{start,stop}_taiga.sh')
		return True

	def test(self, shutit):
		shutit.send('/root/start_taiga.sh')
		# Newline required to make the expect work
		shutit.send('''curl -w '\n' localhost:8000''')
		shutit.send('/root/stop_taiga.sh')
		return True

def module():
	return taigaio(
		'shutit.tk.taigaio.taigaio', 0.33652837652,
		description='Taigaio install',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup','shutit.tk.postgres.postgres']
	)

