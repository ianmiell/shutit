"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class hadoop(ShutItModule):

	def build(self, shutit):
		shutit.install('ssh')
		shutit.install('rsync')
		shutit.install('wget')
		shutit.send('pushd /opt')
		shutit.send('wget http://mirror.gopotato.co.uk/apache/hadoop/common/stable/hadoop-' + shutit.cfg[self.module_id]['version'] + '.tar.gz')
		shutit.send('tar -zxf hadoop*tar.gz')
		shutit.send('mkdir input')
		shutit.add_line_to_file('export HADOOP_PREFIX=/opt/hadoop-' + shutit.cfg[self.module_id]['version'],'/opt/hadoop-' + shutit.cfg[self.module_id]['version'] + '/hadoop_env.sh')
		shutit.send('pushd hadoop-' + shutit.cfg[self.module_id]['version'] + '')
		# TODO
		shutit.send('popd')
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id,'version','2.5.1')
		return True

def module():
	return hadoop(
		'shutit.tk.hadoop.hadoop', 0.16436434,
		description='hadoop',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup','shutit.tk.java_oracle_6.java_oracle_6_jdk','shutit.tk.ssh_key.ssh_key']
	)

