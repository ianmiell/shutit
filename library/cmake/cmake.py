"""ShutIt module. See http://shutit.tk

Based on: https://github.com/maidsafe/MaidSafe/wiki/Build-Instructions-for-Linux#all-other-prerequisites
"""

from shutit_module import ShutItModule

class cmake(ShutItModule):

	def build(self, shutit):
		if shutit.cfg['target']['install_type'] == 'apt' and shutit.cfg['target']['distro'] == 'ubuntu':
			if shutit.cfg['target']['distro_version'] >= "14.04":
				shutit.install('cmake')
			else:
				shutit.install('gcc')
				shutit.install('g++')
				shutit.install('python-software-properties')
				shutit.install('git')
				shutit.send('pushd /opt')
				shutit.send('git clone git://cmake.org/cmake.git')
				shutit.send('pushd cmake')
				shutit.send('git checkout v2.8.12.2')
				shutit.send('./bootstrap')
				shutit.send('make')
				shutit.send('make install')
				shutit.add_to_bashrc("alias cmake='cmake -DCMAKE_C_COMPILER=gcc-4.8 -DCMAKE_CXX_COMPILER=g++-4.8'")
				shutit.send('rm -rf /opt/cmake')
		return True

def module():
	return cmake(
		'shutit.tk.cmake.cmake', 0.09187246124,
		description='CMake',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup.setup']
	)

