#!/bin/bash
IMAGE_ID=$(docker build -q . 2> /dev/null | grep Successfully | awk '{print $NF}')
docker tag $IMAGE_ID imiell/shutit_dist_base

