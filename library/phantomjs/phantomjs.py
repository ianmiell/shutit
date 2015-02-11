from shutit_module import ShutItModule

class phantomjs(ShutItModule):

	def build(self, shutit):
		shutit.send('pushd /opt')
		shutit.install('tar') # required for centos image
		shutit.install('curl')
		shutit.install('bzip2')
		# TODO: latest version of pj?
		shutit.send('curl --insecure https://phantomjs.googlecode.com/files/phantomjs-1.9.0-linux-x86_64.tar.bz2 > phantomjs-1.9.0-linux-x86_64.tar.bz2')
		shutit.send('bunzip2 phantomjs-1.9.0-linux-x86_64.tar.bz2')
		shutit.send('tar -xvf phantomjs-1.9.0-linux-x86_64.tar')
		shutit.send('ln -s phantomjs-1.9.0-linux-x86_64 phantomjs')
		shutit.send('rm phantomjs-*.tar')
		shutit.send('popd')
		return True

	def remove(self, shutit):
		shutit.send('rm -rf /opt/phantomjs')
		return True

def module():
	return phantomjs(
		'shutit.tk.phantomjs.phantomjs', 0.319,
		description='see http://phantomjs.org/',
		depends=['shutit.tk.setup']
	)

