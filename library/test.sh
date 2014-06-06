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
			set_shutit_options
			if [[ x$SHUTIT_PARALLEL_BUILD = 'x' ]]
			then
				./test.sh "`pwd`/../.."
			else
				./test.sh "`pwd`/../.." &
				PIDS="$PIDS $!"
			fi
		fi
	popd
	fi
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
