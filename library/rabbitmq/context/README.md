dockerfiles-fedora-rabbitmq
========================

Fedora dockerfile for rabbitmq

Tested on Docker 0.7.0

To shutit.core.module.build:

Copy the sources down -

	# docker build -rm -t <username>/rabbitmq .

To run:

	# docker run -d -p 5672:5672 -p 15672:15672 <username>/rabbitmq

Confirm the RabbitMQ server started:

```
# docker logs 276c0221d0b93a

            RabbitMQ 3.1.5. Copyright (C) 2007-2013 GoPivotal, Inc.
##  ##      Licensed under the MPL.  See http://www.rabbitmq.com/
##  ##
##########  Logs: /var/log/rabbitmq/rabbit@276c0221d0b9.log
######  ##        /var/log/rabbitmq/rabbit@276c0221d0b9-sasl.log
##########
              Starting broker... completed with 6 plugins.
```


Look at the ports associated with the container:

```
# docker ps
CONTAINER ID        IMAGE                      COMMAND                CREATED             STATUS              PORTS                                              NAMES
01ad9b20d68e        scollier/rabbitmq:latest   /usr/sbin/rabbitmq-s   9 minutes ago       Up 9 minutes        0.0.0.0:15672->15672/tcp, 0.0.0.0:5672->5672/tcp   grave_albat
```


To test:

Download the rabbitmqadmin tool from the management interface.

```
# wget localhost:15672/cli/rabbitmqadmin

# chmod +x rabbitmqadmin 

# ./rabbitmqadmin help subcommands

# ./rabbitmqadmin list users
+-------+------------------------------+---------------+
| name  |        password_hash         |     tags      |
+-------+------------------------------+---------------+
| guest | CkDOzIkuFmtJNeg2AL6T1LiUfmQ= | administrator |
+-------+------------------------------+---------------+

```
