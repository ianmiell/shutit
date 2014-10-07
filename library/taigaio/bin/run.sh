#!/bin/bash
# Example for running
docker run -i -t -p 127.0.0.1:8000:8000 -p 127.0.0.1:8001:8001 taigaio bash -c '/root/start_postgres.sh && /root/start_taiga.sh && echo READY! && sleep infinity'
