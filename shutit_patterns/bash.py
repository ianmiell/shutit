import os
import shutit_global
from . import shutitfile

def setup_bash_pattern(skel_path,
                       skel_delivery,
                       skel_domain,
                       skel_module_name,
                       skel_shutitfiles,
                       skel_domain_hash,
                       skel_depends):

	shutit = shutit_global.shutit
	runsh_filename = skel_path + '/run.sh'
	runsh_file = open(runsh_filename,'w+')
	runsh_file.write('''#!/bin/bash
[[ -z "$SHUTIT" ]] && SHUTIT="$1/shutit"
[[ ! -a "$SHUTIT" ]] || [[ -z "$SHUTIT" ]] && SHUTIT="$(which shutit)"
if [[ ! -a "$SHUTIT" ]]
then
	echo "Must have shutit on path, eg export PATH=$PATH:/path/to/shutit_dir"
	exit 1
fi
$SHUTIT build -d ''' + skel_delivery + ''' "$@"
if [[ $? != 0 ]]
then
	exit 1
fi''')
	runsh_file.close()
	os.chmod(runsh_filename,0o755)

	# build.cnf file
	os.system('mkdir -p ' + skel_path + '/configs')

	# User message
	shutit.log('''# Run:
cd ''' + skel_path + ''' && ./run.sh
# to run.''',transient=True)

	if skel_shutitfiles:
		_count = 0
		_total = len(skel_shutitfiles)
		for skel_shutitfile in skel_shutitfiles:
			_count += 1
			module_modifier = '_' + str(_count)
			new_module_filename = skel_path + '/' + os.path.join(skel_module_name + module_modifier + '.py')
			shutit.cfg['skeleton']['module_modifier'] = module_modifier
			(sections, skel_module_id, skel_module_name, default_include, ok) = shutitfile.shutitfile_to_shutit_module(skel_shutitfile,skel_path,skel_domain,skel_module_name,skel_domain_hash,skel_delivery,skel_depends,_count,_total,module_modifier)
			shutit.cfg['skeleton']['header_section']      = sections['header_section']
			shutit.cfg['skeleton']['config_section']      = sections['config_section']
			shutit.cfg['skeleton']['build_section']       = sections['build_section']
			shutit.cfg['skeleton']['finalize_section']    = sections['finalize_section']
			shutit.cfg['skeleton']['test_section']        = sections['test_section']
			shutit.cfg['skeleton']['isinstalled_section'] = sections['isinstalled_section']
			shutit.cfg['skeleton']['start_section']       = sections['start_section']
			shutit.cfg['skeleton']['stop_section']        = sections['stop_section']
			shutit.cfg['skeleton']['final_section']       = sections['final_section']
			module_file = open(new_module_filename,'w+')
			module_file.write(shutit.cfg['skeleton']['header_section'] + '''

	def build(self, shutit):
''' + shutit.cfg['skeleton']['build_section'] + '''
		return True

	def get_config(self, shutit):
''' + shutit.cfg['skeleton']['config_section'] + '''
		return True

	def test(self, shutit):
''' + shutit.cfg['skeleton']['test_section'] + '''
		return True

	def finalize(self, shutit):
''' + shutit.cfg['skeleton']['finalize_section'] + '''
		return True

	def is_installed(self, shutit):
''' + shutit.cfg['skeleton']['isinstalled_section'] + '''
		return False

	def start(self, shutit):
''' + shutit.cfg['skeleton']['start_section'] + '''
		return True

	def stop(self, shutit):
''' + shutit.cfg['skeleton']['stop_section'] + '''
		return True

''' + shutit.cfg['skeleton']['final_section'])
			module_file.close()
			# Set up build.cnf
			build_cnf_filename = skel_path + '/configs/build.cnf'
			if _count == 1:
				build_cnf_file = open(build_cnf_filename,'w+')
				build_cnf_file.write('''###############################################################################
# PLEASE NOTE: This file should be changed only by the maintainer.
# PLEASE NOTE: This file is only sourced if the "shutit build" command is run
#              and this file is in the relative path: configs/build.cnf
#              This is to ensure it is only sourced if _this_ module is the
#              target.
###############################################################################
# When this module is the one being built, which modules should be built along with it by default?
# This feeds into automated testing of each module.
[''' + skel_module_id + ''']
shutit.core.module.build:yes''')
				build_cnf_file.close()
			else:
				build_cnf_file = open(build_cnf_filename,'a')
				build_cnf_file.write('''
[''' + skel_domain + '''.''' +  skel_module_name + module_modifier + ''']
shutit.core.module.build:yes''')
				build_cnf_file.close()
		os.chmod(build_cnf_filename,0o400)
	else:
		shutit.cfg['skeleton']['header_section']      = 'from shutit_module import ShutItModule\n\nclass ' + skel_module_name + '(ShutItModule):\n'
		shutit.cfg['skeleton']['config_section']      = ''
		shutit.cfg['skeleton']['build_section']       = ''
		shutit.cfg['skeleton']['finalize_section']    = ''
		shutit.cfg['skeleton']['test_section']        = ''
		shutit.cfg['skeleton']['isinstalled_section'] = ''
		shutit.cfg['skeleton']['start_section']       = ''
		shutit.cfg['skeleton']['stop_section']        = ''
		shutit.cfg['skeleton']['final_section']        = """def module():
		return """ + skel_module_name + """(
			'""" + skel_domain + '''.''' + skel_module_name + """', """ + skel_domain_hash + """.0001,
			description='',
			maintainer='',
			delivery_methods=['""" + skel_delivery + """'],
			depends=['""" + skel_depends + """']
		)"""
		new_module_filename = skel_path + '/' + os.path.join(skel_module_name) + '.py'
		module_file = open(new_module_filename,'w+')
		module_file.write(shutit.cfg['skeleton']['header_section'] + '''

	def build(self, shutit):
''' + shutit.cfg['skeleton']['build_section'] + '''
		return True

	def get_config(self, shutit):
''' + shutit.cfg['skeleton']['config_section'] + '''
		return True

	def test(self, shutit):
''' + shutit.cfg['skeleton']['test_section'] + '''
		return True

	def finalize(self, shutit):
''' + shutit.cfg['skeleton']['finalize_section'] + '''
		return True

	def is_installed(self, shutit):
''' + shutit.cfg['skeleton']['isinstalled_section'] + '''
		return False

	def start(self, shutit):
''' + shutit.cfg['skeleton']['start_section'] + '''
		return True

	def stop(self, shutit):
''' + shutit.cfg['skeleton']['stop_section'] + '''
		return True

''' + shutit.cfg['skeleton']['final_section'])
		module_file.close()

		build_cnf_filename = skel_path + '/configs/build.cnf'
		build_cnf_file = open(build_cnf_filename,'w+')
		build_cnf_file.write('''###############################################################################
# PLEASE NOTE: This file should be changed only by the maintainer.
# PLEASE NOTE: This file is only sourced if the "shutit build" command is run
#              and this file is in the relative path: configs/build.cnf
#              This is to ensure it is only sourced if _this_ module is the
#              target.
###############################################################################
# When this module is the one being built, which modules should be built along with it by default?
# This feeds into automated testing of each module.
['''+skel_domain+'''.'''+skel_module_name+''']
shutit.core.module.build:yes''')
		build_cnf_file.close()
		os.chmod(build_cnf_filename,0o400)

