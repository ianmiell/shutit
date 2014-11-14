"""ShutIt module. See http://shutit.tk
In source, line 16 should be blank, within the build def. This doesn't matter except for test builds, so can be removed once in use.
"""

from shutit_module import ShutItModule


class bzip2(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.send('mkdir -p /opt/bzip2')
		shutit.send('pushd /opt/bzip2')
		shutit.send_host_file('/opt/bzip2/bzip2.tar','context/bzip2-1.0.6.tar')
		shutit.send('tar -xf bzip2.tar')
		shutit.send('pushd bzip2-1.0.6')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf bzip2')
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
	return bzip2(
		'shutit.tk.bzip2.bzip2', 0.0101,
		description='',
		maintainer='',
		depends=['shutit.tk.setup','shutit.tk.make.make']
	)

