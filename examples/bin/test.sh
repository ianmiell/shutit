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
set -e
[ "x$DOCKER" != "x" ] || DOCKER="sudo docker"

function cleanup() {
	CONTAINERS=$($DOCKER ps -a | grep shutit_test_container_ | awk '{print $1}')
	if [ "x$1" = "xhard" ]; then
		$DOCKER kill $CONTAINERS >/dev/null 2>&1 || /bin/true
	fi
	$DOCKER rm $CONTAINERS >/dev/null 2>&1 || /bin/true
}


PIDS=""
dirs=`ls ../ | grep -vw bin | grep -v README`
for d in $dirs
do
	cleanup
	pushd ../$d/bin
	# Set up a random container name for tests to use
	CNAME=shutit_test_container_$(dd if=/dev/urandom bs=256 count=1 2>/dev/null | md5sum | awk '{print $1}')
	export SHUTIT_OPTIONS="-s container name $CNAME"
	./test.sh &
	PIDS="$PIDS $!"
	popd
done

for P in $PIDS; do
	echo "PIDS: $PIDS"
	echo "WAITING ON: $P"
	wait $P
	echo "PIDS: $PIDS"
	echo "FINISHED: $P"
done
