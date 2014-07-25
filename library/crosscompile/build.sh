if [[ x$2 != 'x' ]]
then
	echo "build.sh takes exactly one argument at most"
	exit 1
fi
[[ -z "$SHUTIT" ]] && SHUTIT="$1/shutit"
[[ ! -a "$SHUTIT" ]] || [[ -z "$SHUTIT" ]] && SHUTIT="$(which shutit)"
[[ ! -a "$SHUTIT" ]] || [[ -z "$SHUTIT" ]] && SHUTIT="../../shutit"
# Fall back to trying directory of shutit when module was first created
[[ ! -a "$SHUTIT" ]] && SHUTIT="/space/git/shutit/shutit"
if [[ ! -a "$SHUTIT" ]]
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
# Honour pause points
#$SHUTIT build --interactive 1
# Interactive build
#$SHUTIT build --interactive 2
# Tutorial
#$SHUTIT build --interactive 3
