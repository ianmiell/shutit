
# Created from dockerfile: /space/git/dockerfiles_repos/dockerfile-examples/couchdb/Dockerfile
from shutit_module import ShutItModule

class couchdb(ShutItModule):

        def is_installed(self,shutit):
                return False

        def build(self,shutit):
		shutit.send('echo "deb http://us.archive.ubuntu.com/ubuntu/ precise universe" >> /etc/apt/sources.list')
		shutit.send('apt-get -y update')
		shutit.send('apt-get install -y g++')
		shutit.send('apt-get install -y erlang-dev erlang-manpages erlang-base-hipe erlang-eunit erlang-nox erlang-xmerl erlang-inets')
		shutit.send('apt-get install -y libmozjs185-dev libicu-dev libcurl4-gnutls-dev libtool wget')
		shutit.send('cd /tmp ; wget http://www.bizdirusa.com/mirrors/apache/couchdb/source/1.3.1/apache-couchdb-1.3.1.tar.gz')
		shutit.send('cd /tmp && tar xvzf apache-couchdb-1.3.1.tar.gz')
		shutit.send('apt-get install -y make')
		shutit.send('cd /tmp/apache-couchdb-* ; ./configure && make install')
		shutit.send('printf "[httpd]\nport = 8101\nbind_address = 0.0.0.0" > /usr/local/etc/couchdb/local.d/docker.ini')
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
        return couchdb(
                'shutit.tk.couchdb.couchdb', 0.123124,
                depends=['shutit.tk.setup']
        )
