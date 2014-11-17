"""ShutIt module. See http://shutit.tk
In source, line 16 should be blank, within the build def. This doesn't matter except for test builds, so can be removed once in use.
"""

from shutit_module import ShutItModule


class docbookxsl(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.send('mkdir -p /opt/docbookxsl')
		shutit.send('pushd /opt/docbookxsl')
		shutit.send('wget http://downloads.sourceforge.net/docbook/docbook-xsl-1.78.1.tar.bz2')
		shutit.send('bunzip2 docbook-xsl-1.78.1.tar.bz2')
		shutit.send('tar -xf docbook-xsl-1.78.1.tar')
		shutit.send('pushd docbook-xsl-1.78.1')
		shutit.send('./configure --prefix=/usr')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/docbookxsl')
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
	return docbookxsl(
		'shutit.tk.docbookxsl.docbookxsl', 0.011318728,
		description='',
		maintainer='',
		depends=['shutit.tk.libxslt.libxslt']
	)

