
# Created from dockerfile: /space/git/llvm-docker/Dockerfile
# Maintainer:              Chris Corbyn <chris@w3style.co.uk>
from shutit_module import ShutItModule

class llvm(ShutItModule):

	def is_installed(self, shutit):
		return False

	def build(self, shutit):
		# Module for building apps hosted on LLVM.
		shutit.install('subversion')
		shutit.install('python')
		shutit.install('gcc')
		shutit.install('g++')
		shutit.send('pushd /opt')
		shutit.send('svn co http://llvm.org/svn/llvm-project/llvm/trunk llvm')
		shutit.send('pushd llvm/tools')
		shutit.send('svn co http://llvm.org/svn/llvm-project/cfe/trunk clang')
		shutit.send('popd')
		shutit.send('pushd llvm/tools/clang/tools')
		shutit.send('svn co http://llvm.org/svn/llvm-project/clang-tools-extra/trunk extra')
		shutit.send('popd')
		shutit.send('pushd llvm/projects')
		shutit.send('svn co http://llvm.org/svn/llvm-project/compiler-rt/trunk compiler-rt')
		shutit.send('popd')
		shutit.send('pushd llvm')
		shutit.send('./configure --prefix=/usr')
		# Echo required to force newline
		shutit.send('make && echo',timeout=99999)
		# Required for install
		shutit.install('groff')
		shutit.send('make install',timeout=99999)
		shutit.send('popd')
		shutit.add_to_bashrc('export LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/lib/x86_64-linux-gnu')
		shutit.add_to_bashrc('export CPATH=${CPATH}:/usr/include/c++/4.8:/usr/include/x86_64-linux-gnu/c++/4.8')
		return True

	def finalize(self, shutit):
		# Remove llvm stuff
		shutit.send('rm -rf /opt/llvm')
		return True

	def test(self, shutit):
		return True

	def is_installed(self, shutit):
		return shutit.file_exists('/usr/local/bin/pp-trace')

	def get_config(self, shutit):
		return True

def module():
	return llvm(
		'shutit.tk.llvm.llvm', 0.223534,
		description='LLVM and clang',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.make.make']
	)
