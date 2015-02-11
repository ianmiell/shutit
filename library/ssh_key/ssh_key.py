from shutit_module import ShutItModule
import os

class ssh_key(ShutItModule):

	def build(self, shutit):
		shutit.install('openssh-client')
		shutit.send("ssh-keygen -P '' -f '/root/.ssh/id_rsa'")
		shutit.send('cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys')
		return True

	def finalize(self, shutit):
		# We don't want to leave keys lying around.
		if shutit.cfg[self.module_id]['remove_keys']:
			shutit.send('rm -rf /root/.ssh')
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id,'remove_keys',True,boolean=True)
		return True

	def test(self, shutit):
		d = {'authenticity':'yes'}
		shutit.multisend('ssh localhost',d,expect=shutit.cfg['expect_prompts']['base_prompt'],check_exit=False)
		#expect = ['authenticity', shutit.cfg['expect_prompts']['base_prompt']]
		#send = 'ssh localhost'
		#while True:
		#    res = shutit.send(send, expect=expect, check_exit=False)
		#    if res == 0:
		#        send = 'yes'
		#    elif res == 1:
		#        break
		shutit.send('exit')
		return True

def module():
	return ssh_key(
		'shutit.tk.ssh_key.ssh_key', 0.121759,
		description='ssh key provisioning, just for the build. private keys are deleted at end of build.',
		depends=['shutit.tk.setup', 'shutit.tk.ssh_server.ssh_server']
	)

