FROM ubuntu:12.04

RUN apt-get update
RUN apt-get install -y -qq curl git python-pip
WORKDIR /opt
RUN git clone https://github.com/ianmiell/shutit.git
WORKDIR shutit
RUN pip install -r requirements.txt

# Add your build.sh here, so eg:
# COPY configfile ~/.shutit/config
WORKDIR library/win2048
RUN ../../shutit build --shutit_module_path .. --delivery bash

CMD ["/bin/bash"]

