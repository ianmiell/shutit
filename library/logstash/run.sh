# Example for running
docker run -t -i -p 514:514 -p 5043:5043 -p 9200:9200 -p 9292:9292 -p 9300:9300 -e DEBIAN_FRONTEND:noninteractive -e LUMBERJACK_TAG:MYTAG -e ELASTICWORKERS:1 logstash  /usr/local/bin/run.sh
