"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class git(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('wget')
		shutit.install('gcc')
		shutit.install('libssl-dev')
		shutit.install('libcurl4-gnutls-dev')
		shutit.install('libexpat1-dev')
		shutit.install('asciidoc')
		shutit.install('docbook2x')
		shutit.send('mkdir -p /opt/git')
		shutit.send('pushd /opt/git')
		shutit.send('wget https://github.com/git/git/archive/master.zip')
		shutit.send('unzip master.zip')
		shutit.send('pushd git-master')
		shutit.send('make prefix=/usr all doc info')
		shutit.send('make install prefix=/usr')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/git')
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
	return git(
		'shutit.tk.git.git', 0.021,
		description='Git built from source',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.gettext.gettext','shutit.tk.zip.zip','shutit.tk.tcl.tcl']
	)

