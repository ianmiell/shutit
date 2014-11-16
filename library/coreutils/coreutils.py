"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class coreutils(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.send('pushd /opt')
		shutit.send('git clone git://git.sv.gnu.org/coreutils')
		shutit.send('pushd /opt/coreutils')
		shutit.send('./bootstrap')
		shutit.send('FORCE_UNSAFE_CONFIGURE=1 ./configure --prefix=/usr')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/coreutils')
		return True

	#def get_config(self, shutit):
	#	return True

	#def check_ready(self, shutit):
	#	return True
	
	#def start(self, shutit):
	#	return True

	#def stop(self, shutit):
	#	return True

	#def finalize(self, shutit):
	#	return True

	#def remove(self, shutit):
	#	return True

	#def test(self, shutit):
	#	return True

def module():
	return coreutils(
		'shutit.tk.coreutils.coreutils', 0.021251825152,
		description='',
		maintainer='',
		depends=['shutit.tk.git.git','shutit.tk.bison.bison','shutit.tk.gperf.gperf','shutit.tk.patch.patch','shutit.tk.rsync.rsync']
	)

