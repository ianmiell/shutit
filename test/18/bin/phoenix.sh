#!/bin/bash
set -e
DOCKER=${DOCKER:-docker}
CONTAINER_BASE_NAME=${CONTAINER_BASE_NAME:-test18}
# haproxy image suffix
#                             Sent on to:
#                             HA_BACKEND_PORT_A
#                                   +
#                                   |
#            +------------------+   |    +----------------+
#            |                  |   |    |  Container A   |
#            |                  +---v---->  Open on port: |
#            |    HAProxy       |        |  CONTAINER_PORT|
#            |    Container     |        |                |
#            |                  |        +----------------+
#Request+---->received          |
#            |on port:          |        +----------------+
#            |HA_PROXY_PORT     |        |  Container B   |
#            |                  +---+---->  Open on port: |
#            |                  |   ^    |  CONTAINER_PORT|
#            |                  |   |    |                |
#            +------------------+   |    +----------------+
#                                   |
#                                   +
#                              Sent on to:
#                              HA_BACKEND_PORT_B
#
HA_PROXY_CONTAINER_SUFFIX=${HA_PROXY_CONTAINER_SUFFIX:-haproxy}
# The port on which your haproxy image is configured to receive requests from inside
HA_PROXY_PORT=${HA_PROXY_PORT:-8080}
# The port on which your backend 'a' is configured to receive requests on the host
HA_BACKEND_PORT_A=${HA_BACKEND_PORT_A:-8081}
# The port on which your backend 'b' is configured to receive requests on the host
HA_BACKEND_PORT_B=${HA_BACKEND_PORT_B:-8082}
# The port on which your service container receives requests
CONTAINER_PORT=${CONTAINER_PORT:-80}

# Set up haproxy.
# Remove proxy if it's died. If it doesn't exist, rebuild it first.
HAPROXY=$($DOCKER ps --filter=name=${CONTAINER_BASE_NAME}_${HA_PROXY_CONTAINER_SUFFIX} -q)
if [[ $HAPROXY = '' ]]
then
	HAPROXY=$($DOCKER ps --filter=name=${CONTAINER_BASE_NAME}_${HA_PROXY_CONTAINER_SUFFIX} -q -a)
	if [[ $HAPROXY != '' ]]
	then
		$DOCKER rm -f ${CONTAINER_BASE_NAME}_${HA_PROXY_CONTAINER_SUFFIX}
	fi
	pushd ../haproxy
	sed "s/HA_PROXY_PORT/${HA_PROXY_PORT}/g;s/HA_BACKEND_PORT_A/${HA_BACKEND_PORT_A}/g;s/HA_BACKEND_PORT_B/${HA_BACKEND_PORT_B}/g" haproxy.cfg.template > haproxy.cfg
	$DOCKER build -t ${CONTAINER_BASE_NAME}_${HA_PROXY_CONTAINER_SUFFIX} .
	$DOCKER run -d --net=host --name ${CONTAINER_BASE_NAME}_${HA_PROXY_CONTAINER_SUFFIX} ${CONTAINER_BASE_NAME}_${HA_PROXY_CONTAINER_SUFFIX}
	popd
fi

# Cleanup any left-over containers, build the new one, rename the old one,
# rename the new one, delete the old one.
$DOCKER rm -f ${CONTAINER_BASE_NAME}_old > /dev/null 2>&1 || /bin/true
./build.sh -s repository tag yes -s repository name ${CONTAINER_BASE_NAME}
# If there's a running instance, gather the used port, and move any old container
USED_PORT=''
NEW_PORT=${HA_BACKEND_PORT_A}
if [[ $($DOCKER ps --filter=name="${CONTAINER_BASE_NAME}$" -q -a) != '' ]]
then
	$DOCKER rm -f ${CONTAINER_BASE_NAME}_old > /dev/null 2>&1 || /bin/true
	USED_PORT=$($DOCKER inspect -f '{{range $p, $conf := .NetworkSettings.Ports}}{{(index $conf 0).HostPort}} {{end}}' $CONTAINER_BASE_NAME)
	# Decide which port to use
	if [[ "$USED_PORT" -eq "${HA_BACKEND_PORT_A}" ]]
	then
		NEW_PORT=${HA_BACKEND_PORT_B}
	fi
	$DOCKER rename ${CONTAINER_BASE_NAME} ${CONTAINER_BASE_NAME}_old
fi
# The random id is required - suspected docker bug
RANDOM_ID=$RANDOM
./run.sh -i "${CONTAINER_BASE_NAME}" -c "${CONTAINER_BASE_NAME}_${RANDOM_ID}" -a "-p ${NEW_PORT}:${CONTAINER_PORT}"
$DOCKER rm -f ${CONTAINER_BASE_NAME}_old > /dev/null 2>&1 || /bin/true
$DOCKER rename ${CONTAINER_BASE_NAME}_${RANDOM_ID} ${CONTAINER_BASE_NAME}