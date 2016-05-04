#!/bin/bash
for d in [0-9]*
do
	if [[ $d = 14 ]]
	then
		continue
	fi
	pushd $d/bin
	./test.sh
	popd
done
