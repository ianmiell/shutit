#!/bin/bash
[[ -z "$SHUTIT" ]] && SHUTIT="$1/shutit"
[[ ! -a "$SHUTIT" ]] || [[ -z "$SHUTIT" ]] && SHUTIT="$(which shutit)"
if [[ ! -a "$SHUTIT" ]]
then
	echo "Must supply path to ShutIt dir or have shutit on path"
	echo "or set SHUTIT to the shutit executable in the env"
	exit 1
fi
pushd ..
$SHUTIT build --shutit_module_path .. "$@"
if [[ $? != 0 ]]
then
	popd
	exit 1
fi
popd
