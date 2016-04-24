#!/bin/bash
#set -x
set -u
while true
do
	output=$(grep version= setup.py | awk -F'=' '{print $2}' | sed "s/'\([0-9][0-9]*\)\.\([0-9][0-9]*\)\.\([0-9][0-9]*\)',/\1 \2 \3/")
	major=$(echo $output | awk '{print $1}')
	minor=$(echo $output | awk '{print $2}')
	point=$(echo $output | awk '{print $3}')
	newpoint=$[point+1]
	sed -i "s/\([ \s]\)*version=\(.\)$major.$minor.$point\(.\).*/\1version=\2$major.$minor.$newpoint\3,/" setup.py
	sed -i "s/^shutit_version=\(.\)$major.$minor.$point\(.\).*/shutit_version=\1$major.$minor.$newpoint\2/" shutit_main.py
	python setup.py sdist  bdist_wheel upload 
	if [[ $? = 0 ]]
	then
		break
	fi
done
