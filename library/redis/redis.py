
# Created from dockerfile: /space/git/shutit/tmp/Dockerfile
# Maintainer:              
from shutit_module import ShutItModule

class redis(ShutItModule):

	def build(self, shutit):
		# https://github.com/dockerfile/redis
		shutit.install('make')
		shutit.install('wget')
		shutit.send('pushd /tmp')
		shutit.send('wget http://download.redis.io/redis-stable.tar.gz')
		shutit.send('tar xvzf redis-stable.tar.gz')
		shutit.send('pushd redis-stable')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('cp -f src/redis-sentinel /usr/local/bin')
		shutit.send('mkdir -p /etc/redis')
		shutit.send('cp -f *.conf /etc/redis')
		shutit.send('rm -rf /tmp/redis-stable*')
		shutit.send("""sed -i 's/^\(bind .*\)$/# \\1/' /etc/redis/redis.conf""")
		shutit.send("""sed -i 's/^\(daemonize .*\)$/# \\1/' /etc/redis/redis.conf""")
		shutit.send("""sed -i 's/^\(dir .*\)$/# \\1\\ndir \/data/' /etc/redis/redis.conf""")
		shutit.send("""sed -i 's/^\(logfile .*\)$/# \\1/' /etc/redis/redis.conf""")
		shutit.send('popd')
		shutit.send('popd')
		return True

def module():
	return redis(
		'shutit.tk.redis.redis', 0.135135,
		description='',
		maintainer='',
		depends=['shutit.tk.setup']
	)
