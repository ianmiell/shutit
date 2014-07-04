# Example Dockerfile for test purposes

FROM ubuntu:14.04

WORKDIR /

ENV HOME /root

RUN apt-get install -y iputils-ping
RUN ping -c 1 localhost

WORKDIR etc

RUN cat /etc/hosts

COPY test.sh /tmp/test.sh

RUN cat /tmp/test.sh

EXPOSE 8088
EXPOSE 8089 8090

VOLUME /tmp
VOLUME ["/home"]

CMD ["/bin/bash"]
