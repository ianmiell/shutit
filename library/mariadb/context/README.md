dockerfiles-sct-mariadb
========================

Tested on Docker 0.8.1
Based on scollier's mysql dockerfile.

This repo contains a recipe for making Docker container for mariadb on Fedora. 

Check your Docker version

    # docker version

Perform the build

    # docker build -rm -t <yourname>/mariadb .

Check the image out.

    # docker images

Run it:

    # docker run --name=mariadb -d -p 3306:3306 <yourname>/mariadb

Keep in mind the initial password set for mariadb is: mysqlPassword.  Change it now:

    # mysqladmin -u testdb -pmysqlPassword password myNewPass

For mariadb:
    # mysql -utestdb -pmyNewPass

Create a table:

    \> CREATE TABLE test (name VARCHAR(10), owner VARCHAR(10),
        -> species VARCHAR(10), birth DATE, death DATE);


To use a separate data volume for /var/lib/mysql (recommended, to allow image update without
losing database contents):


Create a data volume container: (it doesn't matter what image you use
here, we'll never run this container again; it's just here to
reference the data volume)

    # docker run --name=mariadb-data -v /var/lib/mysql fedora true

Initialise it using a temporary one-time mariadb container:

    # docker run -rm --volumes-from=mariadb-data <yourname>/mariadb /config_mariadb.sh

And now create the new persistent mariadb container:

    # docker run --name=mariadb -d -p 3306:3306 --volumes-from=mariadb-data <yourname>/mariadb
