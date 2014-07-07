
# Created from dockerfile: /space/git/dockerfiles_repos/dockerfiles/mariadb/Dockerfile
from shutit_module import ShutItModule

class mariadb(ShutItModule):

        def is_installed(self,shutit):
                return False

        def build(self,shutit):
		shutit.send('yum -y update; yum clean all')
		shutit.send('yum -y install mariadb-server pwgen supervisor psmisc net-tools; yum clean all')
		shutit.send_host_file('/start.sh','context/./start.sh')
		shutit.send_host_file('/config_mariadb.sh','context/./config_mariadb.sh')
		shutit.send_host_file('/etc/supervisord.conf','context/./supervisord.conf')
		shutit.send('chmod 755 /start.sh')
		shutit.send('chmod 755 /config_mariadb.sh')
		shutit.send('/config_mariadb.sh')
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
        return mariadb(
                'shutit.tk.mariadb.mariadb', 0.12313251,
                depends=['shutit.tk.setup']
        )
