#!/bin/bash

pushd ..
../../shutit build --image_tag debian:6.0.9 -m ../2 "$@"
