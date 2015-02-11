# Created from dockerfile: https://registry.hub.docker.com/u/flurdy/oracle-java6/dockerfile/raw
# Maintainer:              flurdy
from shutit_module import ShutItModule

class java_oracle_6_jdk(ShutItModule):

	def build(self, shutit):
		# accept-java-license
		shutit.send('echo /usr/bin/debconf shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections')
		shutit.install('software-properties-common')
		shutit.send('add-apt-repository ppa:webupd8team/java',expect='ENTER')
		shutit.send('')
		shutit.send('apt-get autoremove -yq')
		shutit.send('rm -rf /var/lib/apt/lists/*')
		shutit.send('apt-get update')
		shutit.install('oracle-java6-installer')
		shutit.install('oracle-java6-set-default')
		shutit.add_to_bashrc('export JAVA_HOME=/usr')
		return True

	def finalize(self, shutit):
		shutit.send('apt-get autoremove -yq')
		shutit.send('apt-get clean -yq')
		return True

def module():
	return java_oracle_6_jdk(
		'shutit.tk.java_oracle_6.java_oracle_6_jdk', 0.1124634634,
		description='Oracle Java 6',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup']
	)
