"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class alfs(ShutItModule):


	def is_installed(self, shutit):
		return shutit.file_exists('/root/shutit_build/module_record/' + self.module_id + '/built')


	def build(self, shutit):
		shutit.install('build-essential bison subversion wget curl texinfo libxml2 gawk patch sudo ncurses-dev libxml2-utils libxml2-dev locales')
		shutit.run_script('''
			echo "LANG=en_US.UTF-8" > /etc/default/locale
			echo "LC_MESSAGES=POSIX" >> /etc/default/locale
			echo "LANGUAGE=en" >> /etc/default/locale
			locale-gen en_US.UTF-8
		''')
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
		password = '2mvjsthr'
		shutit.set_password(password, user='lfs')
		shutit.send('echo "lfs ALL=(ALL:ALL) NOPASSWD: ALL" >> /etc/sudoers')
		# use latest
		shutit.send('svn co svn://svn.linuxfromscratch.org/ALFS/jhalfs/trunk jhalfs-trunk')
		shutit.send('cd jhalfs-trunk')
		shutit.multisend('make config',{r'\(GETPKG\)':'y',r'\(SRC_ARCHIVE\)':'',r'\(RETRYSRCDOWNLOAD\)':'y',r'\(RETRYDOWNLOADCNT\)':'',r'\(DOWNLOADTIMEOUT\)':'',r'\(SERVER\)':'',r'\(CONFIG_TESTS\)':'n',r'\(LANG\)':'C',r'Groff page size':'2',r'Create SBU':'n',r'\(BOOK_LFS\)':'',r'relSVN':'',r'\(CUSTOM_TOOLS\)':'',r'\(BLFS_TOOL\)':'',r'\(CONFIG_USER\)':'',r'\(BUILDDIR\)':'',r'\(CLEAN\)':'',r'\(PKGMNGT\)':'',r'\(INSTALL_LOG\)':'',r'\(HAVE_FSTAB\)':'',r'\(CONFIG_BUILD_KERNEL\)':'',r'\(STRIP\)':'',r'\(VIMLANG\)':'',r'\(NO_PROGRESS_BAR\)':'',r'\(TIMEZONE\)':'',r'\(FULL_LOCALE\)':'n',r'\(COMPARE\)':'',r'\(CONFIG_OPTIMIZE\)':'',r'\(SCRIPT_ROOT\)':'',r'\(JHALFSDIR\)':'',r'\(LOGDIRBASE\)':'',r'\(LOGDIR\)':'',r'\(TESTLOGDIRBASE\)':'',r'\(TESTLOGDIR\)':'',r'\(FILELOGDIRBASE\)':'',r'\(FILELOGDIR\)':'',r'\(ICALOGDIR\)':'',r'\(FARCELOGDIR\)':'',r'\(MKFILE\)':'',r'\(XSL\)':'',r'\(PKG_LST\)':'',r'\(REBUILD_MAKEFILE\)':'',r'\(RUNMAKE\)':'y'})
		shutit.send('touch configuration.old') # cheat to avoid error
		shutit.multisend('./jhalfs run',{'Do you want to run jhalfs':'yes','Are you happy with these settings':'yes'},timeout=9999999)
		shutit.login('lfs')
		shutit.send('cd /mnt/build_dir/jhalfs')
		shutit.send('make',timeout=999999,exit_values=['0','2']) # this will fail, but needs to be run to get to correct it (next line)
		shutit.send(r'''sudo sed -i '4s/.*/cp $PKGDIR\/gettext-runtime\/intl\/plural.c $PKGDIR\/gettext-runtime\/intl\/pluralx.c/' /mnt/build_dir/jhalfs/lfs-commands/chapter05/052-gettext''') #HACK: sudo vi 052-gettext 
		shutit.send('make',timeout=999999) # this will fail, but needs to be run to get to correct it (next line)
		shutit.logout()
		# Download stuff required to build wget (simplest thing to build)
		shutit.send('curl -L http://www.openssl.org/source/openssl-1.0.1j.tar.gz | tar -zxf -')
		shutit.send('curl -L http://www.linuxfromscratch.org/patches/blfs/svn/openssl-1.0.1j-fix_parallel_build-1.patch > /mnt/build_dir/wget/openssl-1.0.1j-fix_parallel_build-1.patch')
		shutit.send('curl -L http://anduin.linuxfromscratch.org/sources/other/certdata.txt > /mnt/build_dir/wget/certdata.txt')
		shutit.send('curl -L http://ftp.gnu.org/gnu/wget/wget-1.16.1.tar.xz | xz -d | tar -xf')
		shutit.pause_point('chroot login?')
		shutit.send('cd /openssl-*')
		shutit.send('patch -Np1 -i ../openssl-1.0.1j-fix_parallel_build-1.patch')
		shutit.send('./config --prefix=/usr --openssldir=/etc/ssl --libdir=lib shared zlib-dynamic')
		shutit.send('make')
		shutit.send('make MANDIR=/usr/share/man MANSUFFIX=ssl install')
		shutit.send('install -dv -m755 /usr/share/doc/openssl-1.0.1j')
		shutit.send('cp -vfr doc/*     /usr/share/doc/openssl-1.0.1j')
		shutit.send_host_file('/usr/bin/make-cert.pl','context/make-cert.pl')
		shutit.send('chmod +x /usr/bin/make-cert.pl')
		shutit.send_host_file('/usr/bin/make-ca.pl','context/make-ca.pl')
		shutit.send('chmod +x /usr/bin/make-ca.pl')
		shutit.send_host_file('/usr/bin/remove-expired-certs.pl','context/remove-expired-certs.pl')
		shutit.send('chmod +x /usr/bin/remove-expired-certs.pl')
		shutit.send('rm -f certdata.txt')
		shutit.send('curl -L http://anduin.linuxfromscratch.org/sources/other/certdata.txt > certdata.txt')
		shutit.send('make-ca.sh')
		shutit.send('remove-expired-certs.sh certs')
		shutit.send('install -d /etc/ssl/certs')
		shutit.send('cp -v certs/*.pem /etc/ssl/certs')
		shutit.send('c_rehash')
		shutit.send('install BLFS-ca-bundle*.crt /etc/ssl/ca-bundle.crt')
		shutit.send('ln -sfv ../ca-bundle.crt /etc/ssl/certs/ca-certificates.crt')
		shutit.send('rm -r certs BLFS-ca-bundle*')
		# wget
		shutit.send('cd wget/wget-*')
		shutit.send('./configure --prefix=/usr --sysconfdir=/etc --with-ssl=openssl')
		shutit.send('make')
		shutit.send('make install')
		shutit.send('echo ca-directory=/etc/ssl/certs >> /etc/wgetrc')
		shutit.pause_point('chroot logout')
		# Remove left-overs
		shutit.send('rm -rf /mnt/build_dir/sources /mnt/build_dir/tools /mnt/build_dir/xslt /mnt/build_dir/jhalfs*')
		shutit.send('echo "ShutIt Distro 0.1" > /etc/issue')
		shutit.send('cd /mnt/build_dir')
		shutit.send('tar -cf /artifacts/lfs.tar .')
		shutit.send('xz /artifacts/lfs.tar')
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

