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

$SHUTIT build --debug
$SHUTIT list_configs
$SHUTIT list_configs --history
$SHUTIT list_deps
$SHUTIT list_modules
$SHUTIT list_modules --long

