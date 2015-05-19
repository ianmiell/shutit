FROM ubuntu:12.04

RUN apt-get update
RUN apt-get install -y -qq curl git python-pip
WORKDIR /opt
RUN git clone https://github.com/ianmiell/shutit.git
WORKDIR shutit
RUN pip install -r requirements.txt

WORKDIR /space/git/shutit/library/mesos <- TODO You will likely need to to change this
RUN /opt/shutit/shutit build --shutit_module_path /opt/shutit/library --delivery dockerfile

CMD ["/bin/bash"] 
