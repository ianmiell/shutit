import os
import logging
from . import shutitfile

def setup_docker_pattern(shutit,
                         skel_path,
                         skel_delivery,
                         skel_domain,
                         skel_module_name,
                         skel_shutitfiles,
                         skel_domain_hash,
                         skel_depends):

	# Set up shutitfile cfg
	shutit.shutitfile['base_image'] = shutit.cfg['skeleton']['base_image']
	shutit.shutitfile['cmd']        = """/bin/sh -c 'sleep infinity'"""
	shutit.shutitfile['expose']     = []
	shutit.shutitfile['env']        = []
	shutit.shutitfile['volume']     = []
	shutit.shutitfile['onbuild']    = []
	shutit.shutitfile['script']     = []

	# arguments
	shutit.cfg['skeleton']['volumes_arg'] = ''
	for varg in shutit.shutitfile['volume']:
		shutit.cfg['skeleton']['volumes_arg'] += ' -v ' + varg + ':' + varg
	shutit.cfg['skeleton']['ports_arg'] = ''
	if isinstance(shutit.shutitfile['expose'], str):
		for parg in shutit.shutitfile['expose']:
			shutit.cfg['skeleton']['ports_arg'] += ' -p ' + parg + ':' + parg
	else:
		for parg in shutit.shutitfile['expose']:
			for port in parg.split():
				shutit.cfg['skeleton']['ports_arg'] += ' -p ' + port + ':' + port
	shutit.cfg['skeleton']['env_arg'] = ''
	for earg in shutit.shutitfile['env']:
		shutit.cfg['skeleton']['env_arg'] += ' -e ' + earg.split()[0] + ':' + earg.split()[1]

	os.system('mkdir -p ' + skel_path)
	build_bin_filename = skel_path + '/build.sh'
	build_bin_file = open(build_bin_filename,'w+')
	build_bin_file.write('''#!/bin/bash
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
	build_bin_file.close()
	os.chmod(build_bin_filename,0o755)
	run_bin_filename   = skel_path + '/run.sh'
	run_bin_file = open(run_bin_filename,'w+')
	# TODO: sort out entrypoint properly
	entrypoint = ''
	run_bin_file.write('''#!/bin/bash
# Example for running
DOCKER=${DOCKER:-docker}
IMAGE_NAME=%s
CONTAINER_NAME=$IMAGE_NAME
DOCKER_ARGS=''
while getopts "i:c:a:" opt
do
    case "$opt" in
    i)
        IMAGE_NAME=$OPTARG
        ;;
    c)
        CONTAINER_NAME=$OPTARG
        ;;
    a)
        DOCKER_ARGS=$OPTARG
        ;;
    esac
done
${DOCKER} run -d --name ${CONTAINER_NAME} ''' + skel_module_name + ''' ''' +  shutit.cfg['skeleton']['ports_arg'] + ''' ''' + shutit.cfg['skeleton']['ports_arg'] + ''' ''' + shutit.cfg['skeleton']['env_arg'] + ''' ${DOCKER_ARGS} ${IMAGE_NAME} ''' + entrypoint + ''' ''' + shutit.shutitfile['cmd'])
	run_bin_file.close()
	os.chmod(run_bin_filename,0o755)
	test_bin_filename  = skel_path + '/test.sh'
	test_bin_file = open(test_bin_filename,'w+')
	test_bin_file.write('''#!/bin/bash
# Test the building of this module
if [ $0 != test.sh ] && [ $0 != ./test.sh ]
then
    echo
    echo "Called as: $0"
    echo "Must be run as test.sh or ./test.sh"
    exit
fi
./build.sh "$@"''')
	test_bin_file.close()
	os.chmod(test_bin_filename,0o755)
	os.system('mkdir -p ' + skel_path + '/configs')

	push_cnf_filename = skel_path + '/configs/push.cnf'
	push_cnf_file = open(push_cnf_filename,'w+')
	push_cnf_file.write('''###############################################################################
# PLEASE NOTE: This file should be changed only by the maintainer.
# PLEASE NOTE: IF YOU WANT TO CHANGE THE CONFIG, PASS IN
#              --config configfilename
#              OR ADD DETAILS TO YOUR
#              ~/.shutit/config
#              FILE
###############################################################################
[target]
rm:false

[repository]
# COPY THESE TO YOUR ~/.shutit/config FILE AND FILL OUT ITEMS IN CAPS
#user:YOUR_USERNAME
## Fill these out in server- and username-specific config (also in this directory)
#password:YOUR_REGISTRY_PASSWORD_OR_BLANK
## Fill these out in server- and username-specific config (also in this directory)
#email:YOUR_REGISTRY_EMAIL_OR_BLANK
#tag:no
#push:yes
#save:no
#export:no
##server:REMOVE_ME_FOR_DOCKER_INDEX
## tag suffix, defaults to "latest", eg registry/username/repository:latest.
## empty is also "latest"
#tag_name:latest
#suffix_date:no
#suffix_format:%s''')
	push_cnf_file.close()
	os.chmod(push_cnf_filename,0o400)
	dockerfile_filename = skel_path + '/Dockerfile'
	dockerfile_file = open(dockerfile_filename,'w+')
	dockerfile_file.write('''FROM ''' + shutit.shutitfile['base_image'] + '''

RUN apt-get update
RUN apt-get install -y -qq git python-pip python-dev
RUN pip install shutit

WORKDIR /opt
# Change the next two lines to build your ShutIt module.
RUN git clone https://github.com/yourname/yourshutitproject.git
WORKDIR /opt/yourshutitproject
RUN shutit build --delivery dockerfile
CMD ["/bin/bash"]''')
	dockerfile_file.close()

	# User message
	shutit.log('''# Run:
cd ''' + skel_path + ''' && ./build.sh
# to build.
# And then:
./run.sh
# to run.''',transient=True)

	if skel_shutitfiles:
		shutit.log('Processing ShutItFiles: ' + str(skel_shutitfiles),level=logging.DEBUG)
		_total = len(skel_shutitfiles)
		_count = 0
		for skel_shutitfile in skel_shutitfiles:
			_count += 1
			shutit.log('Processing ShutItFile: ' + str(skel_shutitfile),level=logging.INFO)
			module_modifier = '_' + str(_count)
			new_module_filename = skel_path + '/' + os.path.join(skel_module_name + module_modifier + '.py')
			shutit.cfg['skeleton']['module_modifier'] = module_modifier
			(sections, skel_module_id, skel_module_name, _, _) = shutitfile.shutitfile_to_shutit_module(shutit, skel_shutitfile,skel_path,skel_domain,skel_module_name,skel_domain_hash,skel_delivery,skel_depends,_count,_total,module_modifier)
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
shutit.core.module.build:yes
# Allowed images as a regexp, eg ["ubuntu:12.*"], or [".*"], or ["centos"].
# It's recommended this is locked down as far as possible.
shutit.core.module.allowed_images:["''' + shutit.shutitfile['base_image'] + '''"]

# Aspects of build process
[build]
base_image:''' + shutit.shutitfile['base_image'] + '''

# Volume arguments wanted as part of the build
[target]
volumes:

[repository]
name:''' + skel_module_name)
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
[''' + skel_domain + '''.''' +  skel_module_name + ''']
shutit.core.module.build:yes
# Allowed images as a regexp, eg ["ubuntu:12.*"], or [".*"], or ["centos"].
# It's recommended this is locked down as far as possible.
shutit.core.module.allowed_images:["''' + shutit.shutitfile['base_image'] + '''"]

# Aspects of build process
[build]
base_image:''' + shutit.shutitfile['base_image'] + '''

# Volume arguments wanted as part of the build
[target]
volumes:

[repository]
name:''' + skel_module_name)
		build_cnf_file.close()
		os.chmod(build_cnf_filename,0o400)
