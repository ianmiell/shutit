#export SHUTIT_PORT=9080
while [ 1 ]; do ./shutit serve -m library --debug 2>&1 > ~/shutit_server.log; sleep 2; done
