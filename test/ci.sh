#!/bin/bash

# Simple CI for ShutIt

# To force a run even if no updates.
FORCE_ARG=$1
VERBOSE_ARG=$2
FORCE=${FORCE_ARG:-0}
VERBOSE=${VERBOSE_ARG:-0}

if [[ $VERBOSE -gt 0 ]]
then
	set +x
fi

SHUTIT_BUILD_DIR="/tmp/shutitci/shutit_builddir"
mkdir -p $SHUTIT_BUILD_DIR
LOGFILE="${SHUTIT_BUILD_DIR}/shutit_build_${RANDOM}.log.txt"
SHUTITLOGFILE="${SHUTIT_BUILD_DIR}/shutit_build.log.txt"
touch $SHUTITLOGFILE

echo $(date) 2>&1 | tee -a $SHUTITLOGFILE

# Lockfile
LOCKFILE="${SHUTIT_BUILD_DIR}/shutitci.lck"
if [[ -a $LOCKFILE ]]
then
	echo "Already running" | tee -a $SHUTITLOGFILE
	exit 
else
	touch $LOGFILE
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
		pushd $SHUTIT_BUILD_DIR
		git clone https://github.com/ianmiell/shutit.git
		popd
		pushd ${SHUTIT_BUILD_DIR}/shutit/test
		./test.sh >> ${LOGFILE} 2>&1
		EXIT_CODE=$?
	        if [[ $EXIT_CODE -ne 0 ]]
		then
			echo "attached" | mail -s "ANGRY SHUTIT" ian.miell@gmail.com -A $LOGFILE
		else
			echo "OK" | mail -s "HAPPY SHUTIT" ian.miell@gmail.com -A $LOGFILE
		fi
		popd
	fi
	# get rid of /tmp detritus, leaving anything accessed 2 days ago+
	find /tmp/shutitci/* -type d -atime +1 | rm -rf
fi
