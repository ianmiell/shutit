from shutit_module import ShutItModule

class memcache(ShutItModule):

	def build(self, shutit):
		shutit.install('memcached')
		shutit.install('libmemcached-dev')
		shutit.install('libmemcached-tools')
		shutit.send("""cat > /root/start_memcache.sh <<< 'service memcached start'""")
		shutit.send("""cat > /root/stop_memcache.sh <<< 'service memcached stop'""")
		shutit.send('chmod +x /root/start_memcache.sh')
		shutit.send('chmod +x /root/stop_memcache.sh')
		return True

	def start(self,shutit):
		shutit.send('/root/start_memcache.sh')
		return True

	def stop(self,shutit):
		shutit.send('/root/stop_memcache.sh')
		return True


def module():
	return memcache(
		'shutit.tk.memcache.memcache', 0.317,
		description='memcache server',
		depends=['shutit.tk.setup']
	)

