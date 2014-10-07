#!/bin/bash
# stop vnc
ps -ef | grep Xvnc4 | grep -v grep | awk '{print $2}' | xargs kill
sleep 10', '/root/stop_vnc.sh
rm -rf /tmp/.X*-lock', '/root/stop_vnc.sh

