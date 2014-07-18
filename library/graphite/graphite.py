
# Created from dockerfile: /space/git/dockerfiles_repos/docker-graphite/Dockerfile
from shutit_module import ShutItModule

class graphite(ShutItModule):

    def is_installed(self, shutit):
        return False

    def build(self, shutit):
        shutit.send('echo \'deb http://us.archive.ubuntu.com/ubuntu/ precise universe\' >> /etc/apt/sources.list')
        shutit.send('apt-get -y update')
        shutit.send('apt-get -y install python-ldap python-cairo python-django python-twisted python-django-tagging python-simplejson python-memcache python-pysqlite2 python-support python-pip gunicorn supervisor nginx-light')
        shutit.send('pip install whisper')
        shutit.send('pip install --install-option="--prefix=/var/lib/graphite" --install-option="--install-lib=/var/lib/graphite/lib" carbon')
        shutit.send('pip install --install-option="--prefix=/var/lib/graphite" --install-option="--install-lib=/var/lib/graphite/webapp" graphite-web')
        shutit.send_host_file('/etc/nginx/nginx.conf', 'context/./nginx.conf')
        shutit.send_host_file('/etc/supervisor/conf.d/supervisord.conf', 'context/./supervisord.conf')
        shutit.send_host_file('/var/lib/graphite/webapp/graphite/initial_data.json', 'context/./initial_data.json')
        shutit.send_host_file('/var/lib/graphite/webapp/graphite/local_settings.py', 'context/./local_settings.py')
        shutit.send_host_file('/var/lib/graphite/conf/carbon.conf', 'context/./carbon.conf')
        shutit.send_host_file('/var/lib/graphite/conf/storage-schemas.conf', 'context/./storage-schemas.conf')
        shutit.send('mkdir -p /var/lib/graphite/storage/whisper')
        shutit.send('touch /var/lib/graphite/storage/graphite.db /var/lib/graphite/storage/index')
        shutit.send('chown -R www-data /var/lib/graphite/storage')
        shutit.send('chmod 0775 /var/lib/graphite/storage /var/lib/graphite/storage/whisper')
        shutit.send('chmod 0664 /var/lib/graphite/storage/graphite.db')
        shutit.send('cd /var/lib/graphite/webapp/graphite && python manage.py syncdb --noinput')
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
        return graphite(
                'shutit.tk.graphite.graphite', 0.124162874,
                depends=['shutit.tk.setup']
        )
