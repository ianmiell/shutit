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
xdotool sleep 10
xdotool key KP_Right

