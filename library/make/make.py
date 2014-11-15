"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class make(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('wget')
		shutit.install('gcc')
		shutit.send('pushd /opt')
		shutit.send('mkdir -p make')
		shutit.send('pushd /opt/make')
		shutit.send('wget http://ftp.gnu.org/gnu/make/make-4.1.tar.gz')
		shutit.send('gunzip make-4.1.tar.gz')
		if shutit.file_exists('/root/tar'):
			shutit.send('/root/tar -xf make-4.1.tar')
		else:
			shutit.send('tar -xf make-4.1.tar')
		shutit.send('pushd make-4.1')
		shutit.send('./configure')
		shutit.send('sh build.sh') # to build make without make
		#shutit.send('./make install')
		shutit.send('mv make /usr/bin')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/make')
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
	return make(
		'shutit.tk.make.make', 0.010011,
		description='',
		maintainer='',
		depends=['shutit.tk.setup']
	)

