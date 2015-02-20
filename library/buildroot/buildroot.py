"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class buildroot(ShutItModule):

	def build(self, shutit):
		shutit.install('wget')
		shutit.install('build-essential')
		shutit.install('ncurses-dev')
		shutit.install('rsync')
		shutit.install('python')
		shutit.install('unzip')
		shutit.install('bc')
		shutit.install('xterm')
		shutit.install('subversion')
		shutit.install('bzr')
		shutit.install('cvs')
		shutit.install('git')
		shutit.install('mercurial')
		shutit.install('rsync')
		shutit.install('default-jdk')
		shutit.install('asciidoc')
		shutit.install('w3m')
		shutit.install('python')
		shutit.install('dblatex')
		shutit.install('graphviz')
		shutit.install('python-matplotlib')
		shutit.install('cpio')
		shutit.send('mkdir -p /opt/buildroot')
		shutit.send('pushd /opt/buildroot')
		shutit.send('wget http://buildroot.uclibc.org/downloads/buildroot-2014.08.tar.gz')
		shutit.send('gunzip buildroot-2014.08.tar.gz')
		shutit.send('tar -xf buildroot-2014.08.tar')
		shutit.send('ls -r | tail -1 | xargs -IXXX ln -s XXX buildroot')
		shutit.send('unset CC')
		shutit.send('unset CXX')
		shutit.send_host_file('/opt/buildroot/buildroot/.config','context/config.shutitdist.base')
		shutit.send('cd buildroot')
		shutit.send('export TERM=xterm')
		shutit.send('make')
		return True

def module():
	return buildroot(
		'shutit.tk.buildroot.buildroot', 0.01251352,
		description='http://www.uclibc.org/toolchains.html',
		maintainer='',
		depends=['shutit.tk.setup']
	)

