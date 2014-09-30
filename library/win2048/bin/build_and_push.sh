#!/bin/bash
export SHUTIT_OPTIONS="$SHUTIT_OPTIONS --config configs/push.cnf"
./build.sh "$@"
