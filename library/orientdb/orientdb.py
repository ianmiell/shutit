
# Created from dockerfile: /tmp/a/Dockerfile
# Maintainer:              Joao Paulo Dubas &quot;joao.dubas@gmail.com&quot;
from shutit_module import ShutItModule

class orientdb(ShutItModule):

        def is_installed(self,shutit):
                return False

        def build(self,shutit):
		shutit.send('apt-get -y -qq update &amp;&amp; apt-get -y -qq install wget')
		shutit.send('export ROOT=/opt/downloads')
		shutit.send('export ORIENT_URL=http://www.orientdb.org/portal/function/portal/download/unknown@unknown.com')
		shutit.send('export ORIENT_VERSION=orientdb-community-1.7.4')
		shutit.send('mkdir ${ROOT} &amp;&amp; cd ${ROOT} &amp;&amp; wget ${ORIENT_URL}/-/-/-/-/-/${ORIENT_VERSION}.tar.gz/false/false/linux &amp;&amp; tar -xzf linux &amp;&amp; ln -s ${ROOT}/${ORIENT_VERSION} ${ROOT}/orientdb')
		shutit.send('apt-get -y -qq --force-yes clean &amp;&amp; rm -rf /opt/downloads/linux /var/lib/apt/lists/* /tmp/* /var/tmp/*')
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
        return orientdb(
                'shutit.tk.orientdb.orientdb', 782914092.00,
                depends=['shutit.tk.setup']
        )
