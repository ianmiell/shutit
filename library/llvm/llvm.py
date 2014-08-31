
# Created from dockerfile: /space/git/llvm-docker/Dockerfile
# Maintainer:              Chris Corbyn <chris@w3style.co.uk>
from shutit_module import ShutItModule

class llvm(ShutItModule):

    def is_installed(self, shutit):
        return False

    def build(self, shutit):
        # Docker container image for building apps hosted on LLVM.
        shutit.install('subversion')
        shutit.install('python')
        shutit.install('gcc')
        shutit.install('g++')
        shutit.install('make')
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
        shutit.send('./configure')
        shutit.send('make')
        shutit.send('popd')
        return True

    def finalize(self, shutit):
        return True

    def test(self, shutit):
        return True

    def is_installed(self, shutit):
        return False

    def get_config(self, shutit):
        return True

def module():
        return llvm(
                'shutit.tk.llvm.llvm', 0.223534,
                description='LLVM',
                maintainer='ian.miell@gmail.com',
                depends=['shutit.tk.setup']
        )
