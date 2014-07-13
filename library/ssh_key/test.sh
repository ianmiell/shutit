#!/bin/bash
# Test the building of this module
set -e
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
./build.sh $1

