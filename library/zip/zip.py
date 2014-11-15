"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class zip(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
#http://www.info-zip.org/Zip.html 
# see context for bzip
		shutit.install('tar')
		shutit.install('gcc')
		shutit.send('mkdir -p /opt/zip')
		shutit.send_host_file('/opt/zip/unzip610b.tar.bz2','context/unzip610b.tar.bz2')
		shutit.send('pushd /opt/zip')
		shutit.send('bunzip2 unzip610b.tar.bz2')
		shutit.send('tar -xf unzip610b.tar')
		shutit.pause_point('zip next step make -f unix/Makefile IZ_BZIP2=/opt/bzip2/bzip2-1.0.6 IZ_ZLIB=../../zlib/zlib-1.2.5 generic')
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
	return zip(
		'shutit.tk.zip.zip', 0.012513136,
		description='',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.bzip2.bzip2']
	)

