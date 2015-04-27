#!/bin/bash

#Copyright (C) 2014 OpenBet Limited

#Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
if [ x$1 = 'x' ]
then
	echo "Must supply path to shutit directory"
	exit 1
fi
# Set up a random container name for tests to use
CNAME=shutit_test_container_$(dd if=/dev/urandom bs=256 count=1 2>/dev/null | md5sum | awk '{print $1}')
export SHUTIT_OPTIONS="-s container name $CNAME"

# sshd problems with fedora and ssh - need to check up on pexcpssh.py
#cd ..
#python ${1}/shutit_main.py --image_tag fedora --debug
#if [[ $? -eq 0 ]]
#then
#	cd -
#else
#	cd -
#        exit 1
#fi

#cd ..
#python ${1}/shutit_main.py --image_tag centos --debug
#if [[ $? -eq 0 ]]
#then
#	cd -
#else
#	cd -
#        exit 1
#fi

../../shutit build --image_tag debian:6.0.9 --shutit_module_path ..
