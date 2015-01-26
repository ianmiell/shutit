# Installing ShutIt

## Installing using Docker

You will need a docker daemon running for this:

```sh
user$ docker run -t -i -v /var/run/docker.sock:/var/run/docker.sock imiell/shutit /bin/bash
root$
```

Then you can try building something in library, eg rabbitmq:

```sh
root$ cd /opt/shutit/library/rabbitmq
root$ shutit build -m ..
```


## Installing on your host machine:

apt-get:

```sh
apt-get install git python-pip
git clone https://github.com/ianmiell/shutit.git
cd shutit
pip install -r requirements.txt
```

yum

```sh
yum install git python-pip
git clone https://github.com/ianmiell/shutit.git
cd shutit
pip install -r requirements.txt
```

## Configuration

To configure for your purposes, see: [CONFIGURATION]('https://github.com/ianmiell/shutit/blob/master/CONFIGURATION.md')
