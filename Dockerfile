FROM alpine

# ShutIt in a container.

RUN apk add --update py-pip
RUN pip install shutit
