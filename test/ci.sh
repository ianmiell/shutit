#!/bin/bash

# Simple CI for ShutIt

# To force a run even if no updates.
FORCE=0

SHUTIT_BUILD_DIR="/tmp/shutit_builddir"
mkdir -p $SHUTIT_BUILD_DIR
LOGFILE="${SHUTIT_BUILD_DIR}/shutit_build_${RANDOM}.log.txt"
touch $LOGFILE

echo $(date) | tee -a $LOGFILE

# Lockfile
LOCKFILE="${SHUTIT_BUILD_DIR}/shutitci.lck"
if [[ -a $LOCKFILE ]]
then
	echo "Already running" | tee $LOGFILE
	rm -rf $SHUTIT_BUILD_DIR
	exit 
else
	touch $LOCKFILE
	# Fetch changes
	git fetch origin master 2>&1 | tee -a $LOGFILE
	# See if there are any incoming changes
	updates=$(git log HEAD..origin/master --oneline | wc -l)
	echo "Updates: $updates" | tee -a $LOGFILE
	if [[ $updates -gt 0 ]] || [[ $FORCE -gt 0 ]]
	then
		echo "Pulling" | tee -a $LOGFILE
		git pull origin master 2>&1 | tee -a $LOGFILE
		# This won't exist in a bit so no point pushd'ing
		cd $SHUTIT_BUILD_DIR
		git clone https://github.com/ianmiell/shutit.git
		cd ${SHUTIT_BUILD_DIR}/shutit/test
		./test.sh 2>&1 | tee -a $LOGFILE || EXIT_CODE=$?
		echo EXIT_CODE:$EXIT_CODE
	        if [[ $EXIT_CODE -ne 0 ]]
		then
			echo "attached" | mail -s "ANGRY SHUTIT" ian.miell@gmail.com -A $LOGFILE
		else
			echo "OK" | mail -s "HAPPY SHUTIT" ian.miell@gmail.com -A $LOGFILE
		fi
		# move aside build dir for reference
		mv ${SHUTIT_BUILD_DIR} ${SHUTIT_BUILD_DIR}.$(date +%s)
	else
		rm -rf $SHUTIT_BUILD_DIR
	fi
	# get rid of /tmp detritus, leaving anything accessed 2 days ago+
	find /tmp/shutit* -type d -atime +1 | rm -rf
fi
