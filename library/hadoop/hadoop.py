"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class hadoop(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('ssh')
		shutit.install('rsync')
		shutit.install('wget')
		shutit.send('pushd /opt')
		# TODO: configure version number
		shutit.send('wget http://mirror.gopotato.co.uk/apache/hadoop/common/stable/hadoop-2.5.1.tar.gz')
		shutit.send('tar -zxvf hadoop*tar.gz')
		shutit.pause_point('install hadoop')
#"Unpack the downloaded Hadoop distribution. In the distribution, edit the file etc/hadoop/hadoop-env.sh to define some parameters as follows:
#
#  # set to the root of your Java installation
#  export JAVA_HOME=/usr/java/latest
#
#  # Assuming your installation directory is /usr/local/hadoop
#  export HADOOP_PREFIX=/usr/local/hadoop
#
#Try the following command:
#
#  $ bin/hadoop
#
#This will display the usage documentation for the hadoop script.
#
#Now you are ready to start your Hadoop cluster in one of the three supported modes:"
		shutit.send('popd /opt')
		return True

	#def get_config(self, shutit):
	#	return True

	#def check_ready(self, shutit):
	#	return True
	
	#def start(self, shutit):
	#	return True

	#def stop(self, shutit):
	#    return True
	#def finalize(self, shutit):
	#	return True

	#def remove(self, shutit):
	#	return True

	#def test(self, shutit):
	#	return True

def module():
	return hadoop(
		'shutit.tk.hadoop.hadoop', 0.16436434,
		description='hadoop',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup','shutit.tk.java_oracle_6.java_oracle_6_jdk']
	)

