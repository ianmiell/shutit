
# Created from dockerfile: /space/git/dockerfiles_repos/dockerfiles/rabbitmq/Dockerfile
from shutit_module import ShutItModule

class rabbitmq(ShutItModule):

	def build(self, shutit):
		shutit.install('wget logrotate rabbitmq-server')
		shutit.send('/usr/lib/rabbitmq/bin/rabbitmq-plugins enable rabbitmq_management')
		return True

def module():
		return rabbitmq(
				'shutit.tk.rabbitmq.rabbitmq', 0.1523523,
				depends=['shutit.tk.setup']
		)
