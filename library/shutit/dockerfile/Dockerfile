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
RUN ../../shutit build -m .. --interactive 0 -s build conn_module shutit.tk.conn_bash

CMD ["/bin/bash"]

