
# Created from dockerfile: /space/git/dockerfiles_repos/Dockerfiles/influxdb/Dockerfile
from shutit_module import ShutItModule

class influxdb(ShutItModule):

        def is_installed(self,shutit):
                return False

        def build(self,shutit):
		shutit.install('wget')
		shutit.send('mkdir -p /')
		shutit.send('wget -O /influxdb_latest_amd64.deb http://s3.amazonaws.com/influxdb/influxdb_latest_amd64.deb')
		shutit.send('dpkg -i /influxdb_latest_amd64.deb')
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
        return influxdb(
                'shutit.tk.influxdb.influxdb', 0.1212353,
                depends=['shutit.tk.setup']
        )
