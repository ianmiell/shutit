#!/bin/bash

# Simple CI for ShutIt

# To force a run even if no updates.
FORCE=0

SHUTIT_BUILD_DIR="/tmp/shutit_builddir"
mkdir -p $SHUTIT_BUILD_DIR
LOGFILE="${SHUTIT_BUILD_DIR}/shutit_build_${RANDOM}.log.txt"

echo $(date) >> $LOGFILE

# Lockfile
LOCKFILE="${SHUTIT_BUILD_DIR}/shutitci.lck"
if [[ -a $LOCKFILE ]]
then
	echo "Already running" >> $LOGFILE
	rm -rf $SHUTIT_BUILD_DIR
	exit 
else
	touch $LOCKFILE
	# Fetch changes
	git fetch origin master
	# See if there are any incoming changes
	updates=$(git log HEAD..origin/master --oneline | wc -l)
	echo "Updates: $updates"
	if [[ $updates -gt 0 ]] || [[ $FORCE -gt 0 ]]
	then
		echo "Pulling"
		git pull origin master
		pushd $SHUTIT_BUILD_DIR
		git clone https://github.com/ianmiell/shutit.git
		popd
		pushd ${SHUTIT_BUILD_DIR}/shutit/test
		./test.sh | tee $LOGFILE 2>&1 || EXIT_CODE=$?
		echo EXIT_CODE:$EXIT_CODE
	        if [[ $EXIT_CODE -ne 0 ]]
		then
			echo "attached" | mail -s "ANGRY SHUTIT" ian.miell@gmail.com -A $LOGFILE
			cp -r $SHUTIT_BUILD_DIR $SHUTIT_BUILD_DIR.$(date +%s)
		else
			echo OK | mail -s "HAPPY SHUTIT" ian.miell@gmail.com -A $LOGFILE
		fi
	fi
	# get rid of /tmp detritus, leaving anything accessed 2 days ago+
	mv ${SHUTIT_BUILD_DIR} ${SHUTIT_BUILD_DIR}.$(date +%s)
	find /tmp/shutit* -type d -atime +1 | rm -rf
	popd
fi
