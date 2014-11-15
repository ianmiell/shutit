"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class gperf(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('wget')
		shutit.install('tar')
		shutit.install('g++')
		shutit.send('mkdir -p /opt/gperf')
		shutit.send('pushd /opt/gperf')
		shutit.send('wget http://ftp.gnu.org/pub/gnu/gperf/gperf-3.0.4.tar.gz')
		shutit.send('gunzip gperf-3.0.4.tar.gz')
		shutit.send('tar -xf gperf-3.0.4.tar')
		shutit.send('pushd gperf-3.0.4')
		shutit.send('./configure --prefix=/usr')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('rm -rf /opt/gperf')
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
	return gperf(
		'shutit.tk.gperf.gperf', 0.01121251,
		description='',
		maintainer='',
		depends=['shutit.tk.make.make']
	)

