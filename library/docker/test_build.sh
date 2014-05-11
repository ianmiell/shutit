# This file tests your build, removing the container when done.
set -e
export SHUTIT_OPTIONS="$SHUTIT_OPTIONS --shutit_module_path ../ssh_server"
python ../../shutit_main.py -s container rm yes
# Display config
#python ../../shutit_main.py --sc
# Debug
#python ../../shutit_main.py --debug
# Tutorial
#python ../../shutit_main.py --tutorial
