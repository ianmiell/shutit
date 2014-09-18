FROM ubuntu:12.04

RUN apt-get update
RUN apt-get install -y -qq lsb-release
RUN echo deb http://archive.ubuntu.com/ubuntu $(lsb_release -s -c) universe > /etc/apt/sources.list.d/universe.list
RUN apt-get update
RUN apt-get install -y -qq passwd passwd apt-utils iptables ca-certificates lxc curl aufs-tools git python-pip
WORKDIR /usr/bin
RUN curl https://get.docker.io/builds/Linux/x86_64/docker-latest > docker
RUN chmod +x docker
WORKDIR /opt
RUN git clone https://github.com/ianmiell/shutit.git
WORKDIR shutit
RUN pip install -r requirements.txt
RUN ln -s /usr/bin/docker /usr/bin/docker.io
COPY wrapdocker /usr/bin/wrapdocker

# Add your build.sh here, so eg:
# COPY configfile ~/.shutit/config
WORKDIR library/win2048
RUN ../../shutit build -m .. --interactive 0

CMD ["/bin/bash"]
