---
layout: default
markdown: 1
---
# ShutIt #

Automation framework for programmers.

## Features ##

 - Shell-based (minimal learning curve)
 - [Pattern-based](https://github.com/ianmiell/shutit-templates) extensible framework
 - Available patterns include:
   - bash builds
   - Docker builds
   - Vagrant builds
   - Vagrant multinode builds
 - Modular
   - [Build an OS from scratch step by step](https://zwischenzugs.wordpress.com/2015/01/12/make-your-own-bespoke-docker-image/)
 - 'Training mode', forces users to type in commands
   - [Git Trainer](https://asciinema.org/a/32807?t=70)
   - [Understanding Docker Namespaces](https://zwischenzugs.wordpress.com/2015/11/21/understanding-docker-network-namespaces/)
 - 'Video mode', ideal for demos
   - [Automating Docker Security Checks](https://asciinema.org/a/32001?t=120)
 - 'Challenge mode' - set command challenges for users
   - [grep scales](https://github.com/ianmiell/grep-scales)
 - 'Golf mode' - set task challenges for users
   - [Git rebase challenge](ianmiell.github.io/git-rebase-tutorial)
 - ShutIt [Lifecycle](https://github.com/ianmiell/shutit/blob/master/README.md) allows for configuration, testing, modularity, and finalization
 - Use your python skills to make it work the way you want
 - Outputs include a series of shell commands you can port to other CM tools
 - Utility functions for common tasks (that work across distros)

Many more examples explained [here](https://zwischenzugs.wordpress.com):


### Step 1: Get ShutIt ###

```sh
[sudo] pip install shutit
```

Run the above as root, and ensuring python-pip and docker are already installed.


### Step 2: Create a Skeleton bash ShutIt Module ###

As your preferred user:

```sh
shutit skeleton
```

Hit return through and follow the instructions.

### Step 3: Automate

Go to the newly-created directory, and open up the .py file.

In there is a function called 'build' with a cheat sheet of functions.

For this example we are going to add commands to ensure that we have a the documentation branch of ShutIt checked out.

```
# Ensure git is installed. This handles different distros gracefully.
shutit.install('git')

# If the directory does not exist, we create it
if not shutit.file_exists('/opt/shutit',directory=True):
	shutit.send('mkdir /opt/shutit')

# Move to the directory
shutit.send('cd /opt/shutit')

# If this is not ShutIt, quit with a message.
if shutit.file_exists('.git',directory=True):
	if shutit.send_and_get_output('git remote -v | grep origin | grep push | grep ianmiell.shutit | wc -l') != '1':
		shutit.fail('Git repo detected that is not ShutIt - terminating')
else:
	# If this is not a git repo, and there are any files in here, we have a problem
	if shutit.send_and_get_output('ls') != '':
		shutit.fail('Not a git repo, and there are other files already in here - terminating')

# Get the branch information
branch = shutit.send_and_get_output("git status -s -b | grep '##' | awk '{print $2}' | awk -F. '{print $1}'")

# If the branch is not correct, check out the correct branch
if branch != 'gh-pages':
	shutit.send('git checkout gh-pages')
```

# Step 4: Use a template

You can use bash to do all sorts of things. ShutIt was original written to manage complex Docker builds, so 
you could write that in bash using the above template. However, there exist other templates for other purposes
such as:

- Docker containers
- Vagrant machines
- Vagrant multinode setup

To use these, follow the shutit skeleton steps above and pick the options you want.

Videos are available going through these steps (links above).

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
