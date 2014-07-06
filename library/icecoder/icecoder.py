
# Created from dockerfile: /space/git/dockerfiles_repos/dockerfile-examples/icecoder/Dockerfile
from shutit_module import ShutItModule

class icecoder(ShutItModule):

        def is_installed(self,shutit):
                return False

        def build(self,shutit):
		shutit.send('apt-get update')
		shutit.send('apt-get install -y apache2 php5 libapache2-mod-php5 unzip')
		shutit.send('export APACHE_RUN_USER=www-data')
		shutit.send('export APACHE_RUN_GROUP=www-data')
		shutit.send('export APACHE_LOG_DIR=/var/log/apache2')
		shutit.install('wget')
		shutit.send('mkdir -p /var/www')
		shutit.send('wget -O /var/www/icecoder.zip http://icecoder.net/download-zip?version=3.0beta')
		shutit.send('cd /var/www && unzip -o icecoder.zip')
		shutit.send('cd /var/www && mv ICEco* icecoder')
		shutit.send('chown www-data -R /var/www/icecoder/lib /var/www/icecoder/backups /var/www/icecoder/test')
		shutit.send('mkdir /var/www/projects && chown -R www-data /var/www/projects && chmod g+s /var/www/projects')
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
        return icecoder(
                'shutit.tk.icecoder.icecoder', 782914092.00,
                depends=['shutit.tk.setup']
        )
