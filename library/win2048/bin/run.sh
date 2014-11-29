# Example for running
docker run -t -d -p 5901:5901 -p 6080:6080 imiell/win2048 /bin/bash -c '/root/start_win2048.sh && sleep infinity'
sleep 5
vncviewer localhost:1
