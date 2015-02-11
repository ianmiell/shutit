"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class rocksdb(ShutItModule):

	def build(self, shutit):
		shutit.install('git')
		shutit.install('make')
		shutit.install('g++')
		shutit.install('libgflags-dev')
		shutit.install('libbz2-dev')
		shutit.send('pushd /opt')
		shutit.send('git clone https://github.com/facebook/rocksdb.git')
		shutit.send('pushd /opt/rocksdb')
		shutit.send('make')
		shutit.send('make all')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		return True

def module():
	return rocksdb(
		'shutit.tk.rocksdb.rocksdb', 0.1103251735,
		description='Facebook\'s rocksdb',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup']
	)

