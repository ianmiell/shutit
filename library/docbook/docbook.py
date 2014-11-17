"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class docbook(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.send('mkdir -p /opt/docbook')
		shutit.send('pushd /opt/docbook')
		shutit.send('wget http://www.docbook.org/xml/4.5/docbook-xml-4.5.zip')
		shutit.send('unzip docbook-xml-4.5.zip')
		shutit.send('install -v -m755 -d /usr/share/xml/docbook/xsl-stylesheets-1.78.1')
		shutit.send('cp -v -R VERSION common eclipse epub extensions fo highlighting html htmlhelp images javahelp lib manpages params profiling roundtrip slides template tests tools webhelp website xhtml xhtml-1_1 /usr/share/xml/docbook/xsl-stylesheets-1.78.1')
		shutit.send('ln -s VERSION /usr/share/xml/docbook/xsl-stylesheets-1.78.1/VERSION.xsl')
		shutit.send('install -v -m644 -D README /usr/share/doc/docbook-xsl-1.78.1/README.txt')
		shutit.send('install -v -m644    RELEASE-NOTES* NEWS* /usr/share/doc/docbook-xsl-1.78.1')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/docbook')
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
	return docbook(
		'shutit.tk.docbook.docbook', 0.01124918274,
		description='',
		maintainer='',
		depends=['shutit.tk.zip.zip']
	)

