# Example for running
docker run -t -i -p 80:80 -e APACHE_RUN_USER:www-data -e APACHE_RUN_GROUP:www-data -e APACHE_LOG_DIR:/var/log/apache2 incecoder  /usr/sbin/apache2 -D FOREGROUND
