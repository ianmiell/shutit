"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class docbookxsl(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.send('mkdir -p /opt/docbookxsl')
		shutit.send('pushd /opt/docbookxsl')
		shutit.send('wget http://downloads.sourceforge.net/docbook/docbook-xsl-' + shutit.cfg[self.module_id]['version'] + '.tar.bz2')
		shutit.send('bunzip2 docbook-xsl-' + shutit.cfg[self.module_id]['version'] + '.tar.bz2')
		shutit.send('tar -xf docbook-xsl-' + shutit.cfg[self.module_id]['version'] + '.tar')
		shutit.send('pushd docbook-xsl-1')
		# www.linuxfromscratch.org/blfs/view/svn/pst/docbook-xsl.html for installation TODO
		shutit.send('./configure --prefix=/usr')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/docbookxsl')
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id,'version','1.78.1')
		return True

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

