#!/bin/bash
# Example for running
docker run -t -i -p 6379:6379 -v [&quot;/data&quot;]:[&quot;/data&quot;] redis  [&quot;redis-server&quot;, &quot;/etc/redis/redis.conf&quot;]
