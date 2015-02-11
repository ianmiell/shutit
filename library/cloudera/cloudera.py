
# Created from dockerfile: https://gist.githubusercontent.com/iMelnik/dffadd951f8c73402254/raw/02acc8ff50e9b180f97b84cd64f051acc9e09103/Dockerfile
# Maintainer:              Sergey Melnik "smelnik@onetwotrip.com"
from shutit_module import ShutItModule

class cloudera(ShutItModule):

	def build(self, shutit):
		shutit.install('curl')
		# add CDH repo
		shutit.send('curl http://archive.cloudera.com/cdh5/ubuntu/precise/amd64/cdh/archive.key | apt-key add -')
		shutit.send('curl http://archive.cloudera.com/cdh5/ubuntu/precise/amd64/cdh/cloudera.list > /etc/apt/sources.list.d/cloudera.list')
		# add CM repo
		shutit.send('curl http://archive.cloudera.com/cm5/ubuntu/precise/amd64/cm/archive.key | apt-key add -')
		shutit.send('curl http://archive.cloudera.com/cm5/ubuntu/precise/amd64/cm/cloudera.list > /etc/apt/sources.list.d/cloudera-manager.list')
		shutit.send('apt-get update')
		shutit.install('oracle-j2sdk1.7',force=True)
		shutit.add_to_bashrc('export JAVA_HOME=/usr/lib/jvm/java-7-oracle-cloudera')
		shutit.add_to_bashrc('export PATH=$JAVA_HOME/bin:$PATH')
		shutit.install('cloudera-manager-daemons cloudera-manager-server',force=True)
		return True

def module():
	return cloudera(
		'shutit.tk.cloudera.cloudera', 0.625471642,
		description='',
		depends=['shutit.tk.setup']
	)
