
# Created from dockerfile: /space/git/dockerfiles_repos/dockerfile-examples/rethinkdb/Dockerfile
from shutit_module import ShutItModule

class rethinkdb(ShutItModule):

	def is_installed(self, shutit):
		return False

	def build(self, shutit):
		shutit.send('echo "0.2" > /version')
		shutit.send('mkdir -p //')
		shutit.send_host_file('/rethinkdb-install.sh', 'context/rethinkdb-install.sh')
		return True

	def finalize(self, shutit):
		return True

	def test(self, shutit):
		return True

	def is_installed(self, shutit):
		return False

	def get_config(self, shutit):
		return True

def module():
		return rethinkdb(
				'shutit.tk.rethinkdb.rethinkdb', 0.124125,
				depends=['shutit.tk.setup']
		)
