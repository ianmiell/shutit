---
layout: default
markdown: 1
---
# ShutIt

Automation framework for programmers.

## Learn it in X minutes ##

[Quick start guide here](https://learnxinyminutes.com/docs/shutit/)

## Examples

[Examples are here](https://github.com/ianmiell/shutit-scripts), including:

- [Gnuplot automation](https://github.com/ianmiell/shutit-scripts/tree/master/gnuplot)
- [Automation of login with a .json configuration](https://github.com/ianmiell/shutit-scripts/tree/master/logmein)
- [Set up a pre-built Vagrant machine](https://github.com/ianmiell/shutit-scripts/tree/master/vagrant-box-create)

## Features

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
 - Utility functions for common tasks (that work across distros)


### Step 1: Get ShutIt

```sh
[sudo] pip install shutit
```

Run the above as root, and ensuring python-pip and docker are already installed.


### Step 2: Create a Skeleton hutIt Module

As your preferred user:

```sh
shutit skeleton
```

Hit return through and follow the instructions.

Choose which template you want to use:

- bash

- Vagrant

- Docker

- Shutitfile

and you'll be guided through the process.

### Anything else?

Didn't work for you? It's probably my fault, not yours. Mail me: ian.miell@gmail.com
