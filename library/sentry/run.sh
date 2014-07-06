# Example for running
docker run -t -i -p 9000:9000 -e LANGUAGE:en_US.UTF-8 -e LANG:en_US.UTF-8 -e LC_ALL:en_US.UTF-8 sentry /usr/local/bin/sentry --config=/sentry.conf.py upgrade
