FROM ubuntu:14.04

RUN apt-get update
RUN apt-get install -y -qq curl git python-pip
WORKDIR /opt
RUN git clone -b dockerfile https://github.com/ianmiell/shutit.git
WORKDIR shutit
RUN pip install -r requirements.txt

WORKDIR /opt/shutit/library/win2048
RUN /opt/shutit/shutit build --shutit_module_path /opt/shutit/library --delivery dockerfile

CMD ["/bin/bash","-c","'/root/start_win2048.sh && sleep infinity'"] 
