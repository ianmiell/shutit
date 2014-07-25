if [[ x$2 != 'x' ]]
then
	echo "build.sh takes exactly one argument at most"
	exit 1
fi
[ -z "$SHUTIT" ] && SHUTIT="$1/shutit"
[ -z "$SHUTIT" ] && SHUTIT="$(which shutit)"
[ -z "$SHUTIT" ] && SHUTIT="../../shutit"
if [ -z "$SHUTIT" -o ! -x "$SHUTIT" ]
then
	echo "Must supply path to ShutIt dir or have shutit on path"
	exit 1
fi
# This file tests your build, leaving the container intact when done.

$SHUTIT build
# Display config
#$SHUTIT sc
# Debug
#$SHUTIT build --debug
# Interactive build
#$SHUTIT build --interactive 1
# Tutorial
#$SHUTIT build --interactive 2
