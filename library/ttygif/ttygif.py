"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class ttygif(ShutItModule):

	def build(self, shutit):
		shutit.install('git')
		shutit.install('imagemagick')
		shutit.install('ttyrec')
		shutit.install('build-essential')
		shutit.send('pushd /opt')
		shutit.send('git clone https://github.com/icholy/ttygif.git')
		shutit.send('pushd /opt/ttygif')
		shutit.send('make')
		shutit.send('mv ttygif /usr/bin/')
		shutit.send('mv concat.sh /usr/bin/')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/ttygif')
		return True

def module():
	return ttygif(
		'shutit.tk.ttygif.ttygif', 0.35136139681,
		description='Turn terminal sessions into gifs',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup','shutit.tk.vnc.vnc']
	)

