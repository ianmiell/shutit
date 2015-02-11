"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class alfs(ShutItModule):

	def build(self, shutit):
		# variable setup
		password = '2mvjsthr'
		src_archive = '/mnt/build_dir/src_archive'
		# install programs
		shutit.install('build-essential bison subversion wget curl texinfo libxml2 gawk patch sudo ncurses-dev libxml2-utils libxml2-dev locales tidy docbook-xml udev')
		shutit.install('vim strace xterm') # optional
		# Try and sort out locale
		shutit.send('''echo "LANG=en_US.UTF-8" > /etc/default/locale''')
		shutit.send('echo "LC_MESSAGES=POSIX" >> /etc/default/locale')
		shutit.send('echo "LANGUAGE=en" >> /etc/default/locale')
		shutit.send('locale-gen en_US.UTF-8')
		shutit.send('export LANG=en_GB.UTF-8')
		# build directory setup
		shutit.send('mkdir -p /mnt/build_dir')
		shutit.send('cd /mnt/build_dir')
		# build libxslt
		shutit.send('mkdir -p /mnt/build_dir/xslt')
		shutit.send('cd /mnt/build_dir/xslt')
		shutit.send('curl -L http://xmlsoft.org/sources/libxslt-1.1.28.tar.gz | tar -zxf -')
		shutit.send('cd libxslt-*')
		shutit.send('./configure --prefix=/usr --disable-static')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('rm -rf /mnt/build_dir/xslt')
		# Add lfs user
		shutit.send('groupadd lfs')
		shutit.send('useradd -s /bin/bash -g lfs -m -k /dev/null lfs')
		shutit.send('cd /mnt/build_dir')
		shutit.set_password(password, user='lfs')
		shutit.send('echo "lfs ALL=(ALL:ALL) NOPASSWD: ALL" >> /etc/sudoers')
		# use latest
		shutit.send('svn co svn://svn.linuxfromscratch.org/ALFS/jhalfs/trunk jhalfs-trunk')
		shutit.send('cd jhalfs-trunk')
		shutit.send('mkdir -p ' + src_archive)
		shutit.multisend('make config',{r'\(GETPKG\)':'y',r'\(SRC_ARCHIVE\)':src_archive,r'\(RETRYSRCDOWNLOAD\)':'y',r'\(RETRYDOWNLOADCNT\)':'5',r'\(DOWNLOADTIMEOUT\)':'30',r'\(SERVER\)':'ftp://ftp.lfs-matrix.net',r'\(CONFIG_TESTS\)':'n',r'\(LANG\)':'C',r'Groff page size':'2',r'Create SBU':'n',r'\(BOOK_LFS\)':'1',r'relSVN':'',r'\(CUSTOM_TOOLS\)':'n',r'\(BLFS_TOOL\)':'y','\(BLFS_SVN\)':'1',r'\(DEP_LIBXML\)':'y',r'\(DEP_LIBXSLT\)':'y',r'\(DEP_TIDY\)':'y',r'\(DEP_DBXML\)':'y',r'\(DEP_LYNX\)':'n',r'\(DEP_SUDO\)':'y',r'\(DEP_WGET\)':'y',r'\(DEP_GPM\)':'y',r'\(DEP_SVN\)':'n',r'\(DEP_PYTHON\)':'y',r'\(DEP_OPENSSL\)':'y',r'\(BLFS_ROOT\)':'/blfs_root',r'\(BLFS_XML\)':'blfs-xml',r'\(TRACKING_DIR\)':'/var/lib/jhalfs/BLFS',r'\(CONFIG_USER\)':'',r'\(BUILDDIR\)':'/mnt/build_dir',r'\(CLEAN\)':'n',r'\(PKGMNGT\)':'n',r'\(INSTALL_LOG\)':'n',r'\(HAVE_FSTAB\)':'n',r'\(CONFIG_BUILD_KERNEL\)':'n',r'\(STRIP\)':'y',r'\(VIMLANG\)':'n',r'\(NO_PROGRESS_BAR\)':'y',r'\(TIMEZONE\)':'',r'\(FULL_LOCALE\)':'n',r'\(COMPARE\)':'n',r'\(CONFIG_OPTIMIZE\)':'',r'\(SCRIPT_ROOT\)':'',r'\(JHALFSDIR\)':'',r'\(LOGDIRBASE\)':'',r'\(LOGDIR\)':'',r'\(TESTLOGDIRBASE\)':'',r'\(TESTLOGDIR\)':'',r'\(FILELOGDIRBASE\)':'',r'\(FILELOGDIR\)':'',r'\(ICALOGDIR\)':'',r'\(FARCELOGDIR\)':'',r'\(MKFILE\)':'',r'\(XSL\)':'',r'\(PKG_LST\)':'',r'\(REBUILD_MAKEFILE\)':'n',r'\(RUNMAKE\)':'y'})
		shutit.send('''sed -i '313,320s/.*//' jhalfs''') # remove stuff that asks us questions
		shutit.send('''sed -i '94,104s/.*//' jhalfs''') # remove stuff that asks us questions
		shutit.send('./jhalfs run',exit_values=['0','1'])
		shutit.login('lfs')
		shutit.send('cd /mnt/build_dir/jhalfs')
		shutit.send('make',timeout=999999,exit_values=['0','2']) # this will fail, but needs to be run to get to correct it (next line)
		shutit.send(r'''sudo sed -i '4s/.*/cp $PKGDIR\/gettext-runtime\/intl\/plural.c $PKGDIR\/gettext-runtime\/intl\/pluralx.c/' /mnt/build_dir/jhalfs/lfs-commands/chapter05/052-gettext''') #HACK: sudo vi 052-gettext 
		shutit.send('make',timeout=999999)
		shutit.logout()
		shutit.send('echo "ShutIt Distro 0.1" > /mnt/build_dir/etc/issue')
		shutit.send('echo "export HISTCONTROL=ignorespace:cmdhist" >> /mnt/build_dir/root/.bashrc')
		shutit.send('echo "export HISTSIZE=99999999" >> /mnt/build_dir/root/.bashrc')
		shutit.send('''echo 'export HISTTIMEFORMAT="%s "' >> /mnt/build_dir/root/.bashrc''')
		shutit.send('echo "shopt -s histappend" >> /mnt/build_dir/root/.bashrc')
		shutit.send('mkdir -p /opt/alfs_build')
		# mv rather than delete, as resluting image will have record in
		shutit.send('mv /mnt/build_dir/sources /opt/alfs_build')
		shutit.send('mv /mnt/build_dir/tools /opt/alfs_build')
		shutit.send('mv ' + src_archive + ' /opt/alfs_build')
		shutit.send('mv /mnt/build_dir/jhalfs* /opt/alfs_build')
		shutit.send('mv /mnt/build_dir/blfs_root /opt/alfs_build')
		shutit.send('cd /mnt/build_dir')
		shutit.send('tar -cf - . | xz - > /artifacts/lfs_$(date +%s).tar.xz')
		return True

	#def get_config(self, shutit):
	#	shutit.get_config(self.module_id,'item','default')
	#	return True

	def check_ready(self, shutit):
		return True
	
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

