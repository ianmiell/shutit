"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class learnxthehardway(ShutItModule):

	def build(self, shutit):
		shutit.install('git')
		shutit.install('python')
		shutit.install('python-pip')
		shutit.install('calibre')
		shutit.install('gzip')
		shutit.install('tar')
		shutit.install('wget')
		shutit.install('texlive-latex-base')
		shutit.install('texlive-latex-recommended')
		shutit.install('texlive-fonts-extra')
		shutit.install('texlive-fonts-recommended')
		shutit.install('texlive-latex-extra')
		shutit.send('pip install dexy')
		shutit.send('pip install docutils')
		shutit.send('wget https://gitorious.org/learn-x-the-hard-way/learn-x-the-hard-way/archive/663fd4f6afd17f9d16fe10bafe3e64fdfb29e629.tar.gz')
		shutit.send('tar -zxf 663fd4f6afd17f9d16fe10bafe3e64fdfb29e629.tar.gz')
		shutit.send('cd learn-x-the-hard-way-learn-x-the-hard-way')
		shutit.send('dexy setup')
		shutit.send('dexy')
		return True

def module():
	return learnxthehardway(
		'shutit.tk.learnxthehardway.learnxthehardway', 0.331125183957,
		description='',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.vnc.vnc']
	)

