# Example for running
docker run -t -i -p 8888:8888 -e LANGUAGE:en_US.UTF-8 -e LANG:en_US.UTF-8 -e LC_ALL:en_US.UTF-8 ipython  ipython notebook --pylab=inline --ip=* --MappingKernelManager.time_to_dead=10 --MappingKernelManager.first_beat=3
