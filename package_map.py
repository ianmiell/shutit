"""Stores known package maps for different distributions.
"""

#The MIT License (MIT)
#
#Copyright (C) 2014 OpenBet Limited
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of
#this software and associated documentation files (the "Software"), to deal in
#the Software without restriction, including without limitation the rights to
#use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#of the Software, and to permit persons to whom the Software is furnished to do
#so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#ITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.


# Structured by package, then another dict with
# install_type -> mapped package inside that.
# The keys are then the canonical package names.
PACKAGE_MAP = {
	'apache2':               {'apt':'apache2',           'yum':'httpd'},
	'httpd':                 {'apt':'apache2',           'yum':'httpd'},
	'adduser':               {'apt':'adduser',           'yum':''},
	'php5':                  {'apt':'php5',              'yum':'php'},
	'ruby-dev':              {'apt':'ruby-dev',          'yum':'ruby-devel',    'brew':'ruby-build'},
	'git':                   {'emerge':'dev-vcs/git'},
	'vagrant':               {'brew':'Caskroom/cask/vagrant'},
	'virtualbox':            {'brew':'Caskroom/cask/virtualbox'},
	'build-essential':       {'brew':'gcc', 'yum':'gcc make gcc-c++'},
	'sudo':                  {'brew':''},
	'netcat':                {'apt':'netcat',            'yum':'nc'},
	'nc':                    {'apt':'netcat',            'yum':'nc'},
	'python-dev':            {'apt':'python-dev',        'yum':'python-devel'},
	'python-devel':          {'apt':'python-dev',        'yum':'python-devel'},
	'mysql-devel':           {'apt':'libmysqlclient-dev', 'yum':'mysql-devel'},
	'libmysqlclient-dev':    {'apt':'libmysqlclient-dev', 'yum':'mysql-devel'},
	'libkrb5-dev':           {'apt':'libkrb5-dev',       'yum':'krb5-devel'},
	'libffi-dev':            {'apt':'libffi-dev',        'yum':'libffi-devel'},
	'libffi-devel':          {'apt':'libffi-dev',        'yum':'libffi-devel'},
	'libsasl2-dev':          {'apt':'libsasl2-dev',      'yum':''},
	'libssl-dev':            {'apt':'libssl-dev',        'yum':'openssl-devel'},
}


# A list of OS Family members                                                                                                         
# Suse      = SLES, SLED, OpenSuSE, Suse                                                                                              
# Archlinux = Archlinux                                                                                                               
# Mandrake  = Mandriva, Mandrake                                                                                                      
# Solaris   = Solaris, Nexenta, OmniOS, OpenIndiana, SmartOS                                                                          
# AIX       = AIX                                                                                                                     
# FreeBSD   = FreeBSD                                                                                                                 
# HP-UK     = HPUX                                                                                                                    
# OSDIST_DICT = {'/etc/vmware-release':'VMwareESX','/etc/openwrt_release':'OpenWrt','/etc/system-release':'OtherLinux','/etc/release':'Solaris','/etc/arch-release':'Archlinux','/etc/SuSE-release':'SuSE','/etc/gentoo-release':'Gentoo'}
#    # A list of dicts.  If there is a platform with more than one package manager, put the preferred one last.  If there is an ansible module, use that as the value for the 'name' key.
#PKG_MGRS = [{'path':'/usr/bin/zypper','name':'zypper'},{'path':'/usr/sbin/urpmi','name':'urpmi'},{'path':'/usr/bin/pacman','name':'pacman'},{'path':'/bin/opkg','name':'opkg'},{'path':'/opt/local/bin/pkgin','name':'pkgin'},{'path':'/opt/local/bin/port','name':'macports'},{'path':'/usr/sbin/pkg','name':'pkgng'},{'path':'/usr/sbin/swlist','name':'SD-UX'},{'path':'/usr/sbin/pkgadd','name':'svr4pkg'},{'path':'/usr/bin/pkg','name':'pkg'},
#    ]
# Map install types based on /etc/issue contents
INSTALL_TYPE_MAP = {'ubuntu':'apt',
	                'debian':'apt',
	                'linuxmint':'apt',
	                'steamos':'apt',
	                'red hat':'yum',
	                'oracleserver':'yum',
	                'amazon':'yum',
	                'centos':'yum',
	                'fedora':'yum',
	                'fedora_dnf':'dnf',
	                'alpine':'apk',
	                'shutit':'src',
	                'coreos':'docker',
	                'gentoo':'emerge',
	                'osx':'brew',
	                'arch':'pacman',
	                'cygwin':'apt-cyg'}



def map_packages(package_str, install_type):
	res = ''
	for package in package_str.split():
		res = res + ' ' + map_package(package,install_type)
	return res


def map_package(package, install_type):
	"""If package mapping exists, then return it, else return package.
	"""
	if package in PACKAGE_MAP.keys():
		for itype in PACKAGE_MAP[package].keys():
			if itype == install_type:
				return PACKAGE_MAP[package][install_type]
	# Otherwise, simply return package
	return package


def find_package(sought_package):
	"""Is this name mentioned anywhere? Then return it as a suggestion?
	"""
	# First check top-level keys
	if sought_package in PACKAGE_MAP.keys():
		return PACKAGE_MAP[sought_package]
	for package in PACKAGE_MAP.keys():
		for install_type in PACKAGE_MAP[package].keys():
			if sought_package == PACKAGE_MAP[package][install_type]:
				return {package:PACKAGE_MAP[package]}
	return None
