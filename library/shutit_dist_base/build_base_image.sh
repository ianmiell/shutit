#!/bin/bash
pushd dockerfile
#docker build --no-cache -t imiell/shutit_dist_base .
docker build -t imiell/shutit_dist_base .
CONTAINER=$(docker run -d imiell/shutit_dist_base /bin/true)
REDUCED_IMAGE=$(docker export $CONTAINER | docker import -)
docker tag $REDUCED_IMAGE imiell/shutit_dist_base
docker push imiell/shutit_dist_base
popd
