"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class binspector(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('curl')
		shutit.install('git')
		shutit.send('git clone https://github.com/binspector/binspector.git')
		shutit.send('./binspector/smoke_test.sh')
		return True

def module():
	return binspector(
		'shutit.tk.binspector.binspector', 0.132235246,
		description='binary inspector',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup','shutit.tk.llvm.llvm']
	)

