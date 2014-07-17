from shutit_module import ShutItModule
import os

class ssh_key(ShutItModule):

	# TODO: look for different ssh keys

	def check_ready(self,shutit):
		f = shutit.cfg[self.module_id]['ssh_keyfile_dir'] + '/' + shutit.cfg[self.module_id]['ssh_keyfile_name']
		if not os.path.isfile(f) and not os.path.isfile(f + '.pub'):
			shutit.log('File: ' + f + "\ndoesn't exist on host",force_stdout=True)
			return False
		return True

	def is_installed(self,shutit):
		return False

	def build(self,shutit):
		cfg = shutit.cfg
		f = shutit.cfg[self.module_id]['ssh_keyfile_dir'] + '/' + shutit.cfg[self.module_id]['ssh_keyfile_name']
		shutit.send('mkdir -p /root/.ssh')
		contents = open(os.path.expanduser(f)).read()
		shutit.send_file('/root/.ssh/' + shutit.cfg[self.module_id]['ssh_keyfile_name'],contents)
		contents = open(os.path.expanduser(f + '.pub')).read()
		shutit.send_file('/root/.ssh/' + shutit.cfg[self.module_id]['ssh_keyfile_name'] + '.pub',contents)
		shutit.send('chmod 0600 ~/.ssh/' + shutit.cfg[self.module_id]['ssh_keyfile_name'])
		shutit.send('chmod 0644 ~/.ssh/' + shutit.cfg[self.module_id]['ssh_keyfile_name'] + '.pub')
		return True

	def finalize(self,shutit):
		# We don't want to leave keys lying around.
		# The real user module should remove these but let's take no chances.
		shutit.send('rm -rf /root/.ssh')
		return True

	def get_config(self,shutit):
		cfg = shutit.cfg
		# SSH passphrase, default to empty
		shutit.get_config(self.module_id,'passphrase','')
		shutit.get_config(self.module_id,'login','')
		shutit.get_config(self.module_id,'ssh_keyfile_dir','/home/' + shutit.cfg['shutit.tk.adduser.adduser']['user'] + '/.ssh')
		shutit.get_config(self.module_id,'ssh_keyfile_name','id_rsa')
		cfg[self.module_id]['login'] = cfg[self.module_id]['login'].split()
		if 'root' not in cfg[self.module_id]['login']:
			cfg[self.module_id]['login'].append('root')
		return True

	# Assumes no passphrase - adding a config is a TODO
	def test(self,shutit):
		cfg = shutit.cfg
		shutit.send('su - ' + cfg[self.module_id]['login'][0],cfg['expect_prompts']['base_prompt'],check_exit=False)
		shutit.setup_prompt('ssh_key_tmp_prompt')
		expect = ['authenticity','Enter passphrase','assword',shutit.get_default_expect()]
		send = 'ssh localhost'
		while True:
			res = shutit.send(send,expect=expect,check_exit=False)
			if res == 0:
				send = 'yes'
			elif res == 1:
				send = shutit.cfg['shutit.tk.ssh_key.ssh_key']['passphrase']
			elif res == 2:
				send = shutit.cfg['shutit.tk.adduser.adduser']['password']
			elif res == 3:
				break
		shutit.send('exit',expect=cfg['expect_prompts']['root_prompt'])
		return True

def module():
	return ssh_key(
		'shutit.tk.ssh_key.ssh_key', 0.1259,
		description='ssh key provisioning, just for the build. keys deleted at end of build.',
		depends=['shutit.tk.setup','shutit.tk.adduser.adduser']
	)

