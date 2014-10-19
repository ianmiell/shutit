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

source ../../test/shared_test_utils.sh

DISTROS=${SHUTITTEST_DISTROS:-ubuntu:12.04}
for dist in $DISTROS
do
	for d in $(ls -d ../* | grep -vw bin)
	do
		declare -A PIDS
		PIDS=()
		if [[ -a $d/bin/test.sh ]]
		then
			pushd $d/bin
			# Set up a random container name for tests to use
			if [[ -a ../STOPTEST ]]
			then
				echo "Skipping $d"
			else
				# Must be done on each iteration as we ned a fresh cid per test run
				set_shutit_options "--image_tag $dist --interactive 0"
				if [[ x$SHUTIT_PARALLEL_BUILD = 'x' ]]
				then
					./test.sh
					if [[ $? != 0 ]]
					then
						echo "FAILURE $d $dist"
						cleanup hard
						exit 1
					fi
					cleanup hard
				else
					LOGFILE="/tmp/shutit_test_parallel_$$_$(dd if=/dev/urandom bs=256 count=1 2>/dev/null | md5sum | awk '{print $1}')"
					./test.sh
					JOB=$!
					PIDS[$JOB]="$JOB: $dist $d"
					sleep 10 #give docker server time to recover
				fi
				set_shutit_options
			fi
		popd
		fi
	done
	if [ x$SHUTIT_PARALLEL_BUILD != 'x' ]
	then
		for P in ${!PIDS[*]}; do
			echo WAITING FOR $P
			wait $P 
			sleep 10 #give docker server time to recover
		done
	fi
	cleanup hard
done
