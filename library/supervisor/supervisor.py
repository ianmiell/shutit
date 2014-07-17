
# Created from dockerfile: /tmp/supervisor/Dockerfile
from shutit_module import ShutItModule

class supervisor(ShutItModule):

        def is_installed(self, shutit):
                return False

        def build(self, shutit):
        shutit.send('echo "deb http://archive.ubuntu.com/ubuntu precise main universe" > /etc/apt/sources.list')
        shutit.send('apt-get update')
        shutit.send('apt-get upgrade -y')
        shutit.send('apt-get install -y supervisor')
        shutit.send('mkdir -p /var/log/supervisor')
        shutit.send_host_file('/etc/supervisor/conf.d/supervisord.conf','context/supervisord.conf')
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
        return supervisor(
                'shutit.tk.supervisor.supervisor', 0.0001,
                depends=['shutit.tk.setup']
        )
