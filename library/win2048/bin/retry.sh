#!/bin/bash
echo "Input key, eg Right, Left, Up, Down, or blank for no key"
read key
while [ 1 ]; do sudo docker run -t -i -p 5902:5901 -p 6081:6080 -e key=$key -e HOME=/root imiell/2048 /root/start_vnc.sh; done
