#!/bin/bash
# Test the building of this module
set -e
if [[ $0 != test.sh ]] && [[ $0 != ./test.sh ]]
then
        echo 
        echo "Called as: $0"
	echo "Must be run from test dir like:"
        echo
        echo "  test.sh <path_to_shutit_dir>"
        echo
        echo "or"
        echo
        echo "  ./test.sh <path_to_shutit_dir>"
        exit
fi
if [ x$1 = 'x' ]
then
	echo "Must supply path to core ShutIt directory"
	exit 1
fi
./test_build.sh
if [[ $? -eq 0 ]]
then
	exit 0
else
	exit 1
fi
