# Example for running
docker run -t -i -p 80:80 -p 443:443 -e HAPROXY_VERSION:1.5-dev22 -e HAPROXY:haproxy-$HAPROXY_VERSION -e TMP_DIR:/tmp -e SSL_SUBJ:/C=CA/ST=QC/L=Saguenay/O=Dis/CN=alanb.ca haproxy  /usr/local/sbin/haproxy -f /etc/haproxy/haproxy.conf
