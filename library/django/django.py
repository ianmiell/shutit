
from shutit_module import ShutItModule

class django(ShutItModule):

        def is_installed(self, shutit):
                return False

        def build(self, shutit):

        shutit.send('apt-get install -y -q software-properties-common')
        #shutit.send('add-apt-repository -y "deb http://archive.ubuntu.com/ubuntu $(lsb_release -sc) universe"')
        shutit.send('apt-get install -y -q vim')
        shutit.send('apt-get install -y -q nano')
        shutit.send('apt-get install -y -q curl')
        shutit.send('apt-get install -y -q git')
        shutit.send('apt-get install -y -q make')
        shutit.send('apt-get install -y -q wget')
        shutit.send('apt-get install -y -q build-essential')
        shutit.send('apt-get install -y -q g++')
        shutit.send('apt-get install -y -q memcached')
        shutit.send('apt-get install -y -q imagemagick')
        shutit.send('apt-get install -y -q graphicsmagick')
        shutit.send('apt-get install -y -q graphicsmagick-libmagick-dev-compat')
        shutit.send('apt-get install -y -q apache2')
        shutit.send('apt-get install -y -q libapache2-mod-php5')
        shutit.send('apt-get install -y -q python-software-properties')
        shutit.send('apt-get install -y -q python')
        shutit.send('apt-get install -y -q python-setuptools')
        shutit.send('apt-get install -y -q python-virtualenv')
        shutit.send('apt-get install -y -q python-dev')
        shutit.send('apt-get install -y -q python-distribute')
        shutit.send('apt-get install -y -q python-pip')
        shutit.send('apt-get install -y -q libjpeg8-dev')
        shutit.send('apt-get install -y -q zlib1g-dev')
        shutit.send('apt-get install -y -q libfreetype6-dev')
        shutit.send('apt-get install -y -q liblcms1-dev')
        shutit.send('apt-get install -y -q libwebp-dev')
        shutit.send('apt-get install -y -q libtiff-dev')
        shutit.send('easy_install django')
                return True

    def finalize(self, shutit):

        return True

def module():
        return django(
                'shutit.tk.django.django', 0.3185,
                depends=['shutit.tk.setup','shutit.tk.mysql.mysql']
        )
