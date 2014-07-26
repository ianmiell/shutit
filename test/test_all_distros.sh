#!/bin/bash
pushd ..
for D in ubuntu:12.04 ubuntu:14.04 debian:7.5 debian:7.4 debian:7.3
do
	SHUTITEST_DISTROS=$D ./test.sh > /tmp/shutittest_$(date +%s)_${D}.log
done
popd
