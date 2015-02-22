"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class osquery(ShutItModule):

	def build(self, shutit):
		shutit.install('git libqt4-dev pkg-config libevent-dev sqlite liblzma-dev libboost1.55-all-dev libgoogle-glog-dev libssl-dev python-pip libbz2-dev libssl-dev python-pip libreadline6-dev libprocps3-dev libsnappy-dev libunwind8-dev flex bison libtool automake cmake clang uuid-dev libudev-dev librpm-dev libblkid-dev libapt-pkg-dev libdpkg-dev')
		shutit.send('pip install jinja2')
		shutit.send('export CPATH=/usr/lib/x86_64-linux-gnu:/opt/rocksdb/include')
		shutit.send('export LIBRARY_PATH=/usr/local/lib')
		shutit.send('cd /opt')
		shutit.send('git clone https://github.com/facebook/osquery.git')
		shutit.send('cd /opt/osquery')
		shutit.send('git submodule init')
		shutit.send('git submodule update')
		shutit.send('make')
		shutit.send('make install')
		return True

def module():
	return osquery(
		'shutit.tk.osquery.osquery', 0.11352451,
		description='Facebook\'s OSQuery sql tool',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.rocksdb.rocksdb','shutit.tk.thrift.thrift']
	)

