[ -z "$SHUTIT" ] && SHUTIT="$1/shutit"
[ -z "$SHUTIT" ] && SHUTIT="$(which shutit)"
# Fall back to trying directory of shutit when module was first created
[ -z "$SHUTIT" ] && SHUTIT="../../shutit" ]
if [ -z "$SHUTIT" -o ! -x "$SHUTIT" ]
then
        echo "Must supply path to ShutIt dir or have shutit on path"
        exit 1
fi
# This file tests your build, leaving the container intact when done.
set -e
$SHUTIT build -m ..
# Display config
#$SHUTIT sc
# Debug
#$SHUTIT build --debug
# Tutorial
#$SHUTIT build --interactive 2
