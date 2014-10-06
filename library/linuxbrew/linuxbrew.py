"""ShutIt module. See http://shutit.tk
https://github.com/homebrew/linuxbrew
"""

from shutit_module import ShutItModule


class linuxbrew(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('ruby')
		shutit.install('gcc')
		shutit.install('build-essential')
		shutit.install('curl')
		shutit.install('git')
		shutit.install('m4')
		shutit.install('texinfo')
		shutit.install('libbz2-dev')
		shutit.install('libcurl4-openssl-dev')
		shutit.install('libexpat-dev')
		shutit.install('libncurses-dev')
		shutit.install('zlib1g-dev')
		shutit.send('pushd /opt')
		shutit.send('git clone https://github.com/Homebrew/linuxbrew.git ~/.linuxbrew')
		shutit.add_to_bashrc('PATH="$HOME/.linuxbrew/bin:$PATH"')
		shutit.add_to_bashrc('LD_LIBRARY_PATH="$HOME/.linuxbrew/lib:$LD_LIBRARY_PATH"')
		return True

	#def get_config(self, shutit):
	#	return True

	#def check_ready(self, shutit):
	#	return True
	
	#def start(self, shutit):
	#	return True

	#def stop(self, shutit):
	#    return True
	#def finalize(self, shutit):
	#	return True

	#def remove(self, shutit):
	#	return True

	#def test(self, shutit):
	#	return True

def module():
	return linuxbrew(
		'shutit.tk.linuxbrew.linuxbrew', 0.124125135,
		description='brew for linux',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup']
	)

