#!/usr/bin/env pythen

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

import logging
import os
import random
import re
import shutil
import sys
try:
	from urllib.parse import urlparse
	from urllib.request import urlopen
except ImportError:
	from urlparse import urlparse
	from urllib2 import urlopen
from six import iteritems
import shutit_global
import shutit_skeleton


def setup_shutitfile_pattern(shutit,
                             skel_path,
                             skel_delivery,
                             skel_pattern,
                             skel_domain,
	                         skel_module_name,
                             skel_vagrant_num_machines,
                             skel_vagrant_machine_prefix,
                             skel_vagrant_ssh_access,
                             skel_vagrant_docker):

	shutit_skeleton_extra_args = ''
	if skel_pattern == 'shutitfile' and skel_delivery == 'vagrant':
		# This is a vagrant build, adjust accordingly.
		skel_pattern = 'vagrant'
		skel_delivery = 'bash'
		if skel_vagrant_num_machines is not None:
			shutit_skeleton_extra_args += ' --vagrant_num_machines ' + skel_vagrant_num_machines
		else:
			shutit_skeleton_extra_args += ' --vagrant_num_machines 3'
		if skel_vagrant_machine_prefix is not None:
			shutit_skeleton_extra_args += ' --vagrant_machine_prefix ' + skel_vagrant_machine_prefix
		else:
			shutit_skeleton_extra_args += ' --vagrant_machine_prefix machine'
		if skel_vagrant_ssh_access is True:
			shutit_skeleton_extra_args += ' --vagrant_ssh_access'
		if skel_vagrant_docker is True:
			shutit_skeleton_extra_args += ' --vagrant_docker'
	if skel_pattern == 'shutitfile' and skel_delivery == 'docker':
		# This is a docker build, adjust accordingly.
		skel_pattern = 'docker'
		skel_delivery = 'docker'
	runsh_filename = skel_path + '/run.sh'
	runsh_file = open(runsh_filename,'w+')
	runsh_file.write('''#!/bin/bash
set -e

MODULE_NAME="''' + skel_module_name + '''"
DIR="/tmp/shutit_built''' + skel_path + '''"
DOMAIN="''' + skel_domain + '''"
DELIVERY="''' + skel_delivery + '''"
PATTERN="''' + skel_pattern + '''"

rm -rf $DIR

shutit skeleton --shutitfile ShutItFile1.sf ShutItFile2.sf --name ${DIR} --domain ${DOMAIN} --delivery ${DELIVERY} --pattern ${PATTERN}''' + shutit_skeleton_extra_args + '''

if [[ ${DELIVERY} == 'bash' ]]
then
	cd $DIR && ./run.sh "$@"
elif [[ ${DELIVERY} == 'docker' ]]
then
	cd $DIR && ./build.sh "$@"
fi''')
	runsh_file.close()
	os.chmod(runsh_filename,0o755)

	# User message
	shutit.log('''# Run:
cd ''' + skel_path + ''' && ./run.sh
# to run.
# Or
# cd ''' + skel_path + ''' && ./run.sh -c
# to run while choosing modules to build. ''',transient=True)

	# ShutItFile1
	shutitfile1_filename = skel_path + '/ShutItFile1.sf'
	shutitfile1_file = open(shutitfile1_filename,'w+')
	shutitfile1_contents = '''# See [here](https://github.com/ianmiell/shutitfile/blob/master/CheatSheet.md) for a cheat sheet.
# See [here](https://github.com/ianmiell/shutitfile/examples) for examples.'''

	shutitfile1_file.write(shutitfile1_contents)
	shutitfile1_file.close()

	# ShutItFile2.sf
	shutitfile2_filename = skel_path + '/ShutItFile2.sf'
	shutitfile2_file = open(shutitfile2_filename,'w+')
	shutitfile2_contents = '''# See [here](https://github.com/ianmiell/shutitfile/blob/master/CheatSheet.md) for a cheat sheet.
# See [here](https://github.com/ianmiell/shutitfile/examples) for examples.'''
	shutitfile2_file.write(shutitfile2_contents)
	shutitfile2_file.close()



# Parses the shutitfile (passed in as a string)
# and info to extract, and returns a list with the information in a more canonical form, still ordered.
def parse_shutitfile(contents):
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
				full_line += line
				if re.match(r"^IF_NOT+[\s]+([A-Z_]+)[\s]+(.*)$", full_line):
					m = re.match(r"^IF_NOT+[\s]+([A-Z_]+)[\s]+(.*)$", full_line)
					ret.append(['IF_NOT',m.group(1),m.group(2)])
				elif re.match(r"^STORE_RUN+[\s]+([a-zA-Z0-9_]+)[\s]+(.*)$", full_line):
					m = re.match(r"^STORE_RUN+[\s]+([a-zA-Z0-9_]+)[\s]+(.*)$", full_line)
					ret.append(['STORE_RUN',m.group(1),m.group(2)])
				elif re.match(r"^ELIF_NOT[\s]+([A-Z_]+)[\s]+(.*)$", full_line):
					m = re.match(r"^ELIF_NOT[\s]+([A-Z_]+)[\s]+(.*)$", full_line)
					ret.append(['ELIF_NOT',m.group(1),m.group(2)])
				elif re.match(r"^IF[\s]+([A-Z_]+)[\s]+(.*)$", full_line):
					m = re.match(r"^IF[\s]+([A-Z_]+)[\s]+(.*)$", full_line)
					ret.append(['IF',m.group(1),m.group(2)])
				elif re.match(r"^ELIF[\s]+([A-Z_]+)[\s]+(.*)$", full_line):
					m = re.match(r"^ELIF[\s]+([A-Z_]+)[\s]+(.*)$", full_line)
					ret.append(['ELIF',m.group(1),m.group(2)])
				elif re.match("^ELSE$", full_line):
					ret.append(['ELSE'])
				elif re.match("^ENDIF$", full_line):
					ret.append(['ENDIF'])
				elif re.match(r"^([A-Za-z_]+)[\s]*(.*)$", full_line):
					m = re.match(r"^[\s]*([A-Za-z_]+)[\s]*(.*)$", full_line)
					ret.append([m.group(1), m.group(2)])
				elif re.match("^#(.*)$", full_line):
					# Comments should be added with 'COMMENT a comment'
					pass
				else:
					full_line_split = ''.join((full_line[:10000].split()))
					full_line_strings = re.findall("[^\x00-\x1F\x7F-\xFF]", full_line_split)
					print('FAILED TO PARSE: ' + full_line_strings[:30] + '[...]')
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
		assert isinstance(ret, list)
	else:
		ret = args_str.split()
		# if all the items have a = in them, then return a dict of nv pairs
	nv_pairs = True
	for item in ret:
		if item.find('=') < 0:
			nv_pairs = False
	if nv_pairs:
		d = {}
		for item in ret:
			item_nv = item.split('=')
			d.update({item_nv[0]:item_nv[1]})
		ret = d
	return ret



# Takes a shutitfile filename and returns represention of that Dockerfile as a ShutIt module snippets
def shutitfile_to_shutit_module(shutit,
                                skel_shutitfile,
                                skel_path,
                                skel_domain,
                                skel_module_name,
                                skel_domain_hash,
                                skel_delivery,
                                skel_depends,
                                order,
	                            total,
	                            skel_module_modifier):

	if not os.path.exists(skel_shutitfile):
		if urlparse(skel_shutitfile)[0] == '':
			shutit.fail('Dockerfile/ShutItFile "' + skel_shutitfile + '" must exist')
		shutitfile_contents = urlopen(skel_shutitfile).read()
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
			else:
				# Copy any other files that do not already exist on the target
				os.system('cp -r -n ' + shutitfile_dirname + '/* ' + skel_path)
		# Change to this context
		os.chdir(shutitfile_dirname)

	# Process the shutitfile
	shutitfile_representation, ok = shutit_skeleton.process_shutitfile(shutit, shutitfile_contents)
	if not ok:
		return '', '', '', '', '', False

	# Check the shutitfile representation
	check_shutitfile_representation(shutit, shutitfile_representation, skel_delivery)

	# Get the shutit module as a string
	sections, module_id, _, depends, default_include = generate_shutit_module_sections(shutit, shutitfile_representation, skel_domain, skel_module_name, skel_module_modifier, skel_shutitfile, skel_depends, order, total)
	if module_id == skel_module_name:
		module_id = skel_domain + """.""" + skel_module_name + skel_module_modifier

	# Final section
	final_section  = """

def module():
	return """ + skel_module_name + skel_module_modifier + """(
		'""" + module_id + """', """ + skel_domain_hash + str(order * 0.0001) + str(random.randint(1,999)) + """,
		description='""" + shutitfile_representation['shutitfile']['description'] + """',
		delivery_methods=[('""" + skel_delivery + """')],
		maintainer='""" + shutitfile_representation['shutitfile']['maintainer'] + """',
		depends=[""" + depends + """]
	)
"""
	sections.update({'final_section':final_section})

	# Return program to main shutit_dir
	if shutitfile_dirname:
		os.chdir(sys.path[0])
	return sections, module_id, skel_module_name, default_include, ok



def check_shutitfile_representation(shutit, shutitfile_representation, skel_delivery):
	# delivery directives
	# Only allow one type of delivery
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

	if skel_delivery not in shutit_global.shutit_global_object.allowed_delivery_methods:
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



def generate_shutit_module_sections(shutit,
                                    shutitfile_representation,
                                    skel_domain,
	                                skel_module_name,
                                    skel_module_modifier,
                                    skel_shutitfile,
                                    skel_depends,
                                    order,
                                    total):
	sections = {}
	sections.update({'header_section':'\n# Created from shutitfile: ' + skel_shutitfile + '\n# Maintainer:              ' + shutitfile_representation['shutitfile']['maintainer'] + '\nfrom shutit_module import ShutItModule\n\nclass ' + skel_module_name + skel_module_modifier + '(ShutItModule):\n\n\tdef is_installed(self, shutit):\n\t\treturn False'})

	# config section - this must be done first, as it collates the config
	# items that can be referenced later
	config_section = ''
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
		config_section += '\n\t\t' + build
	sections.update({'config_section':config_section})


	# build
	build        = ''
	numpushes    = 0
	numlogins    = 0
	ifdepth      = 0
	wgetgot      = False
	current_note = ''
	# section is the section of the shutitfile we're in. Default is 'build', but there are also a few others.
	section       = 'build'
	build_section = ''
	for item in shutitfile_representation['shutitfile']['script']:
		section = shutitfile_get_section(item[0], section)
		if section == 'build':
			ret = handle_shutitfile_script_line(shutit, item, numpushes, wgetgot, numlogins, ifdepth, current_note)
			build        += ret[0]
			numpushes    =  ret[1]
			wgetgot      =  ret[2]
			numlogins    =  ret[3]
			ifdepth      =  ret[4]
			current_note =  ret[5]
	build_section += build
	while numpushes > 0:
		build_section += '''\n\t\tshutit.send('popd')'''
		numpushes -= 1
	while numlogins > 0:
		build_section += '''\n\t\tshutit.logout()'''
		numlogins -= 1
	if ifdepth != 0:
		shutit.fail('Unbalanced IFs in ' + section + ' section')
	sections.update({'build_section':build_section})

	# finalize section
	finalize         = ''
	for line in shutitfile_representation['shutitfile']['onbuild']:
		finalize += '\n\n\t\tshutit.send(\'' + line + ')\''
	sections.update({'finalize_section':finalize})

	# test section
	build          = ''
	test_section   = ''
	numpushes      = 0
	numlogins      = 0
	ifdepth        = 0
	current_note   = ''
	for item in shutitfile_representation['shutitfile']['script']:
		section = shutitfile_get_section(item[0], section)
		if section == 'test':
			ret = handle_shutitfile_script_line(shutit, item, numpushes, wgetgot, numlogins, ifdepth, current_note)
			build        += ret[0]
			numpushes    =  ret[1]
			wgetgot      =  ret[2]
			numlogins    =  ret[3]
			ifdepth      =  ret[4]
			current_note =  ret[5]
	if build:
		test_section += '\n\t\t' + build
	while numpushes > 0:
		test_section += """\n\t\tshutit.send('popd')"""
		numpushes      -= 1
	while numlogins > 0:
		test_section += '''\n\t\tshutit.logout()'''
		numlogins -= 1
	sections.update({'test_section':test_section})

	# isinstalled section
	build          = ''
	isinstalled_section = ''
	numpushes      = 0
	numlogins      = 0
	ifdepth        = 0
	current_note   = ''
	for item in shutitfile_representation['shutitfile']['script']:
		section = shutitfile_get_section(item[0], section)
		if section == 'isinstalled':
			ret = handle_shutitfile_script_line(shutit, item, numpushes, wgetgot, numlogins, ifdepth, current_note)
			build        += ret[0]
			numpushes    =  ret[1]
			wgetgot      =  ret[2]
			numlogins    =  ret[3]
			ifdepth      =  ret[4]
			current_note =  ret[5]
	if build:
		isinstalled_section += '\n\t\t' + build
	while numpushes > 0:
		isinstalled_section += """\n\t\tshutit.send('popd')"""
		numpushes      -= 1
	while numlogins > 0:
		isinstalled_section += '''\n\t\tshutit.logout()'''
		numlogins -= 1
	if ifdepth != 0:
		shutit.fail('Unbalanced IFs in ' + section + ' section')
	sections.update({'isinstalled_section':isinstalled_section})

	# start section
	build          = ''
	start_section  = ''
	numpushes      = 0
	numlogins      = 0
	ifdepth        = 0
	current_note   = ''
	for item in shutitfile_representation['shutitfile']['script']:
		section = shutitfile_get_section(item[0], section)
		if section == 'start':
			ret = handle_shutitfile_script_line(shutit, item, numpushes, wgetgot, numlogins, ifdepth, current_note)
			build        += ret[0]
			numpushes    =  ret[1]
			wgetgot      =  ret[2]
			numlogins    =  ret[3]
			ifdepth      =  ret[4]
			current_note =  ret[5]
	if build:
		start_section += '\n\t\t' + build
	while numpushes > 0:
		start_section += """\n\t\tshutit.send('popd')"""
		numpushes      -= 1
	while numlogins > 0:
		start_section += '''\n\t\tshutit.logout()'''
		numlogins -= 1
	if ifdepth != 0:
		shutit.fail('Unbalanced IFs in ' + section + ' section')
	sections.update({'start_section':start_section})

	# stop section
	build          = ''
	stop_section   = ''
	numpushes      = 0
	numlogins      = 0
	ifdepth        = 0
	current_note   = ''
	for item in shutitfile_representation['shutitfile']['script']:
		section = shutitfile_get_section(item[0], section)
		if section == 'stop':
			ret = handle_shutitfile_script_line(shutit, item, numpushes, wgetgot, numlogins, ifdepth, current_note)
			build        += ret[0]
			numpushes    =  ret[1]
			wgetgot      =  ret[2]
			numlogins    =  ret[3]
			ifdepth      =  ret[4]
			current_note =  ret[5]
	if build:
		stop_section += '\n\t\t' + build
	while numpushes > 0:
		stop_section += """\n\t\tshutit.send('popd')"""
		numpushes      -= 1
	while numlogins > 0:
		stop_section += '''\n\t\tshutit.logout()'''
		numlogins -= 1
	if ifdepth != 0:
		shutit.fail('Unbalanced IFs in ' + section + ' section')
	sections.update({'stop_section':stop_section})

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

	if shutitfile_representation['shutitfile']['module_id']:
		module_id = shutitfile_representation['shutitfile']['module_id']
	else:
		module_id = skel_module_name

	return sections, module_id, module_id, depends, default_include


def handle_shutitfile_config_line(line):
	shutitfile_command = line[0].upper()
	build              = ''
	numtabs            = 2
	assert shutitfile_command in ('CONFIG','CONFIG_SECRET'), '%r is not a handled config command' % shutitfile_command
	if shutitfile_command in ('CONFIG','CONFIG_SECRET'):
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, (dict,list))
		if shutitfile_command == 'CONFIG':
			secret_str = 'False'
		elif shutitfile_command == 'CONFIG_SECRET':
			secret_str = 'True'
		if isinstance(shutitfile_args, list):
			assert len(shutitfile_args) in (1,2), ''
			cfg_name = shutitfile_args[0]
			if len(shutitfile_args) == 1:
				build += """\n""" + numtabs*'\t' + """shutit.get_config(self.module_id,'""" + cfg_name + """',secret=""" + secret_str + """)"""
			elif len(shutitfile_args) == 2:
				cfg_default = shutitfile_args[1]
				build += """\n""" + numtabs*'\t' + """shutit.get_config(self.module_id,'""" + cfg_name + """',default='""" + cfg_default + """',secret=""" + secret_str + """)"""
	return build


def handle_shutitfile_script_line(shutit, line, numpushes, wgetgot, numlogins, ifdepth, current_note):
	shutitfile_command = line[0].upper()
	build  = ''
	numtabs = 2 + ifdepth
	assert shutitfile_command in ('RUN','SEND','SEND_EXPECT','SEND_EXPECT_MULTI','EXPECT_REACT','SEND_EXPECT_REACT','SEND_UNTIL','UNTIL','UNTIL','ASSERT_OUTPUT_SEND','ASSERT_OUTPUT','PAUSE_POINT','EXPECT','EXPECT_MULTI','LOGIN','USER','LOGOUT','GET_AND_SEND_PASSWORD','LOGIN_WITH_PASSWORD','USER_WITH_PASSWORD','WORKDIR','COPY','ADD','ENV','INSTALL','REMOVE','COMMENT','NOTE','IF','ELSE','ELIF','IF_NOT','ELIF_NOT','ENDIF','RUN_SCRIPT','SCRIPT_BEGIN','START_BEGIN','START_END','STOP_BEGIN','STOP_END','TEST_BEGIN','TEST_END','BUILD_BEGIN','BUILD_END','ISINSTALLED_BEGIN','ISINSTALLED_END','COMMIT','PUSH','REPLACE_LINE','LOG','QUIT','STORE_RUN','VAGRANT_LOGIN','VAGRANT_LOGOUT'), '%r is not a handled script command' % shutitfile_command
	if shutitfile_command in ('RUN','SEND'):
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """\n""" + numtabs*'\t' + """shutit.send('''""" + cmd + """''',note='''""" + current_note + """''')"""
		current_note = ''
	elif shutitfile_command == 'SEND_EXPECT':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """\n""" + numtabs*'\t' + """shutit.send('''""" + cmd + """''',note='''""" + current_note + """''',expect="""
		current_note = ''
	elif shutitfile_command == 'EXPECT':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """'''""" + cmd + """''')"""
	elif shutitfile_command == 'SEND_EXPECT_MULTI':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """\n""" + numtabs*'\t' + """shutit.multisend('''""" + cmd + """''',"""
		current_note = ''
	elif shutitfile_command == 'EXPECT_MULTI':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, dict)
		multi_dict = str(shutitfile_args)
		build += multi_dict + """,note='''""" + current_note + """''')"""
	elif shutitfile_command == 'SEND_EXPECT_REACT':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """\n""" + numtabs*'\t' + """shutit.send('''""" + cmd + """''',note='''""" + current_note + """''',follow_on_commands="""
		current_note = ''
	elif shutitfile_command == 'EXPECT_REACT':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, dict)
		multi_dict = str(shutitfile_args)
		# We don't check exit here, as reactions will often have failing commands.
		build += multi_dict + ",check_exit=False)"
	elif shutitfile_command == 'SEND_UNTIL':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """\n""" + numtabs*'\t' + """shutit.send_until('''""" + cmd + """''',"""
		current_note = ''
	elif shutitfile_command == 'UNTIL':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """'''""" + cmd + """''',note='''""" + current_note + """''')"""
	elif shutitfile_command == 'PAUSE_POINT':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
		msg = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """\n""" + numtabs*'\t' + """shutit.pause_point('''""" + msg + """''')"""
	elif shutitfile_command == 'QUIT':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """\n""" + numtabs*'\t' + """shutit.fail('''""" + cmd + """''')"""
	elif shutitfile_command == 'LOGOUT':
		build += """\n""" + numtabs*'\t' + """shutit.logout(note='''""" + current_note + """''')"""
		current_note = ''
		numlogins -= 1
	elif shutitfile_command == 'VAGRANT_LOGIN':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
		machine_name = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """\n""" + numtabs*'\t' + """shutit.login('''vagrant ssh """ + machine_name + """''',note='''""" + current_note + """''')"""
		build += """\n""" + numtabs*'\t' + """shutit.login('''sudo su -''')"""
		current_note = ''
		numlogins += 1
	elif shutitfile_command == 'VAGRANT_LOGOUT':
		build += """\n""" + numtabs*'\t' + """shutit.logout()"""
		build += """\n""" + numtabs*'\t' + """shutit.logout(note='''""" + current_note + """''')"""
		current_note = ''
		numlogins -= 1
	elif shutitfile_command == 'ASSERT_OUTPUT_SEND':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """\n""" + numtabs*'\t' + """_cmd = '''""" + cmd + """'''\n\t\t_output = shutit.send_and_get_output('''""" + cmd + """''',note='''""" + current_note + """''')\n\t\timport re\n\t\tif not re.match('''"""
		current_note = ''
	elif shutitfile_command == 'ASSERT_OUTPUT':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
		expected_output = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += expected_output + """''', _output):\n""" + numtabs*'\t' + """\tshutit.pause_point('''Output of: ''' + _cmd + ''' was: ''' + _output + ''' It should be: """ + expected_output + """''')"""
	elif shutitfile_command == 'LOGIN':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """\n""" + numtabs*'\t' + """shutit.login(command='""" + cmd + """',note='''""" + current_note + """''')"""
		current_note = ''
		numlogins += 1
	elif shutitfile_command == 'USER':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """\n""" + numtabs*'\t' + """shutit.login(user='""" + cmd + """',note='''""" + current_note + """''')"""
		current_note = ''
		numlogins += 1
	elif shutitfile_command == 'GET_AND_SEND_PASSWORD':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
		msg = scan_text(' '.join(shutitfile_args)) + '\n'
		build += """\n""" + numtabs*'\t' + """_password = shutit.get_input('''""" + msg + """''',ispass=True)"""
		build += """\n""" + numtabs*'\t' + """shutit.send(_password,echo=False,check_exit=False,note='''""" + current_note + """''')"""
		current_note = ''
	elif shutitfile_command == 'LOGIN_WITH_PASSWORD':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		msg = scan_text(line[2]) + '\n'
		build += """\n""" + numtabs*'\t' + """_password = shutit.get_input('''""" + msg + """''',ispass=True)"""
		build += """\n""" + numtabs*'\t' + """shutit.login(command='""" + cmd + """', password=_password,note='''""" + current_note + """''')"""
		current_note = ''
	elif shutitfile_command == 'USER_WITH_PASSWORD':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		msg = scan_text(line[2]) + '\n'
		build += """\n""" + numtabs*'\t' + """_password = shutit.get_input('''""" + msg + """''',ispass=True)"""
		build += """\n""" + numtabs*'\t' + """shutit.login(user='""" + cmd + """', password=_password,note='''""" + current_note + """''')"""
		current_note = ''
	elif shutitfile_command == 'WORKDIR':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
		cmd = scan_text(' '.join(shutitfile_args).replace("'", "\\'"))
		build += """\n""" + numtabs*'\t' + """shutit.send('''pushd """ + cmd + """''',echo=False,note='''""" + current_note + """''')"""
		current_note = ''
		numpushes += 1
	elif shutitfile_command == 'COPY' or shutitfile_command == 'ADD':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
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
		if shutitfile_command == 'ADD' and urlparse(shutitfile_args[0])[0] != '':
			if not wgetgot:
				build += """\n""" + numtabs*'\t' + """shutit.install('wget')"""
				wgetgot = True
			if shutitfile_args[1][-1] == '/':
				destdir = scan_text(destdir[0:-1])
				outpath = scan_text(urlparse(shutitfile_args[0])[2])
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
			buildstagefile = scan_text(shutitfile_args[0])
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
		assert isinstance(shutitfile_args, dict)
		for k,v in iteritems(shutitfile_args):
			k = scan_text(k)
			v = scan_text(v)
			build += """\n""" + numtabs*"""\t""" + """shutit.send('''export """ + k + '=' + v + """''',note='''""" + current_note + """''')"""
			current_note = ''
	elif shutitfile_command == 'INSTALL':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
		build += """\n""" + numtabs*"""\t""" + """shutit.install('''""" + scan_text(' '.join(shutitfile_args)) + """''',note='''""" + current_note + """''')"""
		current_note = ''
	elif shutitfile_command == 'REMOVE':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
		build += """\n""" + numtabs*'\t' + """shutit.remove('''""" + scan_text(' '.join(shutitfile_args)) + """''',note='''""" + current_note + """''')"""
		current_note = ''
	elif shutitfile_command in ('COMMENT','NOTE'):
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
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
		assert isinstance(shutitfile_args, str)
		script = scan_text(shutitfile_args)
		build += """\n""" + numtabs*"""\t""" + """shutit.run_script('''""" + script + """''',note='''""" + current_note + """''')"""
		current_note = ''
	elif shutitfile_command == 'COMMIT':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
		assert len(shutitfile_args) == 1
		repo_name = scan_text(shutitfile_args[0])
		_default_repo_name = 'mymodule'
		if repo_name == _default_repo_name:
			shutit.log('The docker container will be committed with the default repo_name: ' + _default_repo_name + '.\nYou can change this by adding this to the ~/.shutit/config file:\n\n[repository]\nname:yourname\n\nand re-running.',level=logging.WARNING)
		if len(shutitfile_args) == 1:
			build += """\n""" + numtabs*"""\t""" + """shutit.do_repository_work('''""" + repo_name + """''',force=None,tag=True,note='''""" + current_note + """''')"""
			current_note = ''
	elif shutitfile_command == 'PUSH':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, list)
		assert len(shutitfile_args) == 1
		assert shutit.repository['user'] != '', 'If you want to push, set the [repository] settings (user,password,email) in your ~/.shutit/config file.'
		repo_name = scan_text(shutitfile_args[0])
		build += """\n""" + numtabs*"""\t""" + """shutit.push_repository('''""" + repo_name + """''',note='''""" + current_note + """''')"""
		current_note = ''
	elif shutitfile_command == 'REPLACE_LINE':
		shutitfile_args    = parse_shutitfile_args(line[1])
		assert isinstance(shutitfile_args, dict)
		# TODO: assert existence of these
		line     = scan_text(shutitfile_args['line'])
		filename = scan_text(shutitfile_args['filename'])
		pattern  = scan_text(shutitfile_args['pattern'])
		build += """\n""" + numtabs*'\t' + """shutit.replace_text('''""" + line + """''','''""" + filename + """''',pattern='''""" + pattern + """''',note='''""" + current_note + """''')"""
		current_note = ''
	elif shutitfile_command == 'LOG':
		shutitfile_args    = scan_text(line[1])
		assert isinstance(shutitfile_args, str) and shutitfile_args in ('DEBUG','WARNING','CRITICAL','INFO','ERROR')
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
	"""Scan text, and replace items that match shutit's pattern format, ie:
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
