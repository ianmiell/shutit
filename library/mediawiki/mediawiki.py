
# Created from dockerfile: /space/git/dockerfiles_repos/nickstenning/dockerfiles/mediawiki/Dockerfile
from shutit_module import ShutItModule

class mediawiki(ShutItModule):

        def is_installed(self,shutit):
                return False

        def build(self,shutit):
		shutit.send('echo \'deb http://us.archive.ubuntu.com/ubuntu/ precise universe\' >> /etc/apt/sources.list')
		shutit.send('apt-get -y update')
		shutit.send('LC_ALL=C DEBIAN_FRONTEND=noninteractive apt-get install -y supervisor nginx-light php5-fpm php5-intl php5-mysql php5-')
		shutit.send('LC_ALL=C DEBIAN_FRONTEND=noninteractive apt-get install -y php-apc php5-gd php5-intl php5-mysqlnd php5-pgsql')
		shutit.send_host_file('/etc/nginx/nginx.conf','context/./nginx.conf')
		shutit.send_host_file('/etc/supervisor/conf.d/supervisord.conf','context/./supervisord.conf')
		shutit.send_host_file('/etc/php5/fpm/php-fpm.conf','context/./fpm.conf')
		shutit.send_host_file('/etc/php5/fpm/pool.d/www.conf','context/./fpm-pool-www.conf')
		shutit.send('mkdir /src')
		shutit.install('wget')
		shutit.send('mkdir -p /src')
		shutit.send('wget -O /src/mediawiki.tgz http://download.wikimedia.org/mediawiki/1.21/mediawiki-1.21.2.tar.gz')
		shutit.send('cd /src && tar zxf mediawiki.tgz')
		shutit.send('ln -snf /src/mediawiki-1.21.2 /src/mediawiki')
		shutit.send('chown -R www-data:www-data /src/mediawiki/')
		shutit.send('mkdir /data')
		shutit.send('ln -s /data/LocalSettings.php /src/mediawiki/LocalSettings.php')
		shutit.send('rm -rf /src/mediawiki/images')
		shutit.send('ln -s /data/images /src/mediawiki/images')
		shutit.send_host_file('/usr/bin/mediawiki-start','context/./mediawiki-start')
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
        return mediawiki(
                'shutit.tk.mediawiki.mediawiki', 0.12412515,
                depends=['shutit.tk.setup']
        )
