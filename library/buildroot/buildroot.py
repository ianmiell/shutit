"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class buildroot(ShutItModule):


	def is_installed(self, shutit):
		return shutit.file_exists('/root/shutit_build/module_record/' + self.module_id + '/built')

	def build(self, shutit):
		shutit.install('wget')
		shutit.install('build-essential')
		shutit.install('ncurses-dev')
		shutit.send('mkdir -p /opt/buildroot')
		shutit.send('pushd /opt/buildroot')
		shutit.send('wget http://buildroot.uclibc.org/downloads/buildroot-2014.08.tar.gz')
		shutit.send('gunzip buildroot-2014.08.tar.gz')
		shutit.send('tar -xvf buildroot-2014.08.tar')
		shutit.send('unset CC')
		shutit.send('unset CXX')
		return True

	#def get_config(self, shutit):
	#	shutit.get_config(self.module_id,'item','default')
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
	return buildroot(
		'shutit.tk.buildroot.buildroot', 0.01251352,
		description='http://www.uclibc.org/toolchains.html',
		maintainer='',
		depends=['shutit.tk.setup']
	)

