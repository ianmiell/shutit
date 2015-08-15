---
layout: default
markdown: 1
---
# ShutIt #

Configuration management for programmers.

## Why? ##

Interested in Docker? Find Dockerfiles limiting? Want to automate a shell script
with all the power of a real programming language?

Are you a programmer annoyed by the obfuscation and indirection
Chef/Puppet/Ansible brings to a simple series of commands?

Interested in stable stateless deployments?

## Features ##

 - Easy to use
 - Deterministic builds
 - Outputs include a series of shell commands you can port to other CM tools
 - Automate your pushing and deployment in one place
 - Shell-based (minimal learning curve)
 - Implement your own tests of modules that are automatically run
 - Use your python skills to make it work the way you want
 - Extensive debugging tools to make reproducible builds easier
 - Util functions for common tasks (that work across distros)

### Step 1: Get ShutIt ###

```sh
pip install shutit
```

Run the above as root, and ensuring python-pip and docker are already installed.


### Step 2: Create a Skeleton ShutIt Module ###

As your preferred user:

```sh
shutit skeleton
```

and accept the defaults until you get to the 'delivery method' section,
where you input 'docker' to build within a Docker container:

```sh
# Input a delivery method from: ('docker', 'dockerfile', 'target', 'ssh', 'bash').
# Default: bash

docker
```

Follow the instructions to go to your new skeleton module and do your first
build. Wait for it to complete.


### Step 3: Modify the Skeleton Module ###

Now you can change your module to do what you want it to.

To install mlocate and create a file if only if it doesn't exist, change the
.py file in your skeleton directory:

```python
[...]
        def build(self, shutit):
                # Install mlocate
                shutit.install('mlocate')
				# Issue a simple command
				if not shutit.file_exists('/tmp/newfile'):
                	shutit.send('touch /tmp/newfile')
                return True
[...]
```

You can find a cheat sheet for ShutIt in the module's .py file to help you
create the build you want.

### Step 4: Build Your Module ###

**Build module:**

```sh
$ ./build.sh
Running: docker --version


Command being run is:

docker run -v=/root/shutit/artifacts:/artifacts -t -i ubuntu /bin/bash
[...]
```

Problems? See Troubleshooting section below.



### Step 5: Run Your Module ###

```sh
$ ./run.sh
root@138ed0fd3728:/#
```

You are now in your bespoke container!

Problems? See Troubleshooting section below.


### Step 6: Mix and Match ###

Let's add mysql to the container build. Change this in your skeleton module's
.py file:

```python
depends=['shutit.tk.setup']
```

to:

```python
depends=['shutit.tk.setup','shutit.tk.mysql.mysql']
```

Rebuild and re-run to get the same container with mysql installed.


```sh
cd $HOME
git clone https://github.com/ianmiell/shutit.git
cd -
./build.sh --shutit_module_path $HOME/shutit/library
./run.sh
```

Problems? See Troubleshooting section below.



## Troubleshooting ##

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

Didn't work for you? It's probably my fault, not yours. Mail me:
ian.miell@gmail.com
