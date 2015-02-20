from shutit_module import ShutItModule
import os

class ssh_key(ShutItModule):

	def is_install(self, shutit):
		return False

	def build(self, shutit):
		shutit.install('openssh-client')
		shutit.install('openssh-server')
		shutit.send('service ssh restart')
		shutit.send("ssh-keygen -P '' -f '/root/.ssh/id_rsa'")
		shutit.send('cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys')
		return True

	def finalize(self, shutit):
		# We don't want to leave keys lying around.
		if shutit.cfg[self.module_id]['remove_keys']:
			shutit.send('rm -rf /root/.ssh')
		shutit.send('service ssh stop')
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id,'remove_keys',True,boolean=True)
		return True

	def test(self, shutit):
		d = {'authenticity':'yes'}
		shutit.multisend('ssh localhost',d,expect=shutit.cfg['expect_prompts']['base_prompt'],check_exit=False)
		shutit.send('exit')
		return True

def module():
	return ssh_key(
		'shutit.tk.ssh_key.ssh_key', 0.121759,
		description='ssh key provisioning, just for the build. private keys are deleted at end of build.',
		depends=['shutit.tk.setup']
	)

