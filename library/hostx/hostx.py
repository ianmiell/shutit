from shutit_module import ShutItModule
import os

class hostx(ShutItModule):

	def build(self, shutit):
		shutit.send('groupadd -g ' + shutit.cfg[self.module_id]['gid'] + ' ' + shutit.cfg[self.module_id]['username'])
		shutit.send('useradd -d /home/' + shutit.cfg[self.module_id]['username'] + ' -s /bin/bash -m ' + shutit.cfg[self.module_id]['username'] + ' -u ' + shutit.cfg[self.module_id]['uid'] + ' -g ' + shutit.cfg[self.module_id]['gid'])
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id, 'username', str(os.getlogin()))
		shutit.get_config(self.module_id, 'uid', str(os.getuid()))
		shutit.get_config(self.module_id, 'gid', str(os.getgid()))
		return True


def module():
	return hostx(
		'shutit.tk.hostx.hostx', 0.3265,
		description='Share your host X server with the container',
		depends=['shutit.tk.setup']
	)

