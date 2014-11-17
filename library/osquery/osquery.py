"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class osquery(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('git')
		shutit.install('libqt4-dev')
		shutit.install('pkg-config')
		shutit.install('libevent-dev')
		shutit.install('sqlite')
		shutit.install('liblzma-dev')
		shutit.install('libboost1.55-all-dev')
		shutit.install('libgoogle-glog-dev')
		shutit.install('libssl-dev')
		shutit.install('python-pip')
		shutit.install('libbz2-dev')
		shutit.install('libssl-dev')
		shutit.install('python-pip')
		shutit.install('libreadline6-dev')
		shutit.install('libprocps3-dev')
		shutit.install('libsnappy-dev')
		shutit.install('libunwind8-dev')
		shutit.send('pip install jinja2')
		shutit.send('export CPATH=/usr/lib/x86_64-linux-gnu:/opt/rocksdb/include')
		shutit.send('export LIBRARY_PATH=/usr/local/lib')
		shutit.send('pushd /opt')
		shutit.send('git clone https://github.com/facebook/osquery.git')
		shutit.send('pushd /opt/osquery')
		shutit.send('git submodule init')
		shutit.send('git submodule update')
		shutit.send('make')
		shutit.send('popd')
		shutit.send('popd')
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
	return osquery(
		'shutit.tk.osquery.osquery', 0.11352451,
		description='Facebook\'s OSQuery sql tool',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.rocksdb.rocksdb','shutit.tk.thrift.thrift','shutit.tk.automake.automake','shutit.tk.bison.bison','shutit.tk.libtool.libtool','shutit.tk.flex.flex']
	)

