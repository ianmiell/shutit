
# Created from dockerfile: ./Dockerfile
from shutit_module import ShutItModule

class docker_registry(ShutItModule):

        def is_installed(self,shutit):
                return False

        def build(self,shutit):
		shutit.send('apt-get update; apt-get install -y git-core build-essential python-dev libevent1-dev python-openssl liblzma-dev wget; rm /var/lib/apt/lists/*_*')
		shutit.send('cd /tmp; wget http://python-distribute.org/distribute_setup.py')
		shutit.send('cd /tmp; python distribute_setup.py; easy_install pip; rm distribute_setup.py')
		shutit.send_host_file('/docker-registry','context/docker-registry')
		shutit.send_host_file('/etc/boto.cfg','context/docker-registry/config/boto.cfg')
		shutit.send('cd /docker-registry && pip install -r requirements.txt')
		shutit.send('export dev_version=1')
		shutit.send_host_file('/docker-registry/config/config.yml','context/config-local-standalone.yml')
		shutit.send('pushd /docker-registry')
		shutit.send('popd')
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
        return docker_registry(
                'shutit.tk.docker_registry.docker_registry', 782914092.00,
                depends=['shutit.tk.setup']
        )
