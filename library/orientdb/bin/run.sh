# Example for running
docker run -t -i -p 2424:2424 -p 2480:2480 -e ROOT:/opt/downloads -e ORIENT_URL:http://www.orientdb.org/portal/function/portal/download/unknown@unknown.com -e ORIENT_VERSION:orientdb-community-1.7.4 orientdb  [&quot;/usr/local/bin/server.sh&quot;]
