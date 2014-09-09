# Example for running
docker run -t -i -p 8529:8529 -e ARANGO_URL:http://www.arangodb.org/repositories/arangodb2/xUbuntu_14.04 arangodb  [&quot;/usr/sbin/arangod&quot;, &quot;--configuration&quot;, &quot;/etc/arangodb/arangod.conf&quot;]
