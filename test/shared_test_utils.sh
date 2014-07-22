#!/bin/bash

[ "x$DOCKER" != "x" ] || DOCKER="docker.io"
[ "x$TESTS" != "x" ] || TEST="basic"

# TODO: do this in this directory and up two/shutit*
find . | grep cnf$ | xargs --no-run-if-empty chmod 0600

# Off for now
SHUTIT_PARALLEL_BUILD=
readonly SHUTIT_PARALLEL_BUILD
BUILD_REF=$(dd if=/dev/urandom bs=256 count=1 2>/dev/null | md5sum | awk '{print $1}' | sed 's/^\(....\).*/\1/')
readonly BUILD_REF

function get_abs_filename() {
        # $1 : relative filename
        echo "$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
}
export SHUTIT=$(get_abs_filename $(dirname ${BASH_SOURCE[0]})/../shutit)
readonly SHUTIT
SHUTIT_TEST_REPORT=""

set -o errexit
set -o nounset
#set -x


function set_shutit_options() {
	local CNAME
	local OPTS
	CNAME=shutit_test_container_${BUILD_REF}_$(dd if=/dev/urandom bs=256 count=1 2>/dev/null | md5sum | awk '{print $1}')
	OPTS=${1:-none}
	if [[ "$OPTS" = "none" ]]
	then
		export SHUTIT_OPTIONS="-s container name $CNAME"
	else
		export SHUTIT_OPTIONS="-s container name $CNAME $OPTS"
	fi
	CNAME=shutit_test_container_${BUILD_REF}_$(dd if=/dev/urandom bs=256 count=1 2>/dev/null | md5sum | awk '{print $1}')
}

function cleanup() {
	CONTAINERS=$($DOCKER ps -a | grep shutit_test_container_${BUILD_REF} | awk '{print $1}')
	if [[ "x$CONTAINERS" != "x" ]]
	then
		if [[ "x${1:-}" = "xhard" ]]
		then
			echo "Force-removing containers: $CONTAINERS"
			$DOCKER rm -f $CONTAINERS
		else
			echo "Removing containers: $CONTAINERS"
			$DOCKER rm $CONTAINERS || /bin/true
		fi
	fi
}

function failure() {
	echo "============================================"
	echo "FAILED"
	echo "$1"
	echo "============================================"
	SHUTIT_TEST_REPORT+="$$: ${1}\n"
}

function report() {
	if [[ "x$SHUTIT_TEST_REPORT" != "x" ]]
	then
		echo "SHUTIT_TEST_REPORT:"
		echo "============================================"
		echo -e $SHUTIT_TEST_REPORT
		echo "============================================"
	fi
}



