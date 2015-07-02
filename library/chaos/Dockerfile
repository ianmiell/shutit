FROM ubuntu:14.04

RUN apt-get update
RUN apt-get install -y -qq python-pip
RUN pip install shutit

WORKDIR /opt/shutit/library/chaos
RUN /opt/shutit/shutit build --shutit_module_path /opt/shutit/library --delivery dockerfile

CMD ["/root/work.sh"] 
