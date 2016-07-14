#!/usr/bin/env pythen

"""ShutIt skeleton functions
"""

# The MIT License (MIT)
# 
# Copyright (C) 2014 OpenBet Limited
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# ITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import ConfigParser
import StringIO
import argparse
import base64
import binascii
import getpass
import glob
import hashlib
import imp
import json
import logging
import operator
import os
import random
import re
import readline
import shutil
import socket
import stat
import string
import sys
import textwrap
import threading
import time
import urllib2
import urlparse
import jinja2
import pexpect
import texttable
import shutit_global
import shutit_main
import shutit_util
from shutit_module import ShutItFailException
from shutit_module import ShutItModule


def create_skeleton():
	"""Creates module based on a template supplied as a git repo.
	"""
	shutit = shutit_global.shutit
	template_setup_script = 'setup.sh'
	# Set up local directories
	skel_path        = shutit.cfg['skeleton']['path']
	skel_module_name = shutit.cfg['skeleton']['module_name']
	skel_domain      = shutit.cfg['skeleton']['domain']
	skel_domain_hash = shutit.cfg['skeleton']['domain_hash']
	skel_depends     = shutit.cfg['skeleton']['depends']
	skel_shutitfiles = shutit.cfg['skeleton']['shutitfiles']
	skel_delivery    = shutit.cfg['skeleton']['delivery']
	# Set up shutitfile cfg
	shutit.shutitfile['base_image'] = shutit.cfg['skeleton']['base_image']
	shutit.shutitfile['cmd']        = """/bin/sh -c 'sleep infinity'"""
	shutit.shutitfile['expose']     = []
	shutit.shutitfile['env']        = []
	shutit.shutitfile['volume']     = []
	shutit.shutitfile['onbuild']    = []
	shutit.shutitfile['script']     = []


	# Check setup
	if len(skel_path) == 0 or skel_path[0] != '/':
		shutit.fail('Must supply a directory and it must be absolute')
	if os.path.exists(skel_path):
		shutit.fail(skel_path + ' already exists')
	if len(skel_module_name) == 0:
		shutit.fail('Must supply a name for your module, eg mymodulename')
	if not re.match('^[a-zA-z_][0-9a-zA-Z_]+$', skel_module_name):
		shutit.fail('Module names must comply with python classname standards: cf: http://stackoverflow.com/questions/10120295/valid-characters-in-a-python-class-name')
	if len(skel_domain) == 0:
		shutit.fail('Must supply a domain for your module, eg com.yourname.madeupdomainsuffix')


	# arguments
	shutit.cfg['skeleton']['volumes_arg'] = ''
	for varg in shutit.shutitfile['volume']:
		shutit.cfg['skeleton']['volumes_arg'] += ' -v ' + varg + ':' + varg
	shutit.cfg['skeleton']['ports_arg'] = ''
	if type(shutit.shutitfile['expose']) == str:
		for parg in shutit.shutitfile['expose']:
			shutit.cfg['skeleton']['ports_arg'] += ' -p ' + parg + ':' + parg
	else:
		for parg in shutit.shutitfile['expose']:
			for port in parg.split():
				shutit.cfg['skeleton']['ports_arg'] += ' -p ' + port + ':' + port
	shutit.cfg['skeleton']['env_arg'] = ''
	for earg in shutit.shutitfile['env']:
		shutit.cfg['skeleton']['env_arg'] += ' -e ' + earg.split()[0] + ':' + earg.split()[1]

	# Create folders and process templates.
	os.makedirs(skel_path)
	os.chdir(skel_path)
	git_command = 'git clone -q ' + shutit.cfg['skeleton']['template_repo'] + ' -b ' + shutit.cfg['skeleton']['template_branch'] + ' --depth 1 ' + shutit.cfg['skeleton']['template_folder']
	res = os.system(git_command)
	if res != 0:
		shutit.fail('git command: \n' + git_command + '\nFailed while setting up skeleton')
	os.system('rm -rf ' + shutit.cfg['skeleton']['template_folder'] + '/.git')
	templates=jinja2.Environment(loader=jinja2.FileSystemLoader(shutit.cfg['skeleton']['template_folder']))
	templates_list = templates.list_templates()
	for template_item in templates_list:
		directory = os.path.dirname(template_item)
		if directory != '' and not os.path.exists(directory):
			os.mkdir(os.path.dirname(template_item))
		template_str = templates.get_template(template_item).render(shutit.cfg)
		f = open(template_item,'w')
		f.write(template_str)
		f.close()
	if shutit.cfg['skeleton']['output_dir']:
		os.system('chmod +x ' + template_setup_script + ' && ./' + template_setup_script + ' > /dev/null 2>&1 && rm -f ' + template_setup_script)
		os.system('rm -rf ' + shutit.cfg['skeleton']['template_folder'])
	else:
		os.system('chmod +x ' + template_setup_script + ' && ./' + template_setup_script + ' && rm -f ' + template_setup_script)
		os.system('rm -rf ' + shutit.cfg['skeleton']['template_folder'])

	# Return program to original path
	os.chdir(sys.path[0])

	# If we have any ShutitFiles
	if skel_shutitfiles:
		try:
			# Attempt to remove any .py files created by default.
			os.remove(skel_path + '/' + skel_module_name + '.py')
		except:
			pass
		_count = 1
		_total = len(skel_shutitfiles)
		buildcnf = ''
		for skel_shutitfile in skel_shutitfiles:
			templatemodule_path   = os.path.join(skel_path, skel_module_name + '_' + str(_count) + '.py')
			(templatemodule,skel_module_id, default_include, ok) = shutitfile_to_shutit_module_template(skel_shutitfile,skel_path,skel_domain,skel_module_name,skel_domain_hash,skel_delivery,skel_depends,_count,_total)
			if not ok:
				shutit.fail('Failed to create shutit module from: ' + skel_shutitfile)
			open(templatemodule_path, 'w').write(templatemodule)
			_count += 1
			buildcnf_path = skel_path + '/configs/build.cnf'
			buildcnf += textwrap.dedent('''\
				[''' + skel_module_id + ''']
				shutit.core.module.build:''' + default_include + '''
			''')
		buildcnf += textwrap.dedent('''\
			shutit.core.module.allowed_images:["''' + shutit.shutitfile['base_image'] + '''"]
			[build]
			base_image:''' + shutit.shutitfile['base_image'] + '''
			[target]
			volumes:
			[repository]
			name:''' + skel_module_name + '''
			''')
		os.chmod(buildcnf_path,0700)
		open(buildcnf_path,'w').write(buildcnf)
		os.chmod(buildcnf_path,0400)



# Parses the shutitfile (passed in as a string)
# and info to extract, and returns a list with the information in a more canonical form, still ordered.
def parse_shutitfile(contents):
	shutit       = shutit_global.shutit
	ret          = []
	full_line    = ''
	for line in contents.split('\n'):
		line = line.strip()
		# Handle continuations
		if len(line) > 0:
			if line[-1] == '\\':
				full_line += line[0:-1]
				continue
			else:
				comment = None
				full_line += line
				if re.match("^IF_NOT+[\s]+([A-Z_]+)[\s]+(.*)$", full_line):
					m = re.match("^IF_NOT+[\s]+([A-Z_]+)[\s]+(.*)$", full_line)
					ret.append(['IF_NOT',m.group(1),m.group(2)])
				elif re.match("^STORE_RUN+[\s]+([a-zA-Z0-9_]+)[\s]+(.*)$", full_line):
					m = re.match("^STORE_RUN+[\s]+([a-zA-Z0-9_]+)[\s]+(.*)$", full_line)
					ret.append(['STORE_RUN',m.group(1),m.group(2)])
				elif re.match("^ELIF_NOT[\s]+([A-Z_]+)[\s]+(.*)$", full_line):
					m = re.match("^ELIF_NOT[\s]+([A-Z_]+)[\s]+(.*)$", full_line)
					ret.append(['ELIF_NOT',m.group(1),m.group(2)])
				elif re.match("^IF[\s]+([A-Z_]+)[\s]+(.*)$", full_line):
					m = re.match("^IF[\s]+([A-Z_]+)[\s]+(.*)$", full_line)
					ret.append(['IF',m.group(1),m.group(2)])
				elif re.match("^ELIF[\s]+([A-Z_]+)[\s]+(.*)$", full_line):
					m = re.match("^ELIF[\s]+([A-Z_]+)[\s]+(.*)$", full_line)
					ret.append(['ELIF',m.group(1),m.group(2)])
				elif re.match("^ELSE$", full_line):
					ret.append(['ELSE'])
				elif re.match("^ENDIF$", full_line):
					ret.append(['ENDIF'])
				elif re.match("^([A-Za-z_]+)[\s]*(.*)$", full_line):
					m = re.match("^[\s]*([A-Za-z_]+)[\s]*(.*)$", full_line)
					ret.append([m.group(1), m.group(2)])
				elif re.match("^#(.*)$", full_line):
					# Comments should be added with 'COMMENT a comment'
					pass
				else:
					full_line_split = ''.join((full_line[:10000].split()))
					full_line_strings = re.findall("[^\x00-\x1F\x7F-\xFF]", full_line_split)
					print 'FAILED TO PARSE: ' + full_line_strings[:30] + '[...]'
					return [], False
				full_line = ''
	return ret, True


def parse_shutitfile_args(args_str):
	"""Parse shutitfile args (eg in the line 'RUN some args', the passed-in args_str would be 'some args').
	If the string is bounded by square brackets, then it's treated in the form: ['arg1','arg2'], and the returned list looks the same.
	If the string composed entirely of name-value pairs (eg RUN a=b c=d) then it's returned as a dict (eg {'a':'b','c':'d'}).
	If what's passed-in is of the form: "COMMAND ['a=b','c=d']" then a dict is also returned.'
	Also eg: ["asd and space=value","asd 2=asdgasdg"]"""
	ret = []
	if args_str == '':
		return ret
	if args_str[0] == '[' and args_str[-1] == ']':
		ret = eval(args_str)
		assert type(ret) == list
	else:
		ret = args_str.split()
		# if all the items have a = in them, then return a dict of nv pairs
	nv_pairs = True
	for item in ret:
		if string.find(item,'=') < 0:
			nv_pairs = False
	if nv_pairs:
		d = {}
		for item in ret:
			item_nv = item.split('=')
			d.update({item_nv[0]:item_nv[1]})
		ret = d
	return ret



# Takes a shutitfile filename and returns a string that represents that Dockerfile as a ShutIt module
def shutitfile_to_shutit_module_template(skel_shutitfile,
                                         skel_path,
                                         skel_domain,
                                         skel_module_name,
                                         skel_domain_hash,
                                         skel_delivery,
                                         skel_depends,
                                         order,
	                                     total):
	shutit = shutit_global.shutit

	if not os.path.exists(skel_shutitfile):
		if urlparse.urlparse(skel_shutitfile)[0] == '':
			shutit.fail('Dockerfile/ShutItFile "' + skel_shutitfile + '" must exist')
		shutitfile_contents = urllib2.urlopen(skel_shutitfile).read()
		shutitfile_dirname = None
	else:
		shutitfile_contents = open(skel_shutitfile).read()
		shutitfile_dirname = os.path.dirname(skel_shutitfile)
		if shutitfile_dirname == '':
			shutitfile_dirname = './'
		if os.path.exists(shutitfile_dirname):
			if os.path.exists(skel_path + '/context'):
				shutil.rmtree(skel_path + '/context')
				shutil.copytree(shutitfile_dirname, skel_path + '/context')
		# Change to this context
		os.chdir(shutitfile_dirname)

	# Process the shutitfile
	shutitfile_representation, ok = process_shutitfile(shutitfile_contents)
	if not ok:
		return '', '', '', False

	# Check the shutitfile representation
	check_shutitfile_representation(shutitfile_representation, skel_delivery)

	# Get the shutit module as a string
	templatemodule, module_id, depends, default_include = generate_shutit_module(shutitfile_representation, skel_domain, skel_module_name, skel_shutitfile, skel_depends, order, total)

	# Final section
	templatemodule += """\n\ndef module():\n\t\treturn template(\n\t\t'"""
	templatemodule += module_id + """', """
	templatemodule += skel_domain_hash + str(order * 0.0001) + str(random.randint(1,999))
	templatemodule += """,\n\t\tdescription='"""
	templatemodule += shutitfile_representation['shutitfile']['description']
	templatemodule += """',\n\t\tdelivery_methods=[('"""
	templatemodule += skel_delivery + """')],\n\t\tmaintainer='"""
	templatemodule += shutitfile_representation['shutitfile']['maintainer']
	templatemodule += """',\n\t\tdepends=[""" + depends + """]\n\t\t)\n"""

	# Return program to main shutit_dir
	if shutitfile_dirname:
		os.chdir(sys.path[0])
	return templatemodule, module_id, default_include, ok



def check_shutitfile_representation(shutitfile_representation, skel_delivery):
	# delivery directives
	# Only allow one type of delivery
	shutit = shutit_global.shutit
	shutitfile_delivery = set()
	# If we've been given a delivery method, add that.
	if skel_delivery:
		shutitfile_delivery.add(skel_delivery)
	for item in shutitfile_representation['shutitfile']['delivery']:
		shutitfile_delivery.add(item[1])
	if len(shutitfile_delivery) > 1:
		shutit.fail('Conflicting delivery methods in ShutItFile')
	elif len(shutitfile_delivery) == 1:
		skel_delivery = shutitfile_delivery.pop()
	else:
		# Default skel_delivery to bash if none seen
		skel_delivery = 'bash'

	if skel_delivery not in shutit_util.allowed_delivery_methods:
		shutit.fail('Disallowed delivery method in ShutItFile: ' + skel_delivery)

	if skel_delivery != 'docker':
		# FROM, ONBUILD, VOLUME, EXPOSE, ENTRYPOINT, CMD, COMMIT, PUSH are verboten
		failed = False
		if shutitfile_representation['shutitfile']['cmd'] != '' or shutitfile_representation['shutitfile']['volume']  != [] or shutitfile_representation['shutitfile']['onbuild'] != [] or shutitfile_representation['shutitfile']['expose']  !=  [] or shutitfile_representation['shutitfile']['entrypoint'] != []:
			failed = True
		for item in shutitfile_representation['shutitfile']['script']:
			if item[0] in ('PUSH','COMMIT'):
				failed = True
				break
		if failed:
			shutit.fail('One of FROM, ONBUILD, VOLUME, EXPOSE, ENTRYPOINT or CMD, COMMIT, PUSH used in ShutItFile  not using the Docker delivery method.')



def generate_shutit_module(shutitfile_representation, skel_domain, skel_module_name, skel_shutitfile, skel_depends, order, total):
	shutit = shutit_global.shutit
	templatemodule = '\n# Created from shutitfile: ' + skel_shutitfile + '\n# Maintainer:              ' + shutitfile_representation['shutitfile']['maintainer'] + '\nfrom shutit_module import ShutItModule\n\nclass template(ShutItModule):\n\n\tdef is_installed(self, shutit):\n\t\treturn False'

	# config section - this must be done first, as it collates the config
	# items that can be referenced later
	templatemodule += '''

	def get_config(self, shutit):
		# CONFIGURATION
		# shutit.get_config(module_id,option,default=None,boolean=False)
		#                                    - Get configuration value, boolean indicates whether the item is
		#                                      a boolean type, eg get the config with:
		# shutit.get_config(self.module_id, 'myconfig', default='a value')
		#                                      and reference in your code with:
		# shutit.cfg[self.module_id]['myconfig']'''
	if shutitfile_representation['shutitfile']['module_id']:
		module_id = shutitfile_representation['shutitfile']['module_id']
	else:
		# If the total number of modules is more than 1, then we want to number these modules.
		if total > 1:
			module_id = '%s.%s.%s_%s' % (skel_domain, skel_module_name, skel_module_name, str(order))
		else:
			module_id = '%s.%s.%s' % (skel_domain, skel_module_name, skel_module_name)

	build     = ''
	for item in shutitfile_representation['shutitfile']['config']:
		build += handle_shutitfile_config_line(item)
	if build:
		templatemodule += '\n\t\t' + build
	templatemodule += '\n\t\treturn True'


	# build
	build        = ''
	numpushes    = 0
	numlogins    = 0
	ifdepth      = 0
	wgetgot      = False
	current_note = ''
	# section is the section of the shutitfile we're in. Default is 'build', but there are also a few others.
	section   = 'build'
	for item in shutitfile_representation['shutitfile']['script']:
		section = shutitfile_get_section(item[0], section)
		if section == 'build':
			ret = handle_shutitfile_script_line(item, numpushes, wgetgot, numlogins, ifdepth, current_note)
			build        += ret[0]
			numpushes    =  ret[1]
			wgetgot      =  ret[2]
			numlogins    =  ret[3]
			ifdepth      =  ret[4]
			current_note =  ret[5]
	templatemodule += shutit_util._build_section + build
	while numpushes > 0:
		templatemodule += '''\n\t\tshutit.send('popd')'''
		numpushes -= 1
	while numlogins > 0:
		templatemodule += '''\n\t\tshutit.logout()'''
		numlogins -= 1
	if ifdepth != 0:
		shutit.fail('Unbalanced IFs in ' + section + ' section')
	templatemodule += '\n\t\treturn True'

	# finalize section
	finalize = ''
	for line in shutitfile_representation['shutitfile']['onbuild']:
		finalize += '\n\n\t\tshutit.send(\'' + line + ')\''
	templatemodule += '\n\n\tdef finalize(self, shutit):' + finalize + '\n\t\treturn True'

	# test section
	build          = ''
	templatemodule += '\n\n\tdef test(self, shutit):'
	numpushes      = 0
	numlogins      = 0
	ifdepth        = 0
	current_note   = ''
	for item in shutitfile_representation['shutitfile']['script']:
		section = shutitfile_get_section(item[0], section)
		if section == 'test':
			ret = handle_shutitfile_script_line(item, numpushes, wgetgot, numlogins, ifdepth, current_note)
			build        += ret[0]
			numpushes    =  ret[1]
			wgetgot      =  ret[2]
			numlogins    =  ret[3]
			ifdepth      =  ret[4]
			current_note =  ret[5]
	if build:
		templatemodule += '\n\t\t' + build
	while numpushes > 0:
		templatemodule += """\n\t\tshutit.send('popd')"""
		numpushes      -= 1
	while numlogins > 0:
		templatemodule += '''\n\t\tshutit.logout()'''
		numlogins -= 1
	templatemodule += '\n\t\treturn True'

	# isinstalled section
	build          = ''
	templatemodule += '\n\n\tdef is_installed(self, shutit):'
	numpushes      = 0
	numlogins      = 0
	ifdepth        = 0
	current_note   = ''
	for item in shutitfile_representation['shutitfile']['script']:
		section = shutitfile_get_section(item[0], section)
		if section == 'isinstalled':
			ret = handle_shutitfile_script_line(item, numpushes, wgetgot, numlogins, ifdepth, current_note)
			build        += ret[0]
			numpushes    =  ret[1]
			wgetgot      =  ret[2]
			numlogins    =  ret[3]
			ifdepth      =  ret[4]
			current_note =  ret[5]
	if build:
		templatemodule += '\n\t\t' + build
	while numpushes > 0:
		templatemodule += """\n\t\tshutit.send('popd')"""
		numpushes      -= 1
	while numlogins > 0:
		templatemodule += '''\n\t\tshutit.logout()'''
		numlogins -= 1
	if ifdepth != 0:
		shutit.fail('Unbalanced IFs in ' + section + ' section')
	templatemodule += '\n\t\treturn False'

	# start section
	build          = ''
	templatemodule += '\n\n\tdef start(self, shutit):'
	numpushes      = 0
	numlogins      = 0
	ifdepth        = 0
	current_note   = ''
	for item in shutitfile_representation['shutitfile']['script']:
		section = shutitfile_get_section(item[0], section)
		if section == 'start':
			ret = handle_shutitfile_script_line(item, numpushes, wgetgot, numlogins, ifdepth, current_note)
			build        += ret[0]
			numpushes    =  ret[1]
			wgetgot      =  ret[2]
			numlogins    =  ret[3]
			ifdepth      =  ret[4]
			current_note =  ret[5]
	if build:
		templatemodule += '\n\t\t' + build
	while numpushes > 0:
		templatemodule += """\n\t\tshutit.send('popd')"""
		numpushes      -= 1
	while numlogins > 0:
		templatemodule += '''\n\t\tshutit.logout()'''
		numlogins -= 1
	if ifdepth != 0:
		shutit.fail('Unbalanced IFs in ' + section + ' section')
	templatemodule += '\n\t\treturn True'

	# stop section
	templatemodule += '\n\n\tdef stop(self, shutit):'
	build          = ''
	numpushes      = 0
	numlogins      = 0
	ifdepth        = 0
	current_note   = ''
	for item in shutitfile_representation['shutitfile']['script']:
		section = shutitfile_get_section(item[0], section)
		if section == 'stop':
			ret = handle_shutitfile_script_line(item, numpushes, wgetgot, numlogins, ifdepth, current_note)
			build        += ret[0]
			numpushes    =  ret[1]
			wgetgot      =  ret[2]
			numlogins    =  ret[3]
			ifdepth      =  ret[4]
			current_note =  ret[5]
	if build:
		templatemodule += '\n\t\t' + build
	while numpushes > 0:
		templatemodule += """\n\t\tshutit.send('popd')"""
		numpushes      -= 1
	while numlogins > 0:
		templatemodule += '''\n\t\tshutit.logout()'''
		numlogins -= 1
	if ifdepth != 0:
		shutit.fail('Unbalanced IFs in ' + section + ' section')
	templatemodule += '\n\t\treturn True'

	# dependencies section
	shutitfile_depends = []
	for item in shutitfile_representation['shutitfile']['depends']:
		shutitfile_depends.append(item[1])
	if len(shutitfile_depends):
		depends = "'" + skel_depends + "','" + "','".join(shutitfile_depends) + "'"
	else:
		depends = "'" + skel_depends + "'"
	
	if shutitfile_representation['shutitfile']['default_include'] == 'false':
		default_include = 'no'
	elif shutitfile_representation['shutitfile']['default_include'] == 'true':
		default_include = 'yes'
	else:
		shutit.fail('Unrecognised DEFAULT_INCLUDE - must be true/false: ' + shutitfile_representation['shutitfile']['default_include'])
	return templatemodule, module_id, depends, default_include


def process_shutitfile(shutitfile_contents):
	shutit = shutit_global.shutit
	# Wipe the command as we expect one in the file.
	shutitfile_representation = {'shutitfile': {}}
	shutitfile_representation['shutitfile']['cmd']             = ''
	shutitfile_representation['shutitfile']['maintainer']      = ''
	shutitfile_representation['shutitfile']['description']     = ''
	shutitfile_representation['shutitfile']['module_id']       = ''
	shutitfile_representation['shutitfile']['script']          = []
	shutitfile_representation['shutitfile']['config']          = []
	shutitfile_representation['shutitfile']['onbuild']         = []
	shutitfile_representation['shutitfile']['volume']          = []
	shutitfile_representation['shutitfile']['expose']          = []
	shutitfile_representation['shutitfile']['entrypoint']      = []
	shutitfile_representation['shutitfile']['env']             = []
	shutitfile_representation['shutitfile']['depends']         = []
	shutitfile_representation['shutitfile']['delivery']        = []
	shutitfile_representation['shutitfile']['base_image']      = []
	# Whether to build this module by default (defaults to 'yes/true'
	shutitfile_representation['shutitfile']['default_include'] = 'true'
	shutitfile_list, ok = parse_shutitfile(shutitfile_contents)
	if not ok:
		return [], False
	# Set defaults from given shutitfile
	last_shutitfile_command = ''
	shutitfile_state = 'NONE'
	inline_script = ''
	for item in shutitfile_list:
		# These items are not order-dependent and don't affect the build, so we collect them here:
		shutitfile_command = item[0].upper()
		# List of handled shutitfile_commands
		if shutitfile_state != 'SCRIPT_DURING':
			assert shutitfile_command in ('SCRIPT_END','SCRIPT_BEGIN','SCRIPT_END','FROM','ONBUILD','VOLUME','DESCRIPTION','MAINTAINER','EXPOSE','ENTRYPOINT','CMD','USER','LOGIN','LOGOUT','GET_PASSWORD','ENV','RUN','SEND','ASSERT_OUTPUT','PAUSE_POINT','EXPECT','EXPECT_MULTI','EXPECT_REACT','UNTIL','ADD','COPY','WORKDIR','COMMENT','NOTE','INSTALL','REMOVE','DEPENDS','DELIVERY','MODULE_ID','REPLACE_LINE','START_BEGIN','START_END','STOP_BEGIN','STOP_END','TEST_BEGIN','TEST_END','BUILD_BEGIN','BUILD_END','ISINSTALLED_BEGIN','ISINSTALLED_END','IF','IF_NOT','ELIF_NOT','ELIF','ELSE','ENDIF','COMMIT','PUSH','DEFAULT_INCLUDE','LOG','CONFIG','CONFIG_SECRET','QUIT','STORE_RUN'), '%r is not a handled ShutItFile command' % shutitfile_command
		if shutitfile_command != 'SCRIPT_END' and shutitfile_state == 'SCRIPT_DURING':
			inline_script += '\n' + ' '.join(item)
		elif shutitfile_command == 'SCRIPT_BEGIN':
			shutitfile_state = 'SCRIPT_DURING'
		elif shutitfile_command == 'SCRIPT_END':
			shutitfile_representation['shutitfile']['script'].append(['RUN_SCRIPT', inline_script])
			shutitfile_state = 'NONE'
			inline_script = ''
		elif shutitfile_command == 'FROM':
			if shutitfile_representation['shutitfile']['base_image'] == []:
				shutitfile_representation['shutitfile']['base_image'] = item[1]
				shutit.shutitfile['base_image'] = item[1]
			else:
				print 'Ignoring FROM line as this it has already been set.'
		elif shutitfile_command == 'ONBUILD':
			# TESTED? NO
			# Maps to finalize :) - can we have more than one of these? assume yes
			# This contains within it one of the above commands, so we need to abstract this out.
			shutitfile_representation['shutitfile']['onbuild'].append(item[1])
		elif shutitfile_command == 'MAINTAINER':
			shutitfile_representation['shutitfile']['maintainer'] = item[1]
		elif shutitfile_command == 'DESCRIPTION':
			shutitfile_representation['shutitfile']['description'] = item[1]
		elif shutitfile_command == 'VOLUME':
			# TESTED? NO
			# Put in the run.sh.
			try:
				shutitfile_representation['shutitfile']['volume'].append(' '.join(json.loads(item[1])))
			except Exception:
				shutitfile_representation['shutitfile']['volume'].append(item[1])
		elif shutitfile_command == 'EXPOSE':
			# TESTED? NO
			# Put in the run.sh.
			shutitfile_representation['shutitfile']['expose'].append(item[1])
		elif shutitfile_command == 'ENTRYPOINT':
			# TESTED? NO
			# Put in the run.sh? Yes, if it exists it goes at the front of cmd
			try:
				shutitfile_representation['shutitfile']['entrypoint'] = ' '.join(json.loads(item[1]))
			except Exception:
				shutitfile_representation['shutitfile']['entrypoint'] = item[1]
		elif shutitfile_command == 'CMD':
			# TESTED? NO
			# Put in the run.sh
			try:
				shutitfile_representation['shutitfile']['cmd'] = ' '.join(json.loads(item[1]))
			except Exception:
				shutitfile_representation['shutitfile']['cmd'] = item[1]
		# Other items to be run through sequentially (as they are part of the script)
		elif shutitfile_command == 'GET_PASSWORD':
			# If we are directed to get the password, change the previous directive internally.
			if last_shutitfile_command not in ('LOGIN','USER'):
				shutit.fail('GET_PASSWORD line not after a USER or LOGIN line: ' + shutitfile_command + ' ' + item[1])
			if last_shutitfile_command in ('LOGIN','USER'):
				if last_shutitfile_command == 'LOGIN':
					shutitfile_representation['shutitfile']['script'][-1][0] = 'LOGIN_WITH_PASSWORD'
				elif last_shutitfile_command == 'USER':
					shutitfile_representation['shutitfile']['script'][-1][0] = 'USER_WITH_PASSWORD'
				shutitfile_representation['shutitfile']['script'][-1].append(item[1])
		elif shutitfile_command == 'ENV':
			# Put in the run.sh.
			shutitfile_representation['shutitfile']['script'].append([shutitfile_command, item[1]])
			# Set in the build
			shutitfile_representation['shutitfile']['env'].append(item[1])
		elif shutitfile_command in ('RUN','SEND'):
			# Only handle simple commands for now and ignore the fact that shutitfiles run with /bin/sh -c rather than bash.
			try:
				shutitfile_representation['shutitfile']['script'].append([shutitfile_command, ' '.join(json.loads(item[1]))])
			except Exception:
				shutitfile_representation['shutitfile']['script'].append([shutitfile_command, item[1]])
		elif shutitfile_command == 'ASSERT_OUTPUT':
			if last_shutitfile_command not in ('RUN','SEND'):
				shutit.fail('ASSERT_OUTPUT line not after a RUN/SEND line: ' + shutitfile_command + ' ' + item[1])
			shutitfile_representation['shutitfile']['script'][-1][0] = 'ASSERT_OUTPUT_SEND'
			shutitfile_representation['shutitfile']['script'].append([shutitfile_command, item[1]])
		elif shutitfile_command == 'EXPECT':
			if last_shutitfile_command not in ('RUN','SEND','GET_PASSWORD'):
				shutit.fail('EXPECT line not after a RUN, SEND or GET_PASSWORD line: ' + shutitfile_command + ' ' + item[1])
			shutitfile_representation['shutitfile']['script'][-1][0] = 'SEND_EXPECT'
			shutitfile_representation['shutitfile']['script'].append([shutitfile_command, item[1]])
		elif shutitfile_command == 'EXPECT_MULTI':
			if last_shutitfile_command not in ('RUN','SEND','GET_PASSWORD'):
				shutit.fail('EXPECT_MULTI line not after a RUN, SEND or GET_PASSWORD line: ' + shutitfile_command + ' ' + item[1])
			shutitfile_representation['shutitfile']['script'][-1][0] = 'SEND_EXPECT_MULTI'
			shutitfile_representation['shutitfile']['script'].append([shutitfile_command, item[1]])
		elif shutitfile_command == 'EXPECT_REACT':
			if last_shutitfile_command not in ('RUN','SEND','GET_PASSWORD'):
				shutit.fail('EXPECT_REACT line not after a RUN, SEND or GET_PASSWORD line: ' + shutitfile_command + ' ' + item[1])
			shutitfile_representation['shutitfile']['script'][-1][0] = 'SEND_EXPECT_REACT'
			shutitfile_representation['shutitfile']['script'].append([shutitfile_command, item[1]])
		elif shutitfile_command == 'UNTIL':
			if last_shutitfile_command not in ('RUN','SEND'):
				shutit.fail('UNTIL line not after a RUN, SEND: ' + shutitfile_command + ' ' + item[1])
			shutitfile_representation['shutitfile']['script'][-1][0] = 'SEND_UNTIL'
			shutitfile_representation['shutitfile']['script'].append([shutitfile_command, item[1]])
		elif shutitfile_command == 'DEPENDS':
			shutitfile_representation['shutitfile']['depends'].append([shutitfile_command, item[1]])
		elif shutitfile_command == 'DELIVERY':
			shutitfile_representation['shutitfile']['delivery'].append([shutitfile_command, item[1]])
		elif shutitfile_command == 'MODULE_ID':
			# Only one item allowed.
			shutitfile_representation['shutitfile']['module_id'] = item[1]
		elif shutitfile_command == 'DEFAULT_INCLUDE':
			shutitfile_representation['shutitfile']['default_include'] = item[1]
		elif shutitfile_command == 'CONFIG':
			shutitfile_representation['shutitfile']['config'].append([shutitfile_command, item[1]])
		elif shutitfile_command == 'CONFIG_SECRET':
			shutitfile_representation['shutitfile']['config'].append([shutitfile_command, item[1]])
		elif shutitfile_command in ('ADD','COPY','WORKDIR','COMMENT','INSTALL','REMOVE','REPLACE_LINE','LOG','COMMIT','PUSH','QUIT','PAUSE_POINT','USER','LOGIN','LOGOUT'):
			shutitfile_representation['shutitfile']['script'].append([shutitfile_command, item[1]])
		elif shutitfile_command in ('IF','IF_NOT','ELIF_NOT','ELIF','STORE_RUN'):
			# Parser retrieved two items here
			shutitfile_representation['shutitfile']['script'].append([shutitfile_command, item[1], item[2]])
		elif shutitfile_command in ('ELSE','ENDIF','START_BEGIN','START_END','STOP_BEGIN','STOP_END','TEST_BEGIN','TEST_END','BUILD_BEGIN','BUILD_END','ISINSTALLED_BEGIN','ISINSTALLED_END'):
			shutitfile_representation['shutitfile']['script'].append([shutitfile_command])
		else:
			shutit.fail('shutitfile command: ' + shutitfile_command + ' not processed')
		last_shutitfile_command = shutitfile_command
	return shutitfile_representation, True


def handle_shutitfile_config_line(line):
	shutitfile_command = line[0].upper()
	shutit             = shutit_global.shutit
	build              = ''
	numtabs            = 2
	assert shutitfile_command in ('CONFIG','CONFIG_SECRET'), '%r is not a handled config command' % shutitfile_command
	if shutitfile_command in ('CONFIG','CONFIG_SECRET'):
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) in (dict,list)
		if shutitfile_command == 'CONFIG':
			secret_str = 'False'
		elif shutitfile_command == 'CONFIG_SECRET':
			secret_str = 'True'
		if type(shutitfile_args) == list:
			assert len(shutitfile_args) in (1,2), ''
			cfg_name = shutitfile_args[0]
			if len(shutitfile_args) == 1:
				build += """\n""" + numtabs*'\t' + """shutit.get_config(self.module_id,'""" + cfg_name + """',secret=""" + secret_str + """)"""
			elif len(shutitfile_args) == 2:
				cfg_default = shutitfile_args[1]
				build += """\n""" + numtabs*'\t' + """shutit.get_config(self.module_id,'""" + cfg_name + """',default='""" + cfg_default + """',secret=""" + secret_str + """)"""
	return build


def handle_shutitfile_script_line(line, numpushes, wgetgot, numlogins, ifdepth, current_note):
	shutitfile_command = line[0].upper()
	shutit = shutit_global.shutit
	build  = ''
	numtabs = 2 + ifdepth
	assert shutitfile_command in ('RUN','SEND','SEND_EXPECT','SEND_EXPECT_MULTI','EXPECT_REACT','SEND_EXPECT_REACT','SEND_UNTIL','UNTIL','UNTIL','ASSERT_OUTPUT_SEND','ASSERT_OUTPUT','PAUSE_POINT','EXPECT','EXPECT_MULTI','LOGIN','USER','LOGOUT','GET_AND_SEND_PASSWORD','LOGIN_WITH_PASSWORD','USER_WITH_PASSWORD','WORKDIR','COPY','ADD','ENV','INSTALL','REMOVE','COMMENT','NOTE','IF','ELSE','ELIF','IF_NOT','ELIF_NOT','ENDIF','RUN_SCRIPT','SCRIPT_BEGIN','START_BEGIN','START_END','STOP_BEGIN','STOP_END','TEST_BEGIN','TEST_END','BUILD_BEGIN','BUILD_END','ISINSTALLED_BEGIN','ISINSTALLED_END','COMMIT','PUSH','REPLACE_LINE','LOG','QUIT','STORE_RUN'), '%r is not a handled script command' % shutitfile_command
	if shutitfile_command in ('RUN','SEND'):
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == list
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """\n""" + numtabs*'\t' + """shutit.send('''""" + cmd + """''',note='''""" + current_note + """''')"""
		current_note = ''
	elif shutitfile_command == 'SEND_EXPECT':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == list
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """\n""" + numtabs*'\t' + """shutit.send('''""" + cmd + """''',note='''""" + current_note + """''',expect="""
		current_note = ''
	elif shutitfile_command == 'EXPECT':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == list
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """'''""" + cmd + """''')"""
	elif shutitfile_command == 'SEND_EXPECT_MULTI':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == list
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """\n""" + numtabs*'\t' + """shutit.multisend('''""" + cmd + """''',"""
		current_note = ''
	elif shutitfile_command == 'EXPECT_MULTI':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == dict
		multi_dict = str(shutitfile_args)
		build += multi_dict + """,note='''""" + current_note + """''')"""
	elif shutitfile_command == 'SEND_EXPECT_REACT':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == list
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """\n""" + numtabs*'\t' + """shutit.send('''""" + cmd + """''',note='''""" + current_note + """''',follow_on_commands="""
		current_note = ''
	elif shutitfile_command == 'EXPECT_REACT':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == dict
		multi_dict = str(shutitfile_args)
		# We don't check exit here, as reactions will often have failing commands.
		build += multi_dict + ",check_exit=False)"
	elif shutitfile_command == 'SEND_UNTIL':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == list
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """\n""" + numtabs*'\t' + """shutit.send_until('''""" + cmd + """''',note='''""" + current_note + """'''"""
		current_note = ''
	elif shutitfile_command == 'UNTIL':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == list
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """'''""" + cmd + """''')"""
	elif shutitfile_command == 'PAUSE_POINT':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == list
		msg = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """\n""" + numtabs*'\t' + """shutit.pause_point('''""" + msg + """''')"""
	elif shutitfile_command == 'QUIT':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == list
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """\n""" + numtabs*'\t' + """shutit.fail('''""" + cmd + """''')"""
	elif shutitfile_command == 'LOGOUT':
		build += """\n""" + numtabs*'\t' + """shutit.logout(note='''""" + current_note + """''')"""
		current_note = ''
		numlogins -= 1
	elif shutitfile_command == 'ASSERT_OUTPUT_SEND':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == list
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """\n""" + numtabs*'\t' + """_cmd = '''""" + cmd + """'''\n\t\t_output = shutit.send_and_get_output('''""" + cmd + """''',note='''""" + current_note + """''')\n\t\tif _output != """
		current_note = ''
	elif shutitfile_command == 'ASSERT_OUTPUT':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == list
		expected_output = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """'''""" + expected_output + """''':\n""" + numtabs*'\t' + """\tshutit.pause_point('''Output of: ''' + _cmd + ''' was: ''' + _output + ''' It should be: """ + expected_output + """''')"""
	elif shutitfile_command == 'LOGIN':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == list
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """\n""" + numtabs*'\t' + """shutit.login(command='""" + cmd + """',note='''""" + current_note + """''')"""
		current_note = ''
		numlogins += 1
	elif shutitfile_command == 'USER':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == list
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """\n""" + numtabs*'\t' + """shutit.login(user='""" + cmd + """',note='''""" + current_note + """''')"""
		current_note = ''
		numlogins += 1
	elif shutitfile_command == 'GET_AND_SEND_PASSWORD':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == list
		msg = scan_text(' '.join(shutitfile_args)) + '\n'
		build += """\n""" + numtabs*'\t' + """_password = shutit.get_input('''""" + msg + """''',ispass=True)"""
		build += """\n""" + numtabs*'\t' + """shutit.send(_password,echo=False,check_exit=False,note='''""" + current_note + """''')"""
		current_note = ''
	elif shutitfile_command == 'LOGIN_WITH_PASSWORD':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == list
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		msg = scan_text(line[2]) + '\n'
		build += """\n""" + numtabs*'\t' + """_password = shutit.get_input('''""" + msg + """''',ispass=True)"""
		build += """\n""" + numtabs*'\t' + """shutit.login(command='""" + cmd + """', password=_password,note='''""" + current_note + """''')"""
		current_note = ''
	elif shutitfile_command == 'USER_WITH_PASSWORD':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == list
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		msg = scan_text(line[2]) + '\n'
		build += """\n""" + numtabs*'\t' + """_password = shutit.get_input('''""" + msg + """''',ispass=True)"""
		build += """\n""" + numtabs*'\t' + """shutit.login(user='""" + cmd + """', password=_password,note='''""" + current_note + """''')"""
		current_note = ''
	elif shutitfile_command == 'WORKDIR':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == list
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """\n""" + numtabs*'\t' + """shutit.send('''pushd """ + cmd + """''',echo=False,note='''""" + current_note + """''')"""
		current_note = ''
		numpushes += 1
	elif shutitfile_command == 'COPY' or shutitfile_command == 'ADD':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == list
		# The <src> path must be inside the context of the build; you cannot COPY ../something /something, because the first step of a docker build is to send the context directory (and subdirectories) to the docker daemon.
		if shutitfile_args[0][0:1] == '..' or shutitfile_args[0][0] == '/' or shutitfile_args[0][0] == '~':
			shutit.fail('Invalid line: ' + str(shutitfile_args) + ' file must be in local subdirectory')
		if shutitfile_args[1][-1] == '/':
			# Dir we're COPYing or ADDing to
			destdir  = scan_text(shutitfile_args[1])
			# File/dir we're COPYing or ADDing from
			fromfile = scan_text(shutitfile_args[0])
			# Final file/dir
			outfile  = destdir + fromfile
			if os.path.isfile(fromfile):
				outfiledir = os.path.dirname(fromfile)
				build += """\n""" + numtabs*'\t' + """shutit.send('''mkdir -p """ + destdir + """/""" + outfiledir + """''',note='''""" + current_note + """''')"""
				current_note = ''
			elif os.path.isdir(fromfile):
				build += """\n""" + numtabs*'\t' + """shutit.send('''mkdir -p """ + destdir + fromfile + """''',note='''""" + current_note + """''')"""
				current_note = ''
		else:
			outfile = shutitfile_args[1]
		# If this is something we have to wget:
		if shutitfile_command == 'ADD' and urlparse.urlparse(shutitfile_args[0])[0] != '':
			if not wgetgot:
				build += """\n""" + numtabs*'\t' + """shutit.install('wget')"""
				wgetgot = True
			if shutitfile_args[1][-1] == '/':
				destdir = scan_text(destdir[0:-1])
				outpath = scan_text(urlparse.urlparse(shutitfile_args[0])[2])
				outpathdir = os.path.dirname(outpath)
				build += """\n""" + numtabs*'\t' + """shutit.send('''mkdir -p """ + destdir + outpathdir + """''')"""
				build += """\n""" + numtabs*'\t' + """shutit.send('''wget -O """ + destdir + outpath + ' ' + shutitfile_args[0] + """''',note='''""" + current_note + """''')"""
				current_note = ''
			else:
				outpath  = scan_text(shutitfile_args[1])
				destdir  = scan_text(os.path.dirname(shutitfile_args[1]))
				build += """\n""" + numtabs*'\t' + """shutit.send('''mkdir -p """ + destdir + """''')"""
				build += """\n""" + numtabs*'\t' + """shutit.send('''wget -O """ + outpath + ' ' + shutitfile_args[0] + """''',note='''""" + current_note + """''')"""
				current_note = ''
		else:
			# From the local filesystem on construction:
			localfile = scan_text(shutitfile_args[0])
			# Local file location on build:
			buildstagefile = scan_text('context/' + shutitfile_args[0])
			#if localfile[-4:] == '.tar':
			#	build += """\n\t\tshutit.send_file('""" + outfile + '/' + localfile + """')"""
			#elif localfile[-4:] == '.bz2':
			#elif localfile[-3:] == '.gz':
			#elif localfile[-3:] == '.xz':
			if os.path.isdir(localfile):
				build += """\n""" + numtabs*"""\t""" + """shutit.send_host_dir('''""" + outfile + """''', '''""" + buildstagefile + """''',note='''""" + current_note + """''')"""
				current_note = ''
			else:
				build += """\n""" + numtabs*"""\t""" + """shutit.send_host_file('''""" + outfile + """''', '''""" + buildstagefile + """''',note='''""" + current_note + """''')"""
				current_note = ''
	elif shutitfile_command == 'ENV':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == dict
		for k,v in shutitfile_args.iteritems():
			k = scan_text(k)
			v = scan_text(v)
			build += """\n""" + numtabs*"""\t""" + """shutit.send('''export """ + k + '=' + v + """''',note='''""" + current_note + """''')"""
			current_note = ''
	elif shutitfile_command == 'INSTALL':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == list
		build += """\n""" + numtabs*"""\t""" + """shutit.install('''""" + scan_text(' '.join(shutitfile_args)) + """''',note='''""" + current_note + """''')"""
		current_note = ''
	elif shutitfile_command == 'REMOVE':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == list
		build += """\n""" + numtabs*'\t' + """shutit.remove('''""" + scan_text(' '.join(shutitfile_args)) + """''',note='''""" + current_note + """''')"""
		current_note = ''
	elif shutitfile_command in ('COMMENT','NOTE'):
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == list
		# COMMENT line should come before the next appropriate line where it can be used, where it is 'consumed' in a note.
		build += """\n""" + numtabs*"""\t""" + """# """ + scan_text(' '.join(shutitfile_args))
		current_note += scan_text(' '.join(shutitfile_args))
	elif shutitfile_command in ('IF','IF_NOT'):
		subcommand      = scan_text(line[1])
		subcommand_args = scan_text(' '.join(line[2:]))
		if subcommand == 'FILE_EXISTS':
			statement = """shutit.file_exists('''""" + subcommand_args + """''',directory=None,note='''""" + current_note + """''')"""
			current_note = ''
		elif subcommand == 'INSTALL_TYPE':
			statement = """shutit.get_current_shutit_pexpect_session_environment(note='''""" + current_note + """''').install_type == '''""" + subcommand_args + """'''"""
			current_note = ''
		elif subcommand == 'RUN':
			statement = """shutit.send_and_return_status('''""" + subcommand_args + """''',check_exit=False,note='''""" + current_note + """''')"""
			current_note = ''
		else:
			shutit.fail('subcommand: ' + subcommand + ' not handled')
		if shutitfile_command == 'IF':
			build += """\n""" + numtabs*"""\t""" + """if """ + statement + """:"""
		elif shutitfile_command == 'IF_NOT':
			build += """\n""" + numtabs*"""\t""" + """if not """ + statement + """:"""
		ifdepth += 1
	elif shutitfile_command == 'ELSE':
		if shutitfile_command == 'ELSE':
			build += """\n""" + (numtabs-1)*"""\t""" + """else:"""
	elif shutitfile_command in ('ELIF','ELIF_NOT'):
		subcommand      = scan_text(line[1])
		subcommand_args = scan_text(' '.join(line[2:]))
		if subcommand == 'FILE_EXISTS':
			statement = """shutit.file_exists('''""" + subcommand_args + """''',directory=None,note='''""" + current_note + """''')"""
			current_note = ''
		elif subcommand == 'INSTALL_TYPE':
			statement = """shutit.get_current_shutit_pexpect_session_environment(note='''""" + current_note + """''').install_type == '""" + subcommand_args + """'"""
			current_note = ''
		elif subcommand == 'RUN':
			statement = """shutit.send_and_return_status('''""" + subcommand_args + """''',check_exit=False,note='''""" + current_note + """''')"""
			current_note = ''
		else:
			shutit.fail('subcommand: ' + subcommand + ' not handled')
		if shutitfile_command == 'ELIF':
			build += """\n""" + (numtabs-1)*'\t' + '''elif ''' + statement + ''':'''
		elif shutitfile_command == 'ELIF_NOT':
			build += """\n""" + (numtabs-1)*"""\t""" + """elif not """ + statement + """:"""
	elif shutitfile_command == 'ENDIF':
		ifdepth -= 1
	elif shutitfile_command == 'RUN_SCRIPT':
		shutitfile_args    = line[1]
		assert type(shutitfile_args) == str
		script = scan_text(shutitfile_args)
		build += """\n""" + numtabs*"""\t""" + """shutit.run_script('''""" + script + """''',note='''""" + current_note + """''')"""
		current_note = ''
	elif shutitfile_command == 'COMMIT':
		global _default_repo_name
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == list
		assert len(shutitfile_args) == 1
		repo_name = scan_text(shutitfile_args[0])
		if repo_name == _default_repo_name:
			shutit.log('The docker container will be committed with the default repo_name: ' + _default_repo_name + '.\nYou can change this by adding this to the ~/.shutit/config file:\n\n[repository]\nname:yourname\n\nand re-running.',level=logging.WARNING)
		if len(shutitfile_args) == 1:
			build += """\n""" + numtabs*"""\t""" + """shutit.do_repository_work('''""" + repo_name + """''',force=None,tag=True,note='''""" + current_note + """''')"""
			current_note = ''
	elif shutitfile_command == 'PUSH':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == list
		assert len(shutitfile_args) == 1
		assert shutit.repository['user'] != '', 'If you want to push, set the [repository] settings (user,password,email) in your ~/.shutit/config file.'
		repo_name = scan_text(shutitfile_args[0])
		build += """\n""" + numtabs*"""\t""" + """shutit.push_repository('''""" + repo_name + """''',note='''""" + current_note + """''')"""
		current_note = ''
	elif shutitfile_command == 'REPLACE_LINE':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert type(shutitfile_args) == dict
		# TODO: assert existence of these
		line     = scan_text(shutitfile_args['line'])
		filename = scan_text(shutitfile_args['filename'])
		pattern  = scan_text(shutitfile_args['pattern'])
		build += """\n""" + numtabs*'\t' + """shutit.replace_text('''""" + line + """''','''""" + filename + """''',pattern='''""" + pattern + """''',note='''""" + current_note + """''')"""
		current_note = ''
	elif shutitfile_command == 'LOG':
		shutitfile_args    = scan_text(line[1])
		assert type(shutitfile_args) == str and shutitfile_args in ('DEBUG','WARNING','CRITICAL','INFO','ERROR')
		build += """\n""" + numtabs*'\t' + """import logging"""
		build += """\n""" + numtabs*'\t' + """logging.getLogger().setLevel(logging.""" + shutitfile_args + """)"""
	elif shutitfile_command == 'STORE_RUN':
		config_item      = scan_text(line[1])
		command          = scan_text(' '.join(line[2:]))
		build += """\n""" + numtabs*'\t' + """shutit.cfg[self.module_id]['""" + config_item + """'] = shutit.send_and_get_output('''""" + command + """''',note='''""" + current_note + """''')"""
		current_note = ''
	# See shutitfile_get_section
	elif shutitfile_command in ('SCRIPT_BEGIN','START_BEGIN','START_END','STOP_BEGIN','STOP_END','TEST_BEGIN','TEST_END','BUILD_BEGIN','BUILD_END','ISINSTALLED_BEGIN','ISINSTALLED_END'):
		# No action to perform on these lines, but they are legal.
		pass
	else:
		shutit.fail('shutitfile_command: ' + shutitfile_command + ' not handled')
	return build, numpushes, wgetgot, numlogins, ifdepth, current_note


def scan_text(text):
	"""Scan text, and replace items that match shutit's template format, ie:
	{{ shutit.THING }}
	"""
	while True:
		match = re.match("(.*){{ shutit.(.*) }}(.*)$", text)
		if match:
			before = match.group(1)
			name = match.group(2)
			after = match.group(3)
			text = before + """''' + shutit.cfg[self.module_id][\"""" + name + """\"] + '''""" + after
		else:
			break
	return text


# Get the section of the shutitfile we are in.
def shutitfile_get_section(shutitfile_command, current):
	match = re.match(r'^(.*)_(BEGIN|END)$',shutitfile_command)
	if match:
		section = match.group(1)
		stage   = match.group(2)
		if stage == 'BEGIN':
			return section.lower()
		else:
			return 'build'
	return current


