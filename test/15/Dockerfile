FROM ubuntu:14.04

RUN apt-get update
RUN apt-get install -y -qq curl git python-pip
WORKDIR /opt
RUN git clone https://github.com/ianmiell/shutit.git
WORKDIR shutit
RUN pip install -r requirements.txt

WORKDIR /opt
# Change the next two lines to build your ShutIt module.
RUN git clone https://github.com/yourname/yourshutitproject.git
WORKDIR /opt/yourshutitproject
RUN /opt/shutit/shutit --delivery dockerfile

CMD ["/bin/bash"] 
