FROM ubuntu:14.04

RUN apt-get update
RUN apt-get install -y -qq git python-pip
RUN pip install shutit

WORKDIR /opt
# Change the next two lines to build your ShutIt module.
RUN git clone https://github.com/yourname/yourshutitproject.git
WORKDIR /opt/yourshutitproject
RUN /opt/shutit/shutit build --shutit_module_path /opt/shutit/library --delivery dockerfile

CMD ["/bin/bash"] 
