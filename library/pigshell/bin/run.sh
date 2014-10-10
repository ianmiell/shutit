#!/bin/bash
# Example for running
sudo docker run -d -p 50937:50937 -v /tmp:/var/psty_dir imiell/psty /bin/bash -c 'python /opt/pigshell/psty.py -a -d /var/psty_dir'
# Then, eg:
mount http://localhost:50937/ /home 
