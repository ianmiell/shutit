#!/bin/bash
export SHUTIT_OPTIONS="$SHUTIT_OPTIONS --config configs/push.cnf -s repository push yes"
./build.sh "$@"
