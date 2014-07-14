
# Created from dockerfile: /space/git/dockerfiles_repos/Dockerfiles/crosscompile/Dockerfile
from shutit_module import ShutItModule

class crosscompile(ShutItModule):

        def is_installed(self,shutit):
                return False

        def build(self,shutit):
		shutit.send('echo "deb http://archive.ubuntu.com/ubuntu precise main universe" > /etc/apt/sources.list')
		shutit.send('apt-get update')
		shutit.send('apt-get upgrade -y')
		shutit.install('mercurial git-core')
		shutit.send('hg clone https://code.google.com/p/go')
		shutit.send('pushd /go')
		shutit.send('hg update go1.1.2')
		shutit.send('export GOROOT=/go')
		shutit.send('export GOBIN=/go/bin')
		shutit.install('gcc')
		shutit.install('g++')
		shutit.install('make build-essential')
		shutit.send('pushd /go/src')
		shutit.send('./all.bash')
		shutit.send('export PATH=$PATH:/go/bin')
		shutit.send('/bin/bash -c "git clone git://github.com/davecheney/golang-crosscompile.git && source golang-crosscompile/crosscompile.bash && go-crosscompile-build-all"')
		shutit.send('popd')
		shutit.send('popd')
                return True

	def finalize(self,shutit):
		return True

	def test(self,shutit):
		return True

	def is_installed(self,shutit):
		return False

	def get_config(self,shutit):
		return True

def module():
        return crosscompile(
                'shutit.tk.crosscompile.crosscompile', 0.1241325,
                depends=['shutit.tk.setup']
        )
