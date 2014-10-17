"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class binspector(ShutItModule):

	def is_installed(self, shutit):
		return False

	def build(self, shutit):
		shutit.install('curl')
		shutit.install('git')
		shutit.install('python2.7-minimal')
		shutit.install('libc6')
		shutit.install('mlocate')
		shutit.send('pushd /opt')
		shutit.send('git clone https://github.com/binspector/binspector.git')
		shutit.send('popd')
		shutit.send('pushd /opt/binspector')
		shutit.send('updatedb')
		shutit.pause_point('export CPATH=/usr/include/c++/4.8')
		shutit.send('./configure.sh')
		shutit.send('./build.sh')
		shutit.send('./smoke_test.sh')
		shutit.send('popd')
		return True

def module():
	return binspector(
		'shutit.tk.binspector.binspector', 0.3132235246,
		description='binary inspector',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup']
	)

