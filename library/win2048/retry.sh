#!/bin/bash
echo "Input keys, eg \"Right Left Down Up\", Left, Up, Down, or blank for no key"
read keys
echo "Input image, default is: $(whoami)/2048"
read image
if [[ $image = '' ]]
then
	image=$(whoami)/2048
fi
while [ 1 ]
do
	echo "Running with: $keys being pressed on image: $image"
	sudo docker run -t -i -p 5901:5901 -p 6080:6080 -e keys="$keys" -e HOME=/root $image /root/start_win2048.sh
	echo "CTRL-C now to exit"
	sleep 2
done
