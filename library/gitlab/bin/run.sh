#!/bin/bash
# Example for running
docker run -t -i -p 22:22 -p 80:80 -p 443:443 -v /home/git/data:/home/git/data -v /var/log/gitlab:/var/log/gitlab gitlab /app/init app:start
