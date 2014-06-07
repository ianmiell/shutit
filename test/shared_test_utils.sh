#!/bin/bash

[ "x$DOCKER" != "x" ] || DOCKER="docker.io"
[ "x$TESTS" != "x" ] || TEST="basic"

# TODO: do this in this directory and up two/shutit*
find . | grep cnf$ | xargs chmod 0600

# Off for now
SHUTIT_PARALLEL_BUILD=$1
readonly SHUTIT_PARALLEL_BUILD

set -o errexit
set -o nounset
#set -x

function set_shutit_options() {
	local CNAME
	CNAME=shutit_test_container_$(dd if=/dev/urandom bs=256 count=1 2>/dev/null | md5sum | awk '{print $1}')
	export SHUTIT_OPTIONS="-s container name $CNAME"
}

function cleanup() {
	CONTAINERS=$($DOCKER ps -a | grep shutit_test_container_ | awk '{print $1}')
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
	cleanup hard
	exit 1
}

