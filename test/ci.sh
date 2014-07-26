#!/bin/bash

# Simple CI for ShutIt

FORCE=1
LOCKFILE="/tmp/shutitci.lck"
if [[ -a $LOCKFILE ]]
then
	echo "Already running"
	exit 
fi

touch $LOCKFILE

git fetch origin master
# See if there are any incoming changes
updates=$(git log HEAD..origin/master --oneline | wc -l)
git log HEAD..origin/master --oneline 
git log HEAD..origin/master --oneline | wc -l
if [[ $updates -gt 0 ]] || [[ $FORCE -gt 0 ]]
then
	git pull origin master
	id=$RANDOM
	./test.sh > /tmp/shutitci_${id}.txt || EXIT_CODE=$?
        if [[ $EXIT_CODE -ne 0 ]] || [[ $FORCE -gt 0 ]]
	then
		cat /tmp/shutitci_${id}.txt | mail ian.miell@gmail.com
	fi
	rm -f /tmp/shutitci_*txt
fi

rm -f $LOCKFILE
