from shutit_module import ShutItModule
import os

class hostx(ShutItModule):

	def build(self, shutit):
		shutit.send('groupadd -g ' + shutit.collect_config(self.module_id,'gid') + ' ' + shutit.collect_config(self.module_id,'username'))
		shutit.send('useradd -d /home/' + shutit.collect_config(self.module_id,'username') + ' -s /bin/bash -m ' + shutit.collect_config(self.module_id,'username') + ' -u ' + shutit.collect_config(self.module_id,'uid') + ' -g ' + shutit.collect_config(self.module_id,'gid'))
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

