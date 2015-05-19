FROM ubuntu:14.04

RUN apt-get update
RUN apt-get install -y -qq curl git python-pip
WORKDIR /tmp/opt
RUN git clone https://github.com/ianmiell/shutit.git
WORKDIR shutit
RUN pip install -r requirements.txt

WORKDIR /tmp/opt/shutit/library/shutit
RUN /tmp/opt/shutit/shutit build --shutit_module_path /tmp/opt/shutit/library --delivery dockerfile
RUN rm -rf /tmp/opt

CMD ["/bin/bash"] 
