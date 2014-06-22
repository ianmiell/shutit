#!/bin/bash
#The MIT License (MIT)
#
#Copyright (C) 2014 OpenBet Limited
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of
#this software and associated documentation files (the "Software"), to deal in
#the Software without restriction, including without limitation the rights to
#use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#of the Software, and to permit persons to whom the Software is furnished to do
#so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

source ../test/shared_test_utils.sh

PIDS=""
BUILD_REPORT=""
for dist in ubuntu:10.04 ubuntu:12.04 ubuntu:12.10 ubuntu:13.10 ubuntu:14.04 ubuntu:13.04 debian:experimental debian:6.0.9 debian:7.5 debian:jessie debian:oldstable debian:sid debian:7.4 debian:6.0.8 debian:7.3
do
	for d in *
	do
		cleanup
		if [[ -a $d/test.sh ]]
		then
			pushd $d
			# Set up a random container name for tests to use
			if [[ -a STOP ]]
			then
				echo "Skipping $d"
			else
				# Must be done on each iteration as we ned a fresh cid per test run
				set_shutit_options "--image_tag $dist"
				if [[ x$SHUTIT_PARALLEL_BUILD = 'x' ]]
				then
					./test.sh "`pwd`/../.." || BUILD_REPORT+="\nFAILED $dist $d"
				else
					./test.sh "`pwd`/../.." || BUILD_REPORT+="\nFAILED $dist $d" &
					PIDS="$PIDS $!"
				fi
			fi
		popd
		fi
	done
done


if [ x$SHUTIT_PARALLEL_BUILD != 'x' ]
then
	for P in $PIDS; do
		echo "PIDS: $PIDS"
		echo "WAITING ON: $P"
		wait $P
		echo "PIDS: $PIDS"
		echo "FINISHED: $P"
	done
fi

if [[ $BUILD_REPORT != "" ]]
	echo $BUILD_REPORT
	exit 1
fi
