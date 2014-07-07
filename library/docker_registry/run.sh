# Example for running
docker run -t -i -p 5000:5000 -v /registry:/registry -e dev_version:1 docker_registry  ./setup-configs.sh && ./run.sh
