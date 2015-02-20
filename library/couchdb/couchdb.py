
# Created from dockerfile: /space/git/dockerfiles_repos/dockerfile-examples/couchdb/Dockerfile
from shutit_module import ShutItModule

class couchdb(ShutItModule):

	def build(self, shutit):
		shutit.send('echo "deb http://us.archive.ubuntu.com/ubuntu/ precise universe" >> /etc/apt/sources.list')
		shutit.send('apt-get -y update')
		shutit.send('apt-get install -y g++')
		shutit.send('apt-get install -y erlang-dev erlang-manpages erlang-base-hipe erlang-eunit erlang-nox erlang-xmerl erlang-inets')
		shutit.send('apt-get install -y libmozjs185-dev libicu-dev libcurl4-gnutls-dev libtool wget')
		shutit.send('cd /tmp')
		shutit.get_url('apache-couchdb-' + shutit.cfg[self.module_id]['version'] + '.tar.gz',['http://www.apache.org/dist/couchdb/source/' + shutit.cfg[self.module_id]['version']])
		shutit.send('tar -zxf apache-couchdb-' + shutit.cfg[self.module_id]['version'] + '.tar.gz')
		shutit.send('cd /tmp && tar xvzf apache-couchdb-' + shutit.cfg[self.module_id]['version'] + '.tar.gz')
		shutit.send('apt-get install -y make')
		shutit.send('cd /tmp/apache-couchdb-*')
		shutit.send('./configure --prefix=/usr')
		shutit.send('make install')
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id,'version','1.6.0')
		return True

	def finalize(self,shutit):
		shutit.send('rm -rf /tmp/apache-couchdb*')
		return True

def module():
		return couchdb(
				'shutit.tk.couchdb.couchdb', 0.123124,
				depends=['shutit.tk.setup']
		)
