
# Created from dockerfile: /space/git/dockerfiles_repos/redis/Dockerfile
# Maintainer:              
from shutit_module import ShutItModule

class redis(ShutItModule):

        def is_installed(self,shutit):
                return False

        def build(self,shutit):
		#add
		shutit.send_host_dir('/usr/src/redis','context/.')
		shutit.send('groupadd -r redis')
		shutit.send('useradd -r -g redis redis')
		shutit.install('build-essential tcl valgrind')
		shutit.send('make -C /usr/src/redis')
		#in
		shutit.send('make -C /usr/src/redis test || true')
		shutit.send('make -C /usr/src/redis install')
		shutit.send('mkdir /data && chown redis:redis /data')
		shutit.send('pushd /data')
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
        return redis(
                'shutit.tk.redis.redis', 0.1502412,
		description='redis, based on https://github.com/docker-library/redis',
                depends=['shutit.tk.setup']
        )
