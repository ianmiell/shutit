
# Created from dockerfile: https://raw.githubusercontent.com/tomparys/docker-skype-pulseaudio/master/Dockerfile
from shutit_module import ShutItModule

class skype_pulseaudio(ShutItModule):
	def build(self, shutit):
		shutit.send('export DEBIAN_FRONTEND=noninteractive')
		shutit.send('dpkg --add-architecture i386')
		shutit.send('apt-get update')
		shutit.install('libpulse0:i386 pulseaudio:i386')
		shutit.install('openssh-server wget')
		shutit.send('wget http://download.skype.com/linux/skype-debian_4.3.0.37-1_i386.deb -O /usr/src/skype.deb')
		shutit.send('dpkg -i /usr/src/skype.deb || true')
		shutit.send('apt-get install -fy # Automatically detect and install dependencies')
		shutit.send('useradd -m -d /home/docker docker')
		shutit.send('echo "docker:docker" | chpasswd')
		shutit.send('mkdir -p /var/run/sshd')
		shutit.send('echo X11Forwarding yes >> /etc/ssh/ssh_config')
		shutit.send('mkdir /home/docker/.ssh')
		shutit.send('chown -R docker:docker /home/docker')
		shutit.send('chown -R docker:docker /home/docker/.ssh')
		shutit.send('localedef -v -c -i en_US -f UTF-8 en_US.UTF-8 || true')
		shutit.send('echo "Europe/Prague" > /etc/timezone')
		shutit.send('''echo 'export PULSE_SERVER="tcp:localhost:64713"' >> /usr/local/bin/skype-pulseaudio''')
		shutit.send('''echo 'PULSE_LATENCY_MSEC=60 skype' >> /usr/local/bin/skype-pulseaudio''')
		shutit.send('chmod 755 /usr/local/bin/skype-pulseaudio')
		return True


def module():
		return skype_pulseaudio(
				'shutit.tk.skype_pulseaudio.skype_pulseaudio', 0.681273871,
				depends=['shutit.tk.setup']
		)
