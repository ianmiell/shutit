#!/bin/bash
pushd ..
for D in ubuntu:13.10 ubuntu:14.04 ubuntu:13.04 debian:6.0.9 debian:7.5 debian:7.4 debian:6.0.8 debian:7.3
do
	SHUTITEST_DISTROS=$D ./test.sh > /tmp/shutittest_$(date +%s)_${D}.log
done
popd
