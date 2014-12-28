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
		shutit.send('mkdir -p /mnt/build_dir/xslt') # build libxslt
		shutit.send('cd /mnt/build_dir/xslt')
		shutit.send('curl -L http://xmlsoft.org/sources/libxslt-1.1.28.tar.gz | tar -zxf -')
		shutit.send('cd libxslt-*')
		shutit.send('./configure --prefix=/usr --disable-static')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('groupadd lfs')
		shutit.send('useradd -s /bin/bash -g lfs -m -k /dev/null lfs')
		shutit.send('cd /mnt/build_dir')
		password = '1ncharge'
		shutit.set_password(password, user='lfs')
		shutit.send('echo "lfs ALL=(ALL:ALL) NOPASSWD: ALL" >> /etc/sudoers')
		# use latest
		shutit.send('svn co svn://svn.linuxfromscratch.org/ALFS/jhalfs/trunk jhalfs-trunk')
		shutit.send('cd jhalfs-trunk')
		# TODO - set locale - http://www.shellhacks.com/en/HowTo-Change-Locale-Language-and-Character-Set-in-Linux
		shutit.multisend('make config',{r'\(GETPKG\)':'y',r'\(SRC_ARCHIVE\)':'',r'\(RETRYSRCDOWNLOAD\)':'y',r'\(RETRYDOWNLOADCNT\)':'',r'\(DOWNLOADTIMEOUT\)':'',r'\(SERVER\)':'',r'\(CONFIG_TESTS\)':'n',r'\(LANG\)':'C',r'Groff page size':'2',r'Create SBU':'n',r'\(BOOK_LFS\)':'',r'relSVN':'',r'\(CUSTOM_TOOLS\)':'',r'\(BLFS_TOOL\)':'',r'\(CONFIG_USER\)':'',r'\(BUILDDIR\)':'',r'\(CLEAN\)':'',r'\(PKGMNGT\)':'',r'\(INSTALL_LOG\)':'',r'\(HAVE_FSTAB\)':'',r'\(CONFIG_BUILD_KERNEL\)':'',r'\(STRIP\)':'',r'\(VIMLANG\)':'',r'\(NO_PROGRESS_BAR\)':'',r'\(TIMEZONE\)':'',r'\(FULL_LOCALE\)':'',r'\(COMPARE\)':'',r'\(CONFIG_OPTIMIZE\)':'',r'\(SCRIPT_ROOT\)':'',r'\(JHALFSDIR\)':'',r'\(LOGDIRBASE\)':'',r'\(LOGDIR\)':'',r'\(TESTLOGDIRBASE\)':'',r'\(TESTLOGDIR\)':'',r'\(FILELOGDIRBASE\)':'',r'\(FILELOGDIR\)':'',r'\(ICALOGDIR\)':'',r'\(FARCELOGDIR\)':'',r'\(MKFILE\)':'',r'\(XSL\)':'',r'\(PKG_LST\)':'',r'\(REBUILD_MAKEFILE\)':'',r'\(RUNMAKE\)':'y'})
		shutit.send('touch configuration.old') # cheat to avoid error
		shutit.multisend('./jhalfs run',{'Do you want to run jhalfs':'yes','Are you happy with these settings':'yes'},timeout=9999999)
		shutit.login('lfs')
		shutit.send('cd /mnt/build_dir/jhalfs')
		shutit.send('make',timeout=999999)
		shutit.send(r'''sed -i 's@cd gettext-tools@cd gettext-tools && cp ../gettext-runtime/intl/plural.c ../gettext-runtime/intl/pluralx.c@' /mnt/build_dir/jhalfs/lfs-commands/chapter05/052-gettext''') #HACK: sudo vi 052-gettext 
		shutit.logout()
		shutit.send('rm -rf /mnt/build_dir/sources /mnt/build_dir/tools /mnt/build_dir/xslt')
		shutit.send('cd /mnt/build_dir')
		shutit.send('tar -cf /artifacts/lfs.tar .')
#FROM scratch
#ADD sd.tar /
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
		description='Automated Linux from Scratch',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup']
	)

