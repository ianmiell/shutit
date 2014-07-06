#!/bin/bash

apt-get update
apt-get install -y python-software-properties python less
add-apt-repository ppa:rethinkdb/ppa
echo "deb http://us.archive.ubuntu.com/ubuntu/ precise universe" >> /etc/apt/sources.list
apt-get update 
apt-get install -y rethinkdb
mkdir /var/rethinkdb
rethinkdb create -d /var/rethinkdb/db
apt-get clean
rm -rf /var/lib/apt/lists/*