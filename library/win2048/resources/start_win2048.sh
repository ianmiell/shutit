#!/bin/bash
# start vnc
rm -rf /tmp/.X*
vncserver << END
1ncharge
1ncharge
END
echo "Did you expose ports 5901 and 6080?"
echo "If so, then vnclient localhost:1 should work."
export DISPLAY=:1
xdotool exec firefox
WID=$(xdotool search --sync --onlyvisible --class firefox)
echo $WID
xdotool sleep 10
killall gnome-terminal
xdotool windowfocus $WID
xdotool key F6
xdotool type http://gabrielecirulli.github.io/2048/
xdotool key KP_Enter

## Example for automating single attempt repeatedly (hitting down on start)
#sleep 2
#xdotool key KP_Down
#sleep 5
#scrot -u /root/a.png
#visgrep -x 0 -y 0 -t 100000 /root/a.png /root/tryagain.pat /root/tryagain.pat
#res=$?
#echo $res
#if [[ $res = 1 ]]
#then
#	echo OK
#else
#	echo FAIL
#fi
#/bin/bash

