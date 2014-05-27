set -e
../../shutit build --config configs/push.cnf -m ../docker:../adduser:../ssh_server
# Display config
#../../shutit sc
# Debug
#../../shutit build --debug
# Tutorial
#../../shutit build --tutorial
