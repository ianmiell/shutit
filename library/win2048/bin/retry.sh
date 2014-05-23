#!/bin/bash
echo "Input key, eg Right, Left, Up, Down, or blank for no key"
read key
echo "Input image, default is: $(whoami)/2048"
read image
if [[ $image = '' ]]
	image=$(whoami)/2048
while [ 1 ]; do sudo docker run -t -i -p 5902:5901 -p 6081:6080 -e key=$key -e HOME=/root $image /root/start_vnc.sh; echo "CTRL-C now to exit"; sleep 2; done
