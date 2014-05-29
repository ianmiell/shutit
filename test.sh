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

set -x

TESTS=$1

source test/shared_test_utils.sh

# Variables
NEWDIR=/tmp/shutit_testing_$(hostname)_$(whoami)_$(date -I)_$(date +%N)
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
	echo "Must be run from root dir of ShutIt"
	exit 1
fi

if [[ "$(sed -n '41p' docs/shutit_module_template.py)" != "		# Line number 42 should be the next one (so bash scripts can be inserted properly)" ]]
then
	echo "Line 41 of docs/shutit_module_template.py should be as test.sh specifies"
	exit 1
fi

PYTHONPATH=$(pwd) python test/test.py || failure "Unit tests"

find ${SHUTIT_DIR} -name '*.cnf' | grep '/configs/[^/]*.cnf' | xargs chmod 600

cleanup nothard
echo "Testing skeleton build"
./shutit skeleton ${NEWDIR} testing shutit.tk ${SHUTIT_DIR}/docs/example.sh
pushd ${NEWDIR}
touch ${NEWDIR}/configs/$(hostname)_$(whoami).cnf
chmod 0600 ${NEWDIR}/configs/$(hostname)_$(whoami).cnf
./test.sh ${SHUTIT_DIR} || failure "1.0 ${NEWDIR}"
cleanup nothard
rm -rf ${NEWDIR}
popd

PIDS=""
# General tests
for d in $(ls test | grep -v configs)
do
	[ -d ${SHUTIT_DIR}/test/$d ] || continue
	pushd ${SHUTIT_DIR}/test/$d
	if [[ -a STOP ]]
	then
		echo "STOP file found in $(pwd)"
	else
		echo "PWD: $(pwd)"
		# Just in case only just git cloned/updated
		touch configs/$(hostname)_$(whoami).cnf
		chmod 0600 configs/$(hostname)_$(whoami).cnf
		if [ x$SHUTIT_PARALLEL_BUILD = 'x' ]
		then
			./test.sh ${SHUTIT_DIR}
		else
			./test.sh ${SHUTIT_DIR} &
			PIDS="$PIDS $!"
		fi
		cleanup nothard
		set_shutit_options
	fi
	popd
done

readonly PIDS
if [ x$SHUTIT_PARALLEL_BUILD != 'x' ]
then
	echo "PIDS: $PIDS"
	for P in $PIDS; do
		echo "WAITING ON: $P"
		wait $P
		echo "FINISHED: $P"
	done
fi

# Examples tests
if [[ $TESTS != 'basic' ]]
then
	pushd  ${SHUTIT_DIR}/library
	./test.sh || failure "3.0.library"
	popd
	cleanup nothard
fi

# OK
echo "================================================================================"
echo "PASSED"
echo "================================================================================"
exit 0


