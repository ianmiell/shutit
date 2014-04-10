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

[ "x$DOCKER" != "x" ] || DOCKER="sudo docker"

# Check we can use docker
if ! $DOCKER info >/dev/null 2>&1; then
	echo "Failed to run docker! - used command \"$DOCKER info\" to check"
	false
fi

function failure() {
	echo "============================================"
	echo "FAILED"
	echo "$1"
	echo "============================================"
	cleanup hard
	exit 1
}

function cleanup() {
	CONTAINERS=$($DOCKER ps -a | grep shutit_test_container_ | awk '{print $1}')
	if [ "x$1" = "xhard" ]; then
		$DOCKER kill $CONTAINERS >/dev/null 2>&1 || /bin/true
	fi
	$DOCKER rm $CONTAINERS >/dev/null 2>&1 || /bin/true
}

# Set up a random container name for tests to use
# This is a fallback, any tests runnable on their own should include the below
CNAME=shutit_test_container_$(dd if=/dev/urandom bs=256 count=1 2>/dev/null | md5sum | awk '{print $1}')
export SHUTIT_OPTIONS="-s container name $CNAME"

SHUTIT_DIR="`pwd`/.."
if [[ $0 != test.sh ]] && [[ $0 != ./test.sh ]]
then
	echo "Must be run from bin dir of ShutIt"
	exit 1
fi

if [[ "`sed -n '38p' ../docs/shutit_module_template.py`" != "		# Line number 39 should be the next one (so bash scripts can be inserted properly)" ]]
then
	echo "Line 38 of ../docs/shutit_module_template.py should be as per bin/test.sh specifies"
	exit 1
fi

find ${SHUTIT_DIR} -name '*.cnf' | grep '/configs/[^/]*.cnf' | xargs chmod 600

cleanup
echo "Testing skeleton build"
# Do basic test of create_skeleton (can't do complete as may require specific config)
NEWDIR=/tmp/shutit_testing_`hostname`_`whoami`_`date -I`_`date +%N`
./create_skeleton.sh ${NEWDIR} testing ${SHUTIT_DIR}/docs/example.sh
pushd ${NEWDIR}/bin
touch ${SHUTIT_DIR}/test/configs/`hostname`_`whoami`.cnf
chmod 0600 ${SHUTIT_DIR}/test/configs/`hostname`_`whoami`.cnf
./test.sh ${SHUTIT_DIR} || failure "1.0 ${NEWDIR}"
cleanup
popd
rm -rf ${NEWDIR}

# General tests
for d in `ls ../test | grep -v configs`
do
	pushd ${SHUTIT_DIR}/test/$d/bin
	echo "PWD: `pwd`"
	# Just in case only just git cloned/updated
	touch ../configs/`hostname`_`whoami`.cnf
	chmod 0600 ../configs/`hostname`_`whoami`.cnf
	./test.sh ${SHUTIT_DIR} || failure "2.0.`pwd`"
	cleanup
	popd
done

# TODO: full/quick cycle?
# Examples tests
pushd  ${SHUTIT_DIR}/examples/bin
./test.sh || failure "3.0.examples"
popd
cleanup


# OK
echo "================================================================================"
echo "PASSED"
echo "================================================================================"
exit 0


