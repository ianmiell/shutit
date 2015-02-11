"""ShutIt module. See http://shutit.tk
https://github.com/homebrew/linuxbrew
"""

from shutit_module import ShutItModule


class linuxbrew(ShutItModule):

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
		shutit.send('''echo 'export PATH="$HOME/.linuxbrew/bin:$PATH"' >> ~/.bashrc''')
		shutit.send('''echo 'export LD_LIBRARY_PATH="$HOME/.linuxbrew/lib:$LD_LIBRARY_PATH"' >> ~/.bashrc''')
		return True

def module():
	return linuxbrew(
		'shutit.tk.linuxbrew.linuxbrew', 0.124125135,
		description='brew for linux',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup']
	)

