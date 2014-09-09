#!/bin/bash
# Test the building of this module
if [ $0 != test.sh ] && [ $0 != ./test.sh ]
then
    echo
    echo "Called as: $0"
    echo "Must be run as test.sh or ./test.sh"
    exit
fi
./build.sh
