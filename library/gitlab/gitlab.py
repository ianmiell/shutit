
# Created from dockerfile: /tmp/docker-gitlab/Dockerfile
# Maintainer:              sameer@damagehead.com
from shutit_module import ShutItModule

class gitlab(ShutItModule):

	def build(self, shutit):
		shutit.send('apt-key adv --keyserver keyserver.ubuntu.com --recv E1DF1F24 && echo "deb http://ppa.launchpad.net/git-core/ppa/ubuntu trusty main" >> /etc/apt/sources.list && apt-key adv --keyserver keyserver.ubuntu.com --recv C3173AA6 && echo "deb http://ppa.launchpad.net/brightbox/ruby-ng/ubuntu trusty main" >> /etc/apt/sources.list && apt-key adv --keyserver keyserver.ubuntu.com --recv C300EE8C && echo "deb http://ppa.launchpad.net/nginx/stable/ubuntu trusty main" >> /etc/apt/sources.list && apt-get update && apt-get install -y supervisor logrotate locales nginx openssh-server mysql-client postgresql-client redis-tools git-core ruby2.1 python2.7 python-docutils libmysqlclient18 libpq5 zlib1g libyaml-0-2 libssl1.0.0 libgdbm3 libreadline6 libncurses5 libffi6 libxml2 libxslt1.1 libcurl3 libicu52 && update-locale LANG=C.UTF-8 LC_MESSAGES=POSIX && gem install --no-document bundler && rm -rf /var/lib/apt/lists/* # 20140918')
		shutit.send('mkdir -p /app/setup')
		shutit.send_host_dir('/app/setup', 'context/assets/setup/')
		shutit.send('chmod 755 /app/setup/install')
		shutit.send('/app/setup/install')
		shutit.send('mkdir -p /app/setup/config/assets/config/')
		#shutit.send_host_dir('/app/setup/config/assets/config/', 'context/assets/config/')
		shutit.send_host_file('/app/init', 'context/assets/init')
		shutit.send('chmod 755 /app/init')
		return True

def module():
		return gitlab(
				'shutit.tk.gitlab.gitlab', 0.121351351,
				description='',
				maintainer='sameer@damagehead.com',
				depends=['shutit.tk.setup']
		)
