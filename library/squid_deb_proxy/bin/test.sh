#!/bin/bash
if [ $0 != test.sh ] && [ $0 != ./test.sh ]
then
	echo
	echo "Called as: $0"
	echo "Must be run from module root dir like:"
	echo
	echo "  test.sh <path_to_shutit_dir>"
	echo
	echo "or"
	echo
	echo "  ./test.sh <path_to_shutit_dir>"
	exit
fi
export SHUTIT_OPTIONS="$SHUTIT_OPTIONS"
./build.sh "$@"
