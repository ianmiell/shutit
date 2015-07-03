FROM ubuntu:14.04

RUN apt-get update
RUN apt-get install -y -qq python-pip git
RUN pip install shutit

WORKDIR /opt
RUN git clone https://github.com/ianmiell/shutit.git
WORKDIR /opt/shutit/library/chaos
RUN shutit build --shutit_module_path /opt/shutit/library --delivery dockerfile

CMD ["/root/work.sh"] 
