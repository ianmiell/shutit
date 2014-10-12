#!/bin/bash

count=0
output=""
file=/root/words.txt
while [[ /bin/true ]]
do
	while [[ $count -lt $RANDOM ]];
	do
		count=$(expr $count + 1)
		output="$output $(shuf -n 1 $file)"
	done
	echo $output
done
