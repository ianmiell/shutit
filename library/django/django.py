
from shutit_module import ShutItModule

class django(ShutItModule):

	def build(self, shutit):
		shutit.install('software-properties-common')
		#shutit.send('add-apt-repository -y "deb http://archive.ubuntu.com/ubuntu $(lsb_release -sc) universe"')
		shutit.install('vim')
		shutit.install('nano')
		shutit.install('curl')
		shutit.install('git')
		shutit.install('make')
		shutit.install('wget')
		shutit.install('build-essential')
		shutit.install('g++')
		shutit.install('memcached')
		shutit.install('imagemagick')
		shutit.install('graphicsmagick')
		shutit.install('graphicsmagick-libmagick-dev-compat')
		shutit.install('apache2')
		shutit.install('libapache2-mod-php5')
		shutit.install('python-software-properties')
		shutit.install('python-setuptools')
		shutit.install('python-virtualenv')
		shutit.install('python-dev')
		shutit.install('python-distribute')
		shutit.install('python-pip')
		shutit.install('libjpeg8-dev')
		shutit.install('zlib1g-dev')
		shutit.install('libfreetype6-dev')
		shutit.install('liblcms2-dev')
		shutit.install('libwebp-dev')
		shutit.install('libtiff5-dev')
		shutit.send('easy_install django')
		return True

def module():
		return django(
				'shutit.tk.django.django', 0.3185,
				depends=['shutit.tk.setup', 'shutit.tk.mysql.mysql']
		)
