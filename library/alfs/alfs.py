"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class alfs(ShutItModule):


	def is_installed(self, shutit):
		return shutit.file_exists('/root/shutit_build/module_record/' + self.module_id + '/built')

	def build(self, shutit):
		shutit.install('build-essential bison subversion wget curl texinfo libxml2 gawk patch sudo ncurses-dev libxml2-utils libxml2-dev')
		shutit.install('vim strace') # optional
		shutit.send('mkdir -p /mnt/build_dir')
		shutit.send('cd /mnt/build_dir')
		shutit.send('export LANG=en_GB.UTF-8')
		# build libxslt
		shutit.send('mkdir -p /mnt/build_dir/xslt')
		shutit.send('cd /mnt/build_dir/xslt')
		shutit.send('curl -L http://xmlsoft.org/sources/libxslt-1.1.28.tar.gz | tar -zxf -')
		shutit.send('cd libxslt-*')
		shutit.send('./configure --prefix=/usr --disable-static')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('groupadd lfs')
		shutit.send('useradd -s /bin/bash -g lfs -m -k /dev/null lfs')
		shutit.send('cd /mnt/build_dir')
		# use latest
		shutit.send('svn co svn://svn.linuxfromscratch.org/ALFS/jhalfs/trunk jhalfs-trunk')
		shutit.send('cd jhalfs-trunk')
		shutit.set_password('1ncharge', user='lfs')
		shutit.send('echo "lfs ALL=(ALL) ALL" >> /etc/sudoers')
		# TODO - set locale - http://www.shellhacks.com/en/HowTo-Change-Locale-Language-and-Character-Set-in-Linux
		shutit.login('lfs')
		shutit.pause_point('')
		shutit.logout()
		return True

	#def get_config(self, shutit):
	#	shutit.get_config(self.module_id,'item','default')
	#	return True

	#def check_ready(self, shutit):
	#	return True
	
	#def start(self, shutit):
	#	return True

	#def stop(self, shutit):
	#	return True

	#def finalize(self, shutit):
	#	return True

	#def remove(self, shutit):
	#	return True

	#def test(self, shutit):
	#	return True

def module():
	return alfs(
		'shutit.tk.alfs.alfs', 782914092.001,
		description='',
		maintainer='',
		depends=['shutit.tk.setup']
	)

