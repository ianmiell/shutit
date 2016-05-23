#!/bin/bash
# pip release scripts that auto-updates version number and keeps trying until successful
#set -x
set -u
i=0
while true
do
	rm -rf build
	i=$[i+1]
	output=$(grep version= setup.py | awk -F'=' '{print $2}' | sed "s/'\([0-9][0-9]*\)\.\([0-9][0-9]*\)\.\([0-9][0-9]*\)',/\1 \2 \3/")
	major=$(echo $output | awk '{print $1}')
	minor=$(echo $output | awk '{print $2}')
	point=$(echo $output | awk '{print $3}')
	newpoint=$[point+1]
	sed -i "s/\([ \s]\)*version=\(.\)$major.$minor.$point\(.\).*/\1version=\2$major.$minor.$newpoint\3,/" setup.py
	sed -i "s/^shutit_version=\(.\)$major.$minor.[0-9][0-9]*\(.\).*/shutit_version=\1$major.$minor.$newpoint\2/" shutit_main.py
	python setup.py sdist bdist_wheel upload 
	if [[ $? = 0 ]]
	then
		break
	fi
	# wait a minute
	sleep 60
done
echo Success after $i attempts
