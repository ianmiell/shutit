#!/bin/bash

#Copyright (C) 2014 OpenBet Limited
#
#Permission is hereby granted, free of charge, to any person obtaining a copy 
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

SKELETON_DIR=$1
MODULE_NAME=$2
SHUTIT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/.."
INCLUDE_SCRIPT=$3
readonly SKELETON_DIR MODULE_NAME SHUTIT_DIR INCLUDE_SCRIPT

set -o errexit
set -o nounset

function usage {
	cat > /dev/stdout << END
$0 PATH MODULE_NAME [SCRIPT]

PATH        - absolute path to new directory for module
MODULE_NAME - name for your module
SCRIPT      - pre-existing shell script to integrate into module
END
exit
}

if [[ $0 != create_skeleton.sh ]] && [[ $0 != ./create_skeleton.sh ]]
then
	cat > /dev/stdout << END
Must be run from bin dir like:

	create_skeleton.sh <absolute_directory_name> <module_name> [<shell script to integrate>]

or

	./create_skeleton.sh <absolute_directory_name> <module_name> [<shell script to integrate>]
END
	sleep 1
	usage
fi


if [[ x$SKELETON_DIR == "x" ]] || [[ $(echo $SKELETON_DIR | head -c 1) != "/" ]]
then
	echo "Must supply a directory and it must be absolute"
	sleep 1
	usage
fi

if [[ -a $SKELETON_DIR ]]
then
	echo "$SKELETON_DIR already exists"
	sleep 1
	usage
fi

if [[ x$MODULE_NAME == "x" ]]
then
	echo "Must supply a name for your module, eg mymodulename"
	sleep 1
	usage
fi


mkdir -p ${SKELETON_DIR}
mkdir -p ${SKELETON_DIR}/configs
mkdir -p ${SKELETON_DIR}/resources
mkdir -p ${SKELETON_DIR}/bin
## Copy self to new directory.
#cp ${BASH_SOURCE[0]} ${SKELETON_DIR}/bin
touch ${SKELETON_DIR}/README.md
cat >> ${SKELETON_DIR}/README.md << END
${MODULE_NAME}: description of module directory in here
END
touch ${SKELETON_DIR}/test_build.sh
cat >> ${SKELETON_DIR}/test_build.sh << END
set -e
python ${SHUTIT_DIR}/shutit_main.py -s container rm yes
# Display config
#python ${SHUTIT_DIR}/shutit_main.py --sc
# Debug
#python ${SHUTIT_DIR}/shutit_main.py --debug
# Tutorial
#python ${SHUTIT_DIR}/shutit_main.py --tutorial
END
chmod +x ${SKELETON_DIR}/test_build.sh
touch ${SKELETON_DIR}/build_and_push.sh
cat >> ${SKELETON_DIR}/build_and_push.sh << END
set -e
python ${SHUTIT_DIR}/shutit_main.py --config configs/push.cnf
# Display config
#python ${SHUTIT_DIR}/shutit_main.py --sc
# Debug
#python ${SHUTIT_DIR}/shutit_main.py --debug
# Tutorial
#python ${SHUTIT_DIR}/shutit_main.py --tutorial
END
chmod +x ${SKELETON_DIR}/build_and_push.sh
touch ${SKELETON_DIR}/resources/README.md
cat >> ${SKELETON_DIR}/resources/README.md << END
${MODULE_NAME}: resources required in this directory, eg gzips or text files.\nNote that the .gitignore file in the ${SKELETON_DIR} directory should exclude these files from being added to git repos (usually due to size), but can be added if forced with 'git add --force <file>'.
END
# Module template
cp ../docs/shutit_module_template.py ${SKELETON_DIR}/${MODULE_NAME}.py
perl -p -i -e "s/template/${MODULE_NAME}/g" ${SKELETON_DIR}/${MODULE_NAME}.py
perl -p -i -e "s/GLOBALLY_UNIQUE_STRING/'com.mycorp.${MODULE_NAME}'/g" ${SKELETON_DIR}/${MODULE_NAME}.py
perl -p -i -e "s/FLOAT/1000.00/" ${SKELETON_DIR}/${MODULE_NAME}.py
# Configs
# Setup base config for the new module
cat >> ${SKELETON_DIR}/configs/defaults.cnf << END
# Base config for the module. This contains standard defaults.
[com.mycorp.${MODULE_NAME}]
example:astring
example_bool:yes
END
# Setup base config for the new module
cat >> ${SKELETON_DIR}/configs/build.cnf << END
# When this module is the one being built, which modules should be built along with it by default?
# This feeds into automated testing of each module.
[com.mycorp.${MODULE_NAME}]
build:yes

# Aspects of build process
[build]
# Allowed images, eg ["ubuntu:12.04"].
# "any" is a special value meaning any image is ok, and is the default.
# It's recommended this is locked down as far as possible.
allowed_images:["any"]
END
# Setup base config for the new module
cat >> ${SKELETON_DIR}/configs/push.cnf << END
[repository]
do_repository_work:yes
user:$(whoami)
password:YOUR_REGISTRY_PASSWORD_OR_BLANK
email:YOUR_REGISTRY_EMAIL_OR_BLANK
push:yes
tar:no
server:REMOVE_ME_FOR_DOCKER_INDEX
name:$MODULE_NAME
suffix_date:yes
suffix_format:%s

[container]
rm:false
END

# Include bash script
if [[ x${INCLUDE_SCRIPT} != "x" ]]
then
	cat > /dev/stdout << END
================================================================================
Please note that your bash script in:
${INCLUDE_SCRIPT}
should be a simple set of one-liners
that return to the prompt. Anything fancy with ifs, backslashes or other
multi-line commands need to be handled more carefully.
================================================================================
Hit return to continue.
================================================================================
END
	read _ignored
	SBSI="/tmp/shutit_bash_script_include_$(date +%N)"
	# egrep removes leading space
	# grep removes comments
	# sed1 ensures no confusion with double quotes
	# sed2 replaces script lines with shutit code
	# sed3 uses treble quotes for simpler escaping of strings
	egrep -v '^[\s]*$' $INCLUDE_SCRIPT | grep -v '^#' | sed "s/\"$/\" /;s/^/\t\tutil.send_and_expect(container_child,\"\"\"/;s/$/\"\"\",root_prompt_expect)/" > ${SBSI}
	sed "64r ${SBSI}" ${SKELETON_DIR}/${MODULE_NAME}.py > ${SKELETON_DIR}/${MODULE_NAME}.py.new
	mv ${SKELETON_DIR}/${MODULE_NAME}.py.new ${SKELETON_DIR}/${MODULE_NAME}.py
fi



cat > ${SKELETON_DIR}/bin/test.sh << 'END'
#!/bin/bash
# Test the building of this module
set -e
if [[ $0 != test.sh ]] && [[ $0 != ./test.sh ]] && [[ $0 != create_skeleton.sh ]] && [[ $0 != ./create_skeleton.sh ]]
then
        echo 
        echo "Called as: $0"
	echo "Must be run from test dir like:"
        echo
        echo "  test.sh <path_to_shutit_dir>"
        echo
        echo "or"
        echo
        echo "  ./test.sh <path_to_shutit_dir>"
        exit
fi
if [ x$1 = 'x' ]
then
	echo "Must supply path to core ShutIt directory"
	exit 1
fi
cd ..
./test_build.sh
if [[ $? -eq 0 ]]
then
	cd -
	exit 0
else
	cd -
	exit 1
fi
END
# Hostname config
echo "Password (for host ($(hostname)))"
read -s pw_host
echo "Container's hostname"
read container_hostname
echo "Password (for container)"
read -s pw_container
cat > ${SKELETON_DIR}/configs/$(hostname)_$(whoami).cnf << END
# Put hostname- and user-specific config in this file.
# This file must always have perms 0600 for shutit to run.

[container]
# The container you create will have this password for root.
password:${pw_container}
# The container you create will have this hostname during the build.
hostname:${container_hostname}
# Whether to remove the container when finished.
rm:no

[host]
# Your username on the host
username:$(whoami)
# Your password on the host (set to empty if not required, ie "password:")
password:${pw_host}

[repository]
do_repository_work:no
# If switched on, will push to docker_io
push:no
repository_server:
#Must be set if do_repository_work is true/yes and user is not blank
password:YOUR_REGISTRY_PASSWORD_OR_BLANK
#Must be set if do_repository_work is true/yes and user is not blank
email:YOUR_REGISTRY_EMAIL_OR_BLANK
# Whether to push to the server
name:${MODULE_NAME}
END
chmod 0600 ${SKELETON_DIR}/configs/defaults.cnf
chmod 0600 ${SKELETON_DIR}/configs/build.cnf
chmod 0600 ${SKELETON_DIR}/configs/push.cnf
chmod 0600 ${SKELETON_DIR}/configs/$(hostname)_$(whoami).cnf
chmod +x ${SKELETON_DIR}/bin/test.sh

pushd ${SKELETON_DIR}
if ! git status >/dev/null 2>&1
then
	git init
	cp ${SHUTIT_DIR}/.gitignore .gitignore
fi
popd

# Run file
touch ${SKELETON_DIR}/run.sh
cat > ${SKELETON_DIR}/run.sh << END
# Example for running
docker run -t -i ${MODULE_NAME} /bin/bash
END
chmod +x ${SKELETON_DIR}/run.sh

echo "================================================================================"
echo "Run:"
echo ""
echo "    cd ${SKELETON_DIR}; python ${SHUTIT_DIR}/shutit_main.py --tutorial"
echo ""
echo "And follow the instructions in the output."
echo ""
echo "An image called ${MODULE_NAME} will be created and can be run"
echo "with the run.sh command."
echo "================================================================================"

