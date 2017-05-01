import shutit_util

class ShutItPexpectSessionEnvironment(object):

	def __init__(self,
	             prefix):
		"""Represents a new 'environment' in ShutIt, which corresponds to a host or any
		machine-like location (eg docker container, ssh'd to host, or even a chroot jail
		with a /tmp folder that has not been touched by shutit.
		"""
		if prefix == 'ORIGIN_ENV':
			self.environment_id = prefix
		else:
			self.environment_id = shutit_util.random_id()
		self.module_root_dir              = '/'
		self.modules_installed            = [] # has been installed in this build
		self.modules_not_installed        = [] # modules _known_ not to be installed
		self.modules_ready                = [] # has been checked for readiness and is ready (in this build)
		self.modules_recorded             = []
		self.modules_recorded_cache_valid = False
		self.install_type                 = ''
		self.distro                       = ''
		self.distro_version               = ''
		self.users                        = dict()
		self.build                        = {}
		self.build['apt_update_done']     = False
		self.build['emerge_update_done']  = False
		self.build['apk_update_done']     = False

	def __str__(self):
		string = ''
		string += 'distro                       = ' + str(self.distro)
		string += 'module_root_dir              = ' + str(self.module_root_dir)
		string += 'modules_installed            = ' + str(self.modules_installed)
		string += 'modules_not_installed        = ' + str(self.modules_not_installed)
		string += 'modules_ready                = ' + str(self.modules_ready)
		string += 'modules_recorded_cache_valid = ' + str(self.modules_recorded)
		string += 'install_type                 = ' + str(self.install_type)
		string += 'distro                       = ' + str(self.distro)
		string += 'distro_version               = ' + str(self.distro_version)
		string += 'users                        = ' + str(self.users)
		string += 'self.build                   = ' + str(self.build)
		return string
