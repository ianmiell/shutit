---
layout: default
markdown: 1
---
# ShutIt #

Automation framework for programmers.

## Features ##

 - Shell-based (minimal learning curve)
 - Pattern-based extensible framework
 - Available patterns include:
   - bash builds
   - Docker builds
   - Vagrant builds
 - Modular
 - Configurable
 - Use your python skills to make it work the way you want
 - Outputs include a series of shell commands you can port to other CM tools
 - Lifecycle allows for testing and finalization
 - Extensive debugging tools to make reproducible runs easier
 - Utility functions for common tasks (that work across distros)
 - 'Training mode', forces users to type in commands
[Git Trainer](https://asciinema.org/a/32807?t=70)
 - 'Video mode', ideal for demos
[Automating Docker Security Checks](https://asciinema.org/a/32001?t=120)
 - 'Golf mode' - set challenges for users
[grep scales](https://github.com/ianmiell/grep-scales)

Many more examples explained [here](https://zwischenzugs.wordpress.com):


### Step 1: Get ShutIt ###

```sh
pip install shutit
```

Run the above as root, and ensuring python-pip and docker are already installed.


### Step 2: Create a Skeleton bash ShutIt Module ###

As your preferred user:

```sh
shutit skeleton --template_branch bash
```

Follow the instructions



## Troubleshooting Docker Patterns ##

### 'Permission denied' ###

If at this point you get an error to do with 'permission denied', then you may
need to configure ShutIt to call 'sudo docker' instead of docker. Open the
~/.shutit/config file, and change this line

```
docker_executable:docker
```

For example if you run with sudo, and the executable is 'docker.io':

```
docker_executable:sudo docker.io
```


### 'Use sudo docker/docker.io to run docker?' ###

If you use "sudo docker", or "docker.io" or some other command to run docker,
then you might need to alter run.sh accordingly.



### Something else? ###

Didn't work for you? It's probably my fault, not yours. Mail me: ian.miell@gmail.com
