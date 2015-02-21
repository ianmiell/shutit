---
layout: default
markdown: 1
---
# ShutIt #

Configuration management for the future.

## Why? ##

Interested in Docker? Find Dockerfiles limiting?

Are you a programmer annoyed by the obfuscation and indirection Chef/Puppet/Ansible brings to a simple series of commands?

Interested in stable stateless deployments?

Join us!

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

### Step 1: Get the source ###
```sh
#install git
#install python-pip
#install docker
git clone https://github.com/ianmiell/shutit.git
cd shutit
pip install --user -r requirements.txt
# Add shutit to your path - YOU WILL NEED TO CHANGE THIS!
echo "export PATH=/PATH/TO/shutit:${PATH}" >> ~/.bashrc
# Source the env
. ~/.bashrc
```

### Step 2: Create a new module ###

```sh
./shutit skeleton $HOME/shutit_modules/my_module my_module my.domain.com --depends shutit.tk --base_image ubuntu
cd $HOME/shutit_modules/my_module
```

Folder structure:

 - **/bin**        - helpful template scripts
 - **/configs**    - config for your module *(see example below)*
 - **/context**    - files you may want to insert into your container or use as part of the build
 - **/dockerfile** - ready-made dockerfile to build the app from a dockerfile if desired

An example folder structure:

```
./my_module
├── bin
│   ├── build_and_push.sh
│   ├── build.sh
│   ├── run.sh
│   └── test.sh
├── configs
│   └── build.cnf
├── context
├── dockerfile
│   └── Dockerfile
├── my_module.py
└── README.md
```

### Step 3: Modify the example module ###

The example module contains examples of many common tasks when installing, e.g.

 - install               - installs packages based on distro ('passwd' install in skeleton --example above)
 - password handling     - automate the inputting of passwords (changing 'password' in skeleton --example above)
 - config to set up apps - allows you to specify build parameters
 - add line to file      - incrementally construct files
 - send file             - or send them in one shot
 - pause_point           - allow you to stop during a build and inspect before continuing
 - handle logins/logouts - to make for safer automated interactions with eg unexpected prompts

It also gives a simple example of each part of the build lifecycle. **Add a package to install to my_module.py**

```python
[...]
        def build(self, shutit):
                # Make sure passwd is installed
                shutit.install('passwd')
                # Install mlocate
                shutit.install('mlocate')
				# Issue a simple command
                shutit.send('touch /tmp/newfile')
                # Install added by you if desired
                #shutit.install('your chosen package here')
                return True
[...]
```

### Step 4: Build your module ###

**Build module:**

```sh
$ cd $HOME/shutit_modules/my_module/bin
$ ./build.sh
Do you want to accept the config option defaults? (boolean - input "yes" or "no") (default: yes): 
[hit return to accept defaults]
Running: docker --version


Command being run is:

docker run --cidfile=/tmp/shutit/cidfilesroot_cidfile_btsync2_root_1423730928.72.724633 --privileged=true -v=/root/shutit/artifacts:/artifacts -t -i ubuntu /bin/bash
[...]
```

### Step 5: Run your module ###

```sh
$ ./run.sh
root@138ed0fd3728:/#
```

NOTE: If you use "sudo docker", or "docker.io" or some other command to run docker, then you will need to alter run.sh accordingly.

You are now in your bespoke container!

### Step 6: Mix and match ###

Let's add mysql to the container build. Change this in your **my_module.py:**

```python
depends=['shutit.tk.setup']
```

to:

```python
depends=['shutit.tk.setup','shutit.tk.mysql.mysql']
```

Rebuild and re-run to get the same container with mysql installed.


```sh
$ ./build.sh
$ ./run.sh
```

NOTE: If you use "sudo docker", or "docker.io" or some other command to run docker, then you will need to alter run.sh accordingly.

Didn't work for you? It's probably my fault, not yours. Mail me: ian.miell@gmail.com
