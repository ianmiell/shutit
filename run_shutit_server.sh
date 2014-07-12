ARG=$1
export SHUTIT_PORT=${ARG:-8080}
while [ 1 ]; do ./shutit serve -m library --debug 2>&1 > ~/shutit_server.log; sleep 2; done

#Handy
#for p in $(jot 10 8081); do echo SHUTIT_PORT=$p ./shutit serve -m library \| tee /tmp/shutit_out_$p \&;  done | sh

