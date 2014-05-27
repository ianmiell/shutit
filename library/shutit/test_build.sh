# This file tests your build, removing the container when done.
set -e
../../shutit build --shutit_module_path ../docker:../adduser -s container rm yes
# Display config
#../../shutit sc
# Debug
#../../shutit build --debug
# Tutorial
#../../shutit build --tutorial
