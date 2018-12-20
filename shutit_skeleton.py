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

from __future__ import print_function
import os
import re
import json
from shutit_patterns import shutitfile


def create_skeleton(shutit):
	"""Creates module based on a pattern supplied as a git repo.
	"""
	skel_path        = shutit.cfg['skeleton']['path']
	skel_module_name = shutit.cfg['skeleton']['module_name']
	skel_domain      = shutit.cfg['skeleton']['domain']
	skel_domain_hash = shutit.cfg['skeleton']['domain_hash']
	skel_depends     = shutit.cfg['skeleton']['depends']
	skel_shutitfiles = shutit.cfg['skeleton']['shutitfiles']
	skel_delivery    = shutit.cfg['skeleton']['delivery']
	skel_pattern     = shutit.cfg['skeleton']['pattern']
	# For vagrant only
	skel_vagrant_num_machines   = shutit.cfg['skeleton']['vagrant_num_machines']
	skel_vagrant_machine_prefix = shutit.cfg['skeleton']['vagrant_machine_prefix']
	skel_vagrant_ssh_access     = shutit.cfg['skeleton']['vagrant_ssh_access']
	skel_vagrant_docker         = shutit.cfg['skeleton']['vagrant_docker']
	skel_vagrant_snapshot       = shutit.cfg['skeleton']['vagrant_snapshot']
	skel_vagrant_upload         = shutit.cfg['skeleton']['vagrant_upload']
	skel_vagrant_image_name     = shutit.cfg['skeleton']['vagrant_image_name']

	# Check setup
	if not skel_path or skel_path[0] != '/':
		shutit.fail('Must supply a directory and it must be absolute') # pragma: no cover
	if os.path.exists(skel_path):
		shutit.fail(skel_path + ' already exists') # pragma: no cover
	if not skel_module_name:
		shutit.fail('Must supply a name for your module, eg mymodulename') # pragma: no cover
	if not re.match('^[a-zA-z_][0-9a-zA-Z_]+$', skel_module_name):
		shutit.fail('Module names must comply with python classname standards: cf: http://stackoverflow.com/questions/10120295/valid-characters-in-a-python-class-name name: ' + skel_module_name) # pragma: no cover
	if not skel_domain:
		shutit.fail('Must supply a domain for your module, eg com.yourname.madeupdomainsuffix') # pragma: no cover

	# Create folders and process pattern
	os.makedirs(skel_path)
	os.chdir(skel_path)
	# If it's shutitfile and vagrant
	if shutit.cfg['skeleton']['pattern'] == 'bash':
		from shutit_patterns import bash
		bash.setup_bash_pattern(shutit,
		                        skel_path=skel_path,
		                        skel_delivery=skel_delivery,
		                        skel_domain=skel_domain,
		                        skel_module_name=skel_module_name,
		                        skel_shutitfiles=skel_shutitfiles,
		                        skel_domain_hash=skel_domain_hash,
		                        skel_depends=skel_depends)
	elif shutit.cfg['skeleton']['pattern'] == 'docker':
		from shutit_patterns import docker
		docker.setup_docker_pattern(shutit,
		                            skel_path=skel_path,
		                            skel_delivery=skel_delivery,
		                            skel_domain=skel_domain,
		                            skel_module_name=skel_module_name,
		                            skel_shutitfiles=skel_shutitfiles,
		                            skel_domain_hash=skel_domain_hash,
		                            skel_depends=skel_depends)
	elif shutit.cfg['skeleton']['pattern'] == 'vagrant': # pragma: no cover
		from shutit_patterns import vagrant
		vagrant.setup_vagrant_pattern(shutit,
		                              skel_path=skel_path,
		                              skel_delivery=skel_delivery,
		                              skel_domain=skel_domain,
		                              skel_module_name=skel_module_name,
		                              skel_shutitfiles=skel_shutitfiles,
		                              skel_domain_hash=skel_domain_hash,
		                              skel_depends=skel_depends,
		                              skel_vagrant_num_machines=skel_vagrant_num_machines,
		                              skel_vagrant_machine_prefix=skel_vagrant_machine_prefix,
		                              skel_vagrant_ssh_access=skel_vagrant_ssh_access,
		                              skel_vagrant_docker=skel_vagrant_docker,
		                              skel_vagrant_snapshot=skel_vagrant_snapshot,
		                              skel_vagrant_upload=skel_vagrant_upload,
		                              skel_vagrant_image_name=skel_vagrant_image_name)
	elif shutit.cfg['skeleton']['pattern'] == 'shutitfile':
		shutitfile.setup_shutitfile_pattern(shutit,
		                                    skel_path=skel_path,
		                                    skel_delivery=skel_delivery,
		                                    skel_pattern=skel_pattern,
		                                    skel_domain=skel_domain,
		                                    skel_module_name=skel_module_name,
		                                    skel_vagrant_num_machines=skel_vagrant_num_machines,
		                                    skel_vagrant_machine_prefix=skel_vagrant_machine_prefix,
		                                    skel_vagrant_ssh_access=skel_vagrant_ssh_access,
		                                    skel_vagrant_docker=skel_vagrant_docker)
	elif shutit.cfg['skeleton']['pattern'] == 'docker_tutorial': # pragma: no cover
		shutit.fail('docker_tutorial not yet supported')


def process_shutitfile(shutit, shutitfile_contents):
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
	shutitfile_list, ok = shutitfile.parse_shutitfile(shutitfile_contents)
	if not ok: # pragma: no cover
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
			assert shutitfile_command in ('SCRIPT_END','SCRIPT_BEGIN','SCRIPT_END','FROM','ONBUILD','VOLUME','DESCRIPTION','MAINTAINER','EXPOSE','ENTRYPOINT','CMD','USER','LOGIN','LOGOUT','GET_PASSWORD','ENV','RUN','SEND','ASSERT_OUTPUT','PAUSE_POINT','EXPECT','EXPECT_MULTI','EXPECT_REACT','UNTIL','ADD','COPY','WORKDIR','COMMENT','NOTE','INSTALL','REMOVE','DEPENDS','DELIVERY','MODULE_ID','REPLACE_LINE','ENSURE_LINE','START_BEGIN','START_END','STOP_BEGIN','STOP_END','TEST_BEGIN','TEST_END','BUILD_BEGIN','BUILD_END','ISINSTALLED_BEGIN','ISINSTALLED_END','IF','IF_NOT','ELIF_NOT','ELIF','ELSE','ENDIF','COMMIT','PUSH','DEFAULT_INCLUDE','LOG','CONFIG','CONFIG_SECRET','QUIT','STORE_RUN','VAGRANT_LOGIN','VAGRANT_LOGOUT'), shutit_util.print_debug(msg='%r is not a handled ShutItFile command' % shutitfile_command)
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
				shutit_global.shutit_global_object.shutit_print('Ignoring FROM line as this it has already been set.') # pragma: no cover
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
				shutit.fail('GET_PASSWORD line not after a USER or LOGIN line: ' + shutitfile_command + ' ' + item[1]) # pragma: no cover
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
				shutit.fail('ASSERT_OUTPUT line not after a RUN/SEND line: ' + shutitfile_command + ' ' + item[1]) # pragma: no cover
			shutitfile_representation['shutitfile']['script'][-1][0] = 'ASSERT_OUTPUT_SEND'
			shutitfile_representation['shutitfile']['script'].append([shutitfile_command, item[1]])
		elif shutitfile_command == 'EXPECT':
			if last_shutitfile_command not in ('RUN','SEND','GET_PASSWORD'):
				shutit.fail('EXPECT line not after a RUN, SEND or GET_PASSWORD line: ' + shutitfile_command + ' ' + item[1]) # pragma: no cover
			shutitfile_representation['shutitfile']['script'][-1][0] = 'SEND_EXPECT'
			shutitfile_representation['shutitfile']['script'].append([shutitfile_command, item[1]])
		elif shutitfile_command == 'EXPECT_MULTI':
			if last_shutitfile_command not in ('RUN','SEND','GET_PASSWORD'):
				shutit.fail('EXPECT_MULTI line not after a RUN, SEND or GET_PASSWORD line: ' + shutitfile_command + ' ' + item[1]) # pragma: no cover
			shutitfile_representation['shutitfile']['script'][-1][0] = 'SEND_EXPECT_MULTI'
			shutitfile_representation['shutitfile']['script'].append([shutitfile_command, item[1]])
		elif shutitfile_command == 'EXPECT_REACT':
			if last_shutitfile_command not in ('RUN','SEND','GET_PASSWORD'):
				shutit.fail('EXPECT_REACT line not after a RUN, SEND or GET_PASSWORD line: ' + shutitfile_command + ' ' + item[1]) # pragma: no cover
			shutitfile_representation['shutitfile']['script'][-1][0] = 'SEND_EXPECT_REACT'
			shutitfile_representation['shutitfile']['script'].append([shutitfile_command, item[1]])
		elif shutitfile_command == 'UNTIL':
			if last_shutitfile_command not in ('RUN','SEND'):
				shutit.fail('UNTIL line not after a RUN, SEND: ' + shutitfile_command + ' ' + item[1]) # pragma: no cover
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
		elif shutitfile_command in ('ADD','COPY','WORKDIR','COMMENT','INSTALL','REMOVE','REPLACE_LINE','ENSURE_LINE','LOG','COMMIT','PUSH','QUIT','PAUSE_POINT','USER','LOGIN','LOGOUT','VAGRANT_LOGIN','VAGRANT_LOGOUT'):
			shutitfile_representation['shutitfile']['script'].append([shutitfile_command, item[1]])
		elif shutitfile_command in ('IF','IF_NOT','ELIF_NOT','ELIF','STORE_RUN'):
			# Parser retrieved two items here
			shutitfile_representation['shutitfile']['script'].append([shutitfile_command, item[1], item[2]])
		elif shutitfile_command in ('ELSE','ENDIF','START_BEGIN','START_END','STOP_BEGIN','STOP_END','TEST_BEGIN','TEST_END','BUILD_BEGIN','BUILD_END','ISINSTALLED_BEGIN','ISINSTALLED_END'):
			shutitfile_representation['shutitfile']['script'].append([shutitfile_command])
		else:
			shutit.fail('shutitfile command: ' + shutitfile_command + ' not processed') # pragma: no cover
		last_shutitfile_command = shutitfile_command
	return shutitfile_representation, True
