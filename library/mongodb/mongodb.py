
from shutit_module import ShutItModule

class mongodb(ShutItModule):

        def is_installed(self,shutit):
                return False

        def build(self,shutit):

		shutit.send('apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10')
		shutit.send('echo "deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen" | tee -a /etc/apt/sources.list.d/10gen.list')
		shutit.send('apt-get update')
		shutit.send('apt-get -y install apt-utils')
		shutit.send('apt-get -y install mongodb-10gen')
                return True

	def finalize(self,shutit):

		return True


def module():
        return mongodb(
                'shutit.tk.mongodb.mongodb', 0.13124,
                depends=['shutit.tk.setup']
        )
