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
		password = '1ncharge'
		shutit.set_password(password, user='lfs')
		shutit.send('echo "lfs ALL=(ALL) ALL" >> /etc/sudoers')
		# use latest
		shutit.send('svn co svn://svn.linuxfromscratch.org/ALFS/jhalfs/trunk jhalfs-trunk')
		shutit.send('cd jhalfs-trunk')
		# TODO - set locale - http://www.shellhacks.com/en/HowTo-Change-Locale-Language-and-Character-Set-in-Linux
		shutit.multisend('make config',{'(GETPKG)':'y','(SRC_ARCHIVE)':'','(RETRYSRCDOWNLOAD)':'y','(RETRYDOWNLOADCNT)':'','(DOWNLOADTIMEOUT)':'','(SERVER)':'','(CONFIG_TESTS)':'n','(LANG)':'C','Groff page size':'2','Create SBU':'n','(BOOK_LFS)':'','relSVN':'','(CUSTOM_TOOLS)':'','(BLFS_TOOL)':'','(CONFIG_USER)':'','(BUILDDIR)':'','(CLEAN)':'','(PKGMNGT)':'','(INSTALL_LOG)':'','(HAVE_FSTAB)':'','(CONFIG_BUILD_KERNEL)':'','(STRIP)':'','(VIMLANG)':'','(NO_PROGRESS_BAR)':'','(TIMEZONE)':'','(FULL_LOCALE)':'','(COMPARE)':'','(CONFIG_OPTIMIZE)':'','(SCRIPT_ROOT)':'','(JHALFSDIR)':'','(LOGDIRBASE)':'','(LOGDIR)':'','(TESTLOGDIRBASE)':'','(TESTLOGDIR)':'','(FILELOGDIRBASE)':'','(FILELOGDIR)':'','(ICALOGDIR)':'','(FARCELOGDIR)':'','(MKFILE)':'','(XSL)':'','(PKG_LST)':'','(REBUILD_MAKEFILE)':'','Are you happy with these settings':'','Do you wish':'','oad an Alt':'E'})
		shutit.send('make')
		shutit.send(r'''sed -i 's@cd gettext-tools@cd gettext-tools && cp ../gettext-runtime/intl/plural.c ../gettext-runtime/intl/pluralx.c@' /mnt/build_dir/jhalfs/lfs-commands/chapter05/052-gettext''') #HACK: sudo vi 052-gettext 
		shutit.login('lfs')
		shutit.send('cd /mnt/build_dir/jhalfs')
		shutit.multisend('make',{'assword:':password})
		shutit.logout()
		shutit.send('rm -rf /mnt/build_dir/sources /mnt/build_dir/tools')
		shutit.send('cd /mnt/build_dir')
		shutit.send('tar -cf /lfs.tar .')
#docker cp id:sd.tar .
# # copy to artifacts
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
		description='',
		maintainer='',
		depends=['shutit.tk.setup']
	)

