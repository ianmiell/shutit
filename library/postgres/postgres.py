from shutit_module import ShutItModule

class postgres(ShutItModule):

	def build(self, shutit):
		shutit.send("""cat > /root/stop_postgres.sh <<< 'service postgresql stop'""")
		shutit.install('postgresql')
		shutit.add_line_to_file('# postgres', '/root/start_postgres.sh')
		shutit.add_line_to_file("echo Setting shmmax for postgres", '/root/start_postgres.sh')
		shutit.add_line_to_file('sysctl -w kernel.shmmax=268435456', '/root/start_postgres.sh', force=True)
		shutit.add_line_to_file('service postgresql start', '/root/start_postgres.sh', force=True)
		shutit.send("""cat > /root/stop_postgres.sh <<< \\
'service postgresql stop'""")
		shutit.send('chmod +x /root/start_postgres.sh')
		shutit.send('chmod +x /root/stop_postgres.sh')
		return True

	def start(self, shutit):
		shutit.send('/root/start_postgres.sh', check_exit=False)
		return True

	def stop(self, shutit):
		shutit.send('/root/stop_postgres.sh', check_exit=False)
		return True

def module():
	return postgres(
		'shutit.tk.postgres.postgres', 0.320,
		description='installs postgres and handles shm settings changes',
		depends=['shutit.tk.setup']
	)

