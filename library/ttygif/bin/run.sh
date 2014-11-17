#!/bin/bash
# Example for running
docker run -t -i -p 5901:5901 -p 6080:6080 ttygif /bin/bash -c '/root/start_vnc.sh && sleep infinity'
