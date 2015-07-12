FROM ubuntu:14.04

RUN apt-get update
RUN apt-get install -y -qq curl git python-pip
WORKDIR /opt
RUN git clone https://github.com/ianmiell/shutit.git
WORKDIR shutit
RUN pip install -r requirements.txt

WORKDIR /space/git/shutit/test/8 <- TODO You will likely need to to change this
RUN /opt/shutit/shutit build --delivery dockerfile

CMD ["/bin/bash"] 
