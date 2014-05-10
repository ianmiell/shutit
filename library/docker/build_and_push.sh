set -e
python /space/git/shutit/bin/../shutit_main.py --config configs/push.cnf
# Display config
#python /space/git/shutit/bin/../shutit_main.py --sc
# Debug
touch /space/git/shutit/library/docker/test_build.sh
cat >> /space/git/shutit/library/docker/test_build.sh << END
set -e
python /space/git/shutit/bin/../shutit_main.py -s container rm yes
# Display config
#python /space/git/shutit/bin/../shutit_main.py --sc
# Debug
#python /space/git/shutit/bin/../shutit_main.py --debug
# Tutorial
#python /space/git/shutit/bin/../shutit_main.py --tutorial
set -e
python /space/git/shutit/bin/../shutit_main.py --config configs/push.cnf
# Display config
#python /space/git/shutit/bin/../shutit_main.py --sc
# Debug
#python /space/git/shutit/bin/../shutit_main.py --debug
# Tutorial
#python /space/git/shutit/bin/../shutit_main.py --tutorial
