# Example for running
docker run -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix -u $(whoami) --rm imiell/hostx /bin/bash -c 'firefox'
