
# Created from dockerfile: /space/git/dockerfiles_repos/dockerfile-examples/icecoder/Dockerfile
from shutit_module import ShutItModule

class icecoder(ShutItModule):

        def is_installed(self, shutit):
                return False

        def build(self, shutit):
        shutit.install('apache2')
        shutit.install('php5')
        shutit.install('libapache2-mod-php5')
        shutit.install('unzip')
        shutit.send('export APACHE_RUN_USER=www-data')
        shutit.send('export APACHE_RUN_GROUP=www-data')
        shutit.send('export APACHE_LOG_DIR=/var/log/apache2')
        shutit.install('wget')
        shutit.send('mkdir -p /var/www')
        shutit.send('wget -O /var/www/icecoder.zip \'http://icecoder.net/download-zip?version=3.0beta\'')
        shutit.send('cd /var/www')
        shutit.send('unzip -o icecoder.zip')
        shutit.send('cd /var/www')
        shutit.send('mv ICEco* icecoder')
        shutit.send('chown www-data -R /var/www/icecoder/lib /var/www/icecoder/backups /var/www/icecoder/test')
        shutit.send('mkdir /var/www/projects')
        shutit.send('chown -R www-data /var/www/projects')
        shutit.send('chmod g+s /var/www/projects')
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
        return icecoder(
                'shutit.tk.icecoder.icecoder', 0.1241435,
                depends=['shutit.tk.setup']
        )
