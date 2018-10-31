"""Stores known package maps for different distributions.
"""

from __future__ import print_function
import logging
import shutit_pexpect

from shutit_sendspec import ShutItSendSpec

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

# TODO: figure out how to install pip in yum, and/or return a function that
#       does that rather than a string (see https://github.com/ianmiell/shutit/issues/313)

# Structured by package, then another dict with
# install_type -> mapped package inside that.
# The keys are then the canonical package names.

def yum_install_pip(shutit_pexpect_session):
	# https://www.liquidweb.com/kb/how-to-install-pip-on-centos-7/
	shutit_pexpect_session.send(ShutItSendSpec(shutit_pexpect_session,
	                                           send='yum install -y epel-release',
	                                           loglevel=logging.INFO))
	shutit_pexpect_session.send(ShutItSendSpec(shutit_pexpect_session,
	                                           send='yum -y update',
	                                           loglevel=logging.INFO))
	shutit_pexpect_session.send(ShutItSendSpec(shutit_pexpect_session,
	                                           send='yum -y install python-pip',
	                                           loglevel=logging.INFO))

PACKAGE_MAP = {
	'apache2':               {                            'yum':'httpd'},
	'httpd':                 {'apt':'apache2'},
	'adduser':               {'apt':'adduser',            'yum':''},
	'php5':                  {                            'yum':'php'},
	'ruby-dev':              {                            'yum':'ruby-devel',       'brew':'ruby-build'},
	'git':                   {                                                                                        'emerge':'dev-vcs/git'},
	'vagrant':               {                                                      'brew':'Caskroom/cask/vagrant'},
	'virtualbox':            {                                                      'brew':'Caskroom/cask/virtualbox'},
	'build-essential':       {                            'yum':'gcc make gcc-c++', 'brew':'gcc'},
	'sudo':                  {                                                      'brew':''},
	'netcat':                {                            'yum':'nc'},
	'nc':                    {'apt':'netcat'},
	'python-dev':            {                            'yum':'python-devel'},
	'python-devel':          {'apt':'python-dev'},
	'mysql-devel':           {'apt':'libmysqlclient-dev'},
	'libmysqlclient-dev':    {                            'yum':'mysql-devel'},
	'libkrb5-dev':           {                            'yum':'krb5-devel'},
	'libffi-dev':            {                            'yum':'libffi-devel'},
	'libffi-devel':          {'apt':'libffi-dev'},
	'libsasl2-dev':          {                            'yum':''},
	'libssl-dev':            {                            'yum':'openssl-devel'},
	'kvm':                   {'apt':'qemu-kvm'},
	'libvirt':               {'apt':'libvirt-bin'},
	'libvirt-dev':           {                            'yum':'libvirt-devel'},
	'libvirt-devel':         {'apt':'libvirt-dev'},
	'docker':                {'apt':'docker.io'},
	'asciinema':             {                            'yum':'epel-release asciinema'},
	'run-one':               {                            'yum':''},
	'python-pip':            {                            'yum': yum_install_pip},
	'piptest':               {'apt':'python-pip',         'yum': yum_install_pip},
    'lsb-release':           {                            'yum': 'redhat-lsb-core'},
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
	                'raspbian':'apt',
	                'linuxmint':'apt',
	                'steamos':'apt',
	                'red hat':'yum',
	                'redhatenterpriseserver':'yum',
	                'oracleserver':'yum',
	                'amazon':'yum',
	                'amazonami':'yum',
	                'centos':'yum',
	                'fedora':'yum',
	                'fedora_dnf':'dnf',
	                'alpine':'apk',
	                'shutit':'src',
	                'coreos':'docker',
	                'gentoo':'emerge',
	                'osx':'brew',
	                'arch':'pacman',
	                'minishift':'none',
	                'minikube':'none',
	                'cygwin':'apt-cyg'}



def map_packages(shutit_pexpect_session, package_str, install_type):
	res = ''
	for package in package_str.split():
		map_package_res = map_package(shutit_pexpect_session, package,install_type)
		if map_package_res == '':
			return res
		res += ' ' + map_package_res
	return res


def map_package(shutit_pexpect_session, package, install_type):
	"""If package mapping exists, then return it, else return package.
	"""
	if package in PACKAGE_MAP.keys():
		for itype in PACKAGE_MAP[package].keys():
			if itype == install_type:
				ret = PACKAGE_MAP[package][install_type]
				if isinstance(ret,str):
					return ret
				if callable(ret):
					ret(shutit_pexpect_session)
					return ''
	# Otherwise, simply return package
	return package
