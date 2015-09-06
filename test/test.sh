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

TESTS=${1:-basic}

pushd $(dirname ${BASH_SOURCE[0]})/.. > /dev/null 2>&1

#set -x

source test/shared_test_utils.sh

# Variables
NEWDIR=/tmp/shutit_testing_$$_$(hostname)_$(whoami)_$(date -I)_$(date +%N)
SHUTIT_DIR="$(pwd)"
readonly NEWDIR SHUTIT_DIR

set_shutit_options

# Check we can use docker
if ! $DOCKER info >/dev/null 2>&1; then
	echo "Failed to run docker! - used command \"$DOCKER info\" to check"
	false
fi

# This is a fallback, any tests runnable on their own should include the below
if [[ $0 != test.sh ]] && [[ $0 != ./test.sh ]]
then
	echo "Must be run from dir of test.sh"
	exit 1
fi

if [[ "$(sed -n '10p' assets/shutit_module_template_bare.py)" != "	def build(self, shutit):" ]]
then
	echo "Line 10 of assets/shutit_module_template_bare.py should be as test.sh specifies"
	exit 1
fi

#PYTHONPATH=$(pwd) python test/test.py 

find ${SHUTIT_DIR} -name '*.cnf' | grep '/configs/[^/]*.cnf' | xargs chmod 600
cleanup hard

DESC="Testing skeleton build with Dockerfile"
echo $DESC
./shutit skeleton --dockerfile assets/dockerfile/Dockerfile --module_directory ${NEWDIR} --module_name testing --domain shutit.tk --depends shutit.tk.setup --base_image ubuntu:14.04 --delivery docker
pushd ${NEWDIR}/bin
./test.sh --interactive 0
if [[ "x$?" != "x0" ]]
then
	echo "FAILED ON $DESC: $?"
	cleanup hard
	exit 1
fi
cleanup hard
rm -rf ${NEWDIR}
popd > /dev/null 2>&1

DESC="Testing skeleton build basic bare"
echo $DESC
./shutit skeleton --module_directory ${NEWDIR} --module_name testing --domain shutit.tk --depends shutit.tk.setup --base_image ubuntu:14.04 --delivery docker
pushd ${NEWDIR}/bin
./test.sh --interactive 0
if [[ "x$?" != "x0" ]]
then
	echo "FAILED ON $DESC"
	cleanup hard
	exit 1
fi
cleanup hard
rm -rf ${NEWDIR}
popd > /dev/null 2>&1


DESC="Testing skeleton build basic with example script"
echo $DESC
./shutit skeleton --module_directory ${NEWDIR} --module_name testing --domain shutit.tk --depends shutit.tk.setup --base_image ubuntu:14.04 --script ${SHUTIT_DIR}/assets/example.sh --delivery docker

pushd ${NEWDIR}/bin
./test.sh --interactive 0
if [[ "x$?" != "x0" ]]
then
	echo "FAILED ON $DESC"
	cleanup hard
	exit 1
fi
cleanup hard
rm -rf ${NEWDIR}
popd > /dev/null 2>&1

pushd ${SHUTIT_DIR}/test/11
shutit build --delivery bash
RES=$?
if [[ "x$RES" != "x0" ]]
then
	echo "FAILURE |$RES| in: $(pwd) running test.sh"
	cleanup hard
	exit 1
fi
popd

# General tests
mkdir -p /tmp/shutit_logs/$$
declare -A PIDS
PIDS=()
DISTROS=${SHUTITTEST_DISTROS:-ubuntu:14.04}
for dist in $DISTROS
do
	for d in $(ls -d test/[0-9][0-9]* | sort -n)
	do
		[ -d ${SHUTIT_DIR}/$d ] || continue
		pushd ${SHUTIT_DIR}/$d/bin
		if [[ -a STOPTEST ]]
		then
			echo "STOPTEST file found in $(pwd)"
		else 
			if [[ -a /tmp/SHUTITSTOPTEST ]]
			then
				echo "/tmp/SHUTITSTOPTEST file found in /tmp"
			else
				# Must be done on each iteration as we ned a fresh cid per test run
				set_shutit_options "--image_tag $dist --interactive 0 --imageerrorok"
				echo "================================================================================"
				echo "SHUTIT MODULE TEST $d: In directory: `pwd` BEGIN"
				echo "================================================================================"
				if [ x$SHUTIT_PARALLEL_BUILD = 'x' ]
				then
					./test.sh --interactive 0
					RES=$?
					if [[ "x$RES" != "x0" ]]
					then
						echo "FAILURE |$RES| in: $(pwd) running test.sh"
						cleanup hard
						exit 1
					fi
					cleanup hard
					echo "================================================================================"
					echo "SHUTIT MODULE TEST $d: In directory: `pwd` END"
					echo "================================================================================"
				else
					# TODO
					#http://stackoverflow.com/questions/356100/how-to-wait-in-bash-for-several-subprocesses-to-finish-and-return-exit-code-0
					./test.sh --interactive 0
					JOB=$!
					PIDS[$JOB]="$JOB: $dist $d"
				fi
				set_shutit_options
			fi
		fi
		report
		popd
	done
done

if [ x$SHUTIT_PARALLEL_BUILD != 'x' ]
then
	for P in ${!PIDS[*]}; do
		echo "WAITING FOR $P"
		wait $P 
		if [[ $? != 0 ]]
		then
			cleanup hard
			exit 1
		fi
		report
		cleanup nothard
	done
fi

report
cleanup hard

popd > /dev/null 2>&1
# OK
echo "SHUTIT TEST OK"
exit

