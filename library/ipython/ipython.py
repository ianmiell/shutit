
# Created from dockerfile: /space/git/dockerfiles_repos/Dockerfiles/ipython/Dockerfile
from shutit_module import ShutItModule

class ipython(ShutItModule):

        def is_installed(self, shutit):
                return False

        def build(self, shutit):
		shutit.send('echo "deb http://archive.ubuntu.com/ubuntu precise main universe" > /etc/apt/sources.list')
		shutit.send('apt-get update')
		shutit.send('apt-get upgrade -y')
		shutit.send('apt-get install -y language-pack-en')
		shutit.send('export LANGUAGE=en_US.UTF-8')
		shutit.send('export LANG=en_US.UTF-8')
		shutit.send('export LC_ALL=en_US.UTF-8')
		shutit.send('locale-gen en_US.UTF-8')
		shutit.send('dpkg-reconfigure locales')
		shutit.send('apt-get install -y openssh-server git-core libxml2-dev curl python build-essential make gcc python-dev wget libsqlite3-dev sqlite3')
		shutit.send('apt-get install -y postgresql-client-9.1 postgresql-client-common libpq5')
		shutit.send('apt-get install -y libpq-dev')
		shutit.send('wget http://python-distribute.org/distribute_setup.py')
		shutit.send('python distribute_setup.py')
		shutit.send('wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py')
		shutit.send('python get-pip.py')
		shutit.send('apt-get install -y libfreetype6 libfreetype6-dev')
		shutit.send('apt-get install -y python-imaging libpng-dev')
		shutit.send('apt-get install -y libzmq-dev')
		shutit.send('pip install pyzmq')
		shutit.send('pip install numpy')
		shutit.send('pip install matplotlib')
		shutit.send('pip install pandas')
		shutit.send('pip install jinja2')
		shutit.send('pip install ipython')
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
        return ipython(
                'shutit.tk.ipython.ipython', 0.1325135,
                depends=['shutit.tk.setup']
        )
