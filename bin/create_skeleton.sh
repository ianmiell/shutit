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

set -e

function usage {
	cat > /dev/stdout << END
$0 PATH MODULE_NAME [SCRIPT]

PATH        - absolute path to new directory for module
MODULE_NAME - name for your module
SCRIPT      - pre-existing shell script to integrate into module
END
exit
}

usage

if [[ $0 != create_skeleton.sh ]] && [[ $0 != ./create_skeleton.sh ]]
then
	cat > /dev/stdout << END
Must be run from bin dir like:

	create_skeleton.sh <absolute_directory_name> <module_name> [<shell script to integrate>]

or

	./create_skeleton.sh <absolute_directory_name> <module_name> [<shell script to integrate>]
END
	sleep 2
	usage
fi


if [[ x$1 == "x" ]] || [[ $(echo $1 | head -c 1) != "/" ]]
then
	echo "Must supply a directory and it must be absolute"
	sleep 2
	usage
fi

if [[ -a $1 ]]
then
	echo "$1 already exists"
	sleep 2
	usage
fi

if [[ x$2 == "x" ]]
then
	echo "Must supply a name for your module, eg mymodulename"
	sleep 2
	usage
fi

# TODO: make patch
SKELETON_DIR=$1
MODULE_NAME=$2
SHUTIT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/.."

mkdir -p ${SKELETON_DIR}
mkdir -p ${SKELETON_DIR}/configs
mkdir -p ${SKELETON_DIR}/resources
mkdir -p ${SKELETON_DIR}/bin
# Copy self to new directory.
cp ${BASH_SOURCE[0]} ${SKELETON_DIR}/bin
touch ${SKELETON_DIR}/README.md
cat >> ${SKELETON_DIR}/README.md << END
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
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

${MODULE_NAME}: description of module directory in here
END
touch ${SKELETON_DIR}/build.sh
cat >> ${SKELETON_DIR}/build.sh << END
#!/bin/bash
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
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

python ${SHUTIT_DIR}/shutit_main.py
END
chmod +x ${SKELETON_DIR}/build.sh
touch ${SKELETON_DIR}/resources/README.md
cat >> ${SKELETON_DIR}/resources/README.md << END
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
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

${MODULE_NAME}: resources required in this directory, eg gzips or text files.\nNote that the .gitignore file in the ${SKELETON_DIR} directory should exclude these files from being added to git repos (usually due to size), but can be added if forced with 'git add --force <file>'.
END
touch ${SKELETON_DIR}/bin/README.md
cat ${SKELETON_DIR}/bin/README.md << END
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
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

${MODULE_NAME}: test.sh to run as part of tests in this directory
END
# Module template
cp ../docs/shutit_module_template.py ${SKELETON_DIR}/${MODULE_NAME}.py
perl -p -i -e "s/template/${MODULE_NAME}/g" ${SKELETON_DIR}/${MODULE_NAME}.py
perl -p -i -e "s/GLOBALLY_UNIQUE_STRING/'com.mycorp.${MODULE_NAME}'/g" ${SKELETON_DIR}/${MODULE_NAME}.py
perl -p -i -e "s/FLOAT/1000.00/" ${SKELETON_DIR}/${MODULE_NAME}.py
# Configs
# Setup base config for the new module
cat >> ${SKELETON_DIR}/configs/defaults.cnf << END
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
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

# Base config for the module. This contains standard defaults.
[com.mycorp.${MODULE_NAME}]
example:astring
example_bool:yes

[build]
# Let's error on exit code problem until we want to switch this off.
action_on_ret_code:error

# Defaults as at creation time, hashed out by default:
END
# Setup base config for the new module
cat >> ${SKELETON_DIR}/configs/build.cnf << END
# When this module is the one being built, which modules should be built along with it by default?
# This feeds into automated testing of each module.
[com.mycorp.${MODULE_NAME}]
build:yes
END

# Include bash script
if [[ x${3} != "x" ]]
then
	echo "Please note that your bash script in ${3} should be a simple set of one-liners that return to the prompt."
	echo "Anything fancy with ifs, backslashes etc need to be handled more carefully (see README). Hit return to continue."
	read _ignored
	SBSI="/tmp/shutit_bash_script_include_`date +%N`"
	egrep -v '^[\s]*$' $3 | grep -v '^#!' | sed "s/^/\t\tutil.send_and_expect(container_child,\"/;s/$/\",config_dict['container_child']['root_prompt'])/" > ${SBSI}
	sed "25r ${SBSI}" ${SKELETON_DIR}/${MODULE_NAME}.py > ${SKELETON_DIR}/${MODULE_NAME}.py.new
	mv ${SKELETON_DIR}/${MODULE_NAME}.py.new ${SKELETON_DIR}/${MODULE_NAME}.py
fi



cat > ${SKELETON_DIR}/bin/test.sh << END
#!/bin/bash
# Test the building of this module
set -e
if [[ \$0 != test.sh ]] && [[ \$0 != ./test.sh ]] && [[ \$0 != create_skeleton.sh ]] && [[ \$0 != ./create_skeleton.sh ]]
then
        echo
        echo "Called as: \$0"
	echo "Must be run from test dir like:"
        echo
        echo "  test.sh <path_to_shutit_dir>"
        echo
        echo "or"
        echo
        echo "  ./test.sh <path_to_shutit_dir>"
        exit
fi
if [ x\$1 = 'x' ]
then
	echo "Must supply path to core ShutIt directory"
	exit 1
fi
cd ..
./build.sh
if [[ \$? -eq 0 ]]
then
	cd -
	exit 0
else
	cd -
	exit 1
fi
END
# Hostname config
echo "Password (for host (`hostname`))"
read -s pw_host
echo "Container's hostname"
read container_hostname
echo "Password (for container)"
read -s pw_container
cat > ${SKELETON_DIR}/configs/`hostname`_`whoami`.cnf << END
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
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

# Put hostname- and user-specific config in this file.
# This file must always have perms 0600 for shutit to run.

[container]
# The container you create will have this password for root.
password:${pw_container}
# The container you create will have this hostname during the build.
hostname:${container_hostname}
[host]
# Your username on the host
username:`whoami`
# Your password on the host (set to empty if not required, ie "password:")
password:${pw_host}
[repository]
do_repository_work:yes
# If switched on, will push to docker_io
push:no
repository_server:
#Must be set if do_repository_work is true/yes and user is not blank
#password:YOUR_REGISTRY_PASSWORD_OR_BLANK
#Must be set if do_repository_work is true/yes and user is not blank
#email:YOUR_REGISTRY_PASSWORD_OR_BLANK
# Whether to push to the server
repository_name:${MODULE_NAME}
END
chmod 0600 ${SKELETON_DIR}/configs/defaults.cnf
chmod 0600 ${SKELETON_DIR}/configs/build.cnf
chmod 0600 ${SKELETON_DIR}/configs/`hostname`_`whoami`.cnf
chmod +x ${SKELETON_DIR}/bin/test.sh

pushd ${SKELETON_DIR}
if [[ ! `git status` ]]
then
	git init
	cp ${SHUTIT_DIR}/.gitignore .gitignore
fi
popd

# Run file
touch ${SKELETON_DIR}/run.sh
cat > ${SKELETON_DIR}/run.sh << END
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
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

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

