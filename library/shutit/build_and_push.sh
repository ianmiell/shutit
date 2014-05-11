set -e
python /home/imiell/shutit/bin/../shutit_main.py --config configs/push.cnf
# Display config
#python /home/imiell/shutit/bin/../shutit_main.py --sc
# Debug
touch /home/imiell/shutit/library/shutit/test_build.sh
cat >> /home/imiell/shutit/library/shutit/test_build.sh << END
set -e
python /home/imiell/shutit/bin/../shutit_main.py -s container rm yes
# Display config
#python /home/imiell/shutit/bin/../shutit_main.py --sc
# Debug
#python /home/imiell/shutit/bin/../shutit_main.py --debug
# Tutorial
#python /home/imiell/shutit/bin/../shutit_main.py --tutorial
set -e
python /home/imiell/shutit/bin/../shutit_main.py --config configs/push.cnf
# Display config
#python /home/imiell/shutit/bin/../shutit_main.py --sc
# Debug
#python /home/imiell/shutit/bin/../shutit_main.py --debug
# Tutorial
#python /home/imiell/shutit/bin/../shutit_main.py --tutorial
