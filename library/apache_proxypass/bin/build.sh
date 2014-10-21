#!/bin/bash
[ -z "$SHUTIT" ] && SHUTIT="$1/shutit"
[[ ! -a "$SHUTIT" ]] || [[ -z "$SHUTIT" ]] && SHUTIT="$(which shutit)"
[[ ! -a "$SHUTIT" ]] || [[ -z "$SHUTIT" ]] && SHUTIT="../../shutit"
[[ ! -a "$SHUTIT" ]] || [[ -z "$SHUTIT" ]] && SHUTIT="~/shutit"
# Fall back to trying directory of shutit when module was first created
[[ ! -a "$SHUTIT" ]] && SHUTIT="''' + shutit_dir + '''/shutit"
if [[ ! -a "$SHUTIT" ]]
then
	echo "Must supply path to ShutIt dir or have shutit on path"
	exit 1
fi
# This file tests your build, leaving the container intact when done.
pushd ..
$SHUTIT build "$@"
if [[ $? != 0 ]]
then
        popd
        exit 1
fi
popd
