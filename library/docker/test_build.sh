# This file tests your build, removing the container when done.
set -e
../../shutit build -s container rm yes --shutit_module_path ../ssh_server
# Display config
#../../shutit sc
# Debug
#../../shutit build --debug
# Tutorial
#../../shutit build --tutorial
