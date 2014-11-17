"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class zip(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		#http://www.info-zip.org/Zip.html 
		shutit.install('tar')
		shutit.install('gcc')
		shutit.install('m4')
		shutit.send('mkdir -p /opt/zip')
		shutit.send_host_file('/opt/zip/unzip60.tar.gz','context/unzip60.tar.gz')
		shutit.send('pushd /opt/zip')
		shutit.send('gunzip unzip60.tar.gz')
		shutit.send('tar -xf unzip60.tar')
		shutit.send('pushd unzip60')
		shutit.send('make -f unix/Makefile IZ_BZIP2=/opt/bzip2/bzip2-1.0.6 IZ_ZLIB=../../zlib/zlib-1.2.5 generic')
		shutit.send('make -f unix/Makefile install')
		shutit.send('rm -rf /opt/zip')
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
		'shutit.tk.zip.zip', 0.0111332513136,
		description='',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.zlib.zlib']
	)

