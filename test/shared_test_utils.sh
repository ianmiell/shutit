#!/bin/bash

[ "x$DOCKER" != "x" ] || DOCKER="docker"
[ "x$TESTS" != "x" ] || TEST="basic"

# TODO: do this in this directory and up two/shutit*
find . | grep cnf$ | xargs --no-run-if-empty chmod 0600

# Off for now
SHUTIT_PARALLEL_BUILD=
readonly SHUTIT_PARALLEL_BUILD
BUILD_REF=$$
readonly BUILD_REF

function get_abs_filename() {
        # $1 : relative filename
        echo "$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
}
export SHUTITDIR=${SHUTITDIR:-$(get_abs_filename $(dirname ${BASH_SOURCE[0]})/..)}
export SHUTIT=${SHUTIT:-${SHUTITDIR}/shutit}
readonly SHUTIT SHUTITDIR

SHUTIT_TEST_REPORT=""

# Default distros
#SHUTITTEST_DISTROS=${SHUTITTEST_DISTROS:-phusion/baseimage ubuntu:12.04 ubuntu:14.04 debian:7.5 fedora:20}
SHUTITTEST_DISTROS=${SHUTITTEST_DISTROS:-ubuntu:14.04}

set -o nounset

function set_shutit_options() {
	local CNAME
	local OPTS
	CNAME=shutit_test_container_${BUILD_REF}
	OPTS=${1:-none}
	if [[ "$OPTS" = "none" ]]
	then
		export SHUTIT_OPTIONS="-s target name $CNAME -s repository tag no --interactive 0 --imageerrorok"
	else
		export SHUTIT_OPTIONS="-s target name $CNAME $OPTS -s repository tag no --interactive 0 --imageerrorok"
	fi
}

function cleanup() {
	CONTAINERS=$($DOCKER ps -a | grep shutit_test_container_${BUILD_REF} | awk '{print $1}')
	if [[ "x$CONTAINERS" != "x" ]]
	then
		if [[ "x${1:-}" = "xhard" ]]
		then
			echo "Force-removing containers: $CONTAINERS"
			# Has been seen to fail - this is best endeavours
			# Sometimes you have to wait
			$DOCKER rm -f $CONTAINERS || (sleep 60 && $DOCKER rm -f $CONTAINERS)
		else
			echo "Removing containers: $CONTAINERS"
			# Has been seen to fail - this is best endeavours
			$DOCKER rm $CONTAINERS || (sleep 60 && $DOCKER rm $CONTAINERS)
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

