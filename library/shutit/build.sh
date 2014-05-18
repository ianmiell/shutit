# This file tests your build, leaving the container intact when done.
set -e
../../shutit build --shutit_module_path ../docker:../ssh_server
# Display config
#../../shutit sc
# Debug
#../../shutit build --debug
# Tutorial
#../../shutit build --tutorial
