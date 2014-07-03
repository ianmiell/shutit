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

for dist in ubuntu:12.04 ubuntu:12.10 ubuntu:13.10 ubuntu:14.04 ubuntu:13.04 debian:experimental debian:6.0.9 debian:7.5 debian:7.4 debian:6.0.8 debian:7.3
do
	for d in *
	do
		declare -A PIDS
		PIDS=()
		if [[ -a $d/test.sh ]]
		then
			pushd $d
			# Set up a random container name for tests to use
			if [[ -a STOP ]]
			then
				echo "Skipping $d"
			else
				# Must be done on each iteration as we ned a fresh cid per test run
				set_shutit_options "--image_tag $dist --interactive 0"
				if [[ x$SHUTIT_PARALLEL_BUILD = 'x' ]]
				then
					./test.sh "`pwd`/../.." || failure "FAILED $dist $d"
					report
				else
					LOGFILE="/tmp/shutit_test_parallel_$$_$(dd if=/dev/urandom bs=256 count=1 2>/dev/null | md5sum | awk '{print $1}')"
					./test.sh "`pwd`/../.." 2>&1 | tee $LOGFILE &
					JOB=$!
					PIDS[$JOB]="$JOB: $dist $d"
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
			wait $P || failure "FAILED: ${PIDS[$P]}"
			report
		done
	fi
done

cleanup nothard
