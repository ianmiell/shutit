
# Created from dockerfile: /space/git/dockerfiles_repos/Dockerfiles/crosscompile/Dockerfile
from shutit_module import ShutItModule

class crosscompile(ShutItModule):

        def is_installed(self,shutit):
                return False

        def build(self,shutit):
		shutit.send('echo "deb http://archive.ubuntu.com/ubuntu precise main universe" > /etc/apt/sources.list')
		shutit.send('apt-get update')
		shutit.send('apt-get upgrade -y')
		shutit.send('apt-get install -y mercurial git-core')
		shutit.send('hg clone https://code.google.com/p/go')
		shutit.send('cd /go && hg update go1.1.2')
		shutit.send('export GOROOT=/go')
		shutit.send('export GOBIN=/go/bin')
		shutit.send('apt-get install -y gcc g++ make build-essential')
		shutit.send('cd /go/src && ./all.bash')
		shutit.send('export PATH=$PATH:/go/bin')
		shutit.send('/bin/bash -c "git clone git://github.com/davecheney/golang-crosscompile.git && source golang-crosscompile/crosscompile.bash && go-crosscompile-build-all"')
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
                'shutit.tk.crosscompile.crosscompile', 782914092.00,
                depends=['shutit.tk.setup']
        )
