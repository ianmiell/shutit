#!/bin/bash

[ "x$DOCKER" != "x" ] || DOCKER="docker.io"
[ "x$TESTS" != "x" ] || TEST="basic"

# TODO: do this in this directory and up two/shutit*
find . | grep cnf$ | xargs --no-run-if-empty chmod 0600

# Off for now
SHUTIT_PARALLEL_BUILD=x
readonly SHUTIT_PARALLEL_BUILD

SHUTIT_TEST_REPORT=""

set -o errexit
set -o nounset
#set -x

function set_shutit_options() {
	local CNAME
	local OPTS
	CNAME=shutit_test_container_$$_$(dd if=/dev/urandom bs=256 count=1 2>/dev/null | md5sum | awk '{print $1}')
	OPTS=${1:-none}
	if [[ "$OPTS" = "none" ]]
	then
		export SHUTIT_OPTIONS="-s container name $CNAME"
	else
		export SHUTIT_OPTIONS="-s container name $CNAME $OPTS"
	fi
}

function cleanup() {
	CONTAINERS=$($DOCKER ps -a | grep shutit_test_container_$$ | awk '{print $1}')
	if [[ "x${1:-}" = "xhard" ]]
	then
		$DOCKER kill $CONTAINERS >/dev/null 2>&1 || /bin/true
	fi
	$DOCKER rm $CONTAINERS >/dev/null 2>&1 || /bin/true
}

function failure() {
	echo "============================================"
	echo "FAILED"
	echo "$1"
	echo "============================================"
	SHUTIT_TEST_REPORT+="$$: ${1}\n"
}

function report() {
	echo "SHUTIT_TEST_REPORT:"
	echo "============================================"
	echo -e $SHUTIT_TEST_REPORT
	echo "============================================"
}
