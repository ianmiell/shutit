
# Maintainer:              Joao Paulo Dubas 'joao.dubas@gmail.com'
from shutit_module import ShutItModule

class arangodb(ShutItModule):

        def is_installed(self,shutit):
                return False

        def build(self,shutit):
		shutit.install('wget')
		shutit.send('export ARANGO_URL=http://www.arangodb.org/repositories/arangodb2/xUbuntu_14.04')
		shutit.send('echo "deb $ARANGO_URL/ /" >> /etc/apt/sources.list.d/arangodb.list && wget $ARANGO_URL/Release.key && apt-key add - < Release.key && rm Release.key')
		shutit.send('apt-get -y -qq --force-yes update')
		shutit.send('apt-get -y -qq --force-yes install arangodb=2.1.2')
		shutit.send('rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*')
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
        return arangodb(
                'shutit.tk.arangodb.arangodb', 0.398214,
		description='arangodb',
                depends=['shutit.tk.setup']
        )
