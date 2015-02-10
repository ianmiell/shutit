from shutit_module import ShutItModule
import os

class copy_ssh_key(ShutItModule):

	def check_ready(self,shutit):
		files = [
			"~/.ssh/id_rsa",
			"~/.ssh/id_rsa.pub"			
		]

		for f in files:
			if not os.path.isfile(os.path.expanduser(f)):
				shutit.log('File: ' + f + ' does not exist on host', force_stdout=True)
				return False

		return True

	def is_installed(self,shutit):
		# If we use this we must do it every build
		return False

	def build(self,shutit):
		shutit.send('useradd -d /home/' + shutit.cfg[self.module_id]['login'] + ' -s /bin/bash -m ' + shutit.cfg[self.module_id]['login'])
		shutit.install('passwd')
		shutit.install('sudo')
		shutit.install('adduser')
		shutit.set_password(shutit.cfg[self.module_id]['login'], user=shutit.cfg[self.module_id]['login'])
		cfg = shutit.cfg
		shutit.login(shutit.cfg[self.module_id]['login'])
		shutit.send('mkdir -p ~/.ssh')
		file_perms = {
			"~/.ssh/id_rsa"     : "0600",
			"~/.ssh/id_rsa.pub" : "0644"
		}
		for f, p in file_perms.iteritems():
				contents = open(os.path.expanduser(f)).read()
				shutit.send_file(f, contents)
		shutit.send('chmod {perm} {file}'.format(perm=p, file=f))
		shutit.logout()
		return True

	def finalize(self,shutit):
		# We don't want to leave keys lying around.
		# The real user module should remove these but let's take no chances.
		for login in shutit.cfg[self.module_id]['login']:
			shutit.send('rm -rf ~' + login + '/.ssh')
		return True

	def get_config(self,shutit):
		cfg = shutit.cfg
		# SSH passphrase, default to empty
		shutit.get_config(self.module_id,'passphrase','')
		shutit.get_config(self.module_id,'login')
		return True

	def test(self,shutit):
		return True

def module():
	return copy_ssh_key(
		'shutit.tk.copy_ssh_key.copy_ssh_key', 0.1259,
		description='Copy your ssh key for the build',
		depends=['shutit.tk.setup']
	)

