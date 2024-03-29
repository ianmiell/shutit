[ShutIt](http://shutit.tk)
==========================


[![Join the chat at https://gitter.im/ianmiell/shutit](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/ianmiell/shutit?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

A versatile automation framework.

ShutIt is an automation tool that models a user's actions on a terminal.

It can automate any process that can be run by a human on the command line with little effort.

It was originally written to manage complex Docker builds, but is a now general-purpose automation tool that supports bash, Docker, Vagrant, ssh and arbitrary build contexts.

ShutIt can also be used as an educational tool, as it can produce videos of demos, capture reproducible steps required to set environments up, and even challenge you to get the right output (see [grep-scales](https://github.com/ianmiell/grep-scales)).

If you want to know more about Docker, see the [official site](https://www.docker.com/) or take a look at the book by the creators of ShutIt - [Docker in Practice](http://docker-in-practice.github.io/).

Really Quick Overview
=====================
Some use cases:

- You like bash, want to automate tasks, have structure and support, but don't want to learn a configuration management framework that takes you away from the command line you know and love.

- Want to create [complex Vagrant environments](https://medium.com/@zwischenzugs/a-complete-openshift-cluster-on-vagrant-step-by-step-7465e9816d98) to model clusters of machines.

- Want to create instructive [walkthroughs](https://asciinema.org/a/30598?t=70): 

- Are interested in "phoenix deployment".

- Want to take your scripts and turn them into stateless containers quickly, without needing to maintain (or learn) a configuration management solution designed for moving-target systems.

- You're programmer who wants highly configurable stateless containers development, testing, and production.

- Want to [build everything from source](https://github.com/ianmiell/shutit-distro/blob/master/README.md) in a way that's comprehensible and auditable.


What Does it Do (bash Builds)?
==============================

ShutIt acts as a modular and easy to use wrapper around [pexpect](https://github.com/pexpect/pexpect).

Here is a simple example of a script that creates a file and a directory if they are not there already:

[![Simple Example](https://asciinema.org/a/47076.png)](https://asciinema.org/a/47076)

What Does it Do (Tutorials)?
============================

This builds on the docker features (see below), but allows you to interrupt the run at points of your choosing with 'challenges' for the user to overcome.

Two types of 'challenge' exist in ShutIt:

- scales
- free form

Scales tell you to run a specific command before continuing. This is useful when you want to get certain commands or flags 'under your fingers', which does not happen without dedicated and direct practice.

[![grep Scales](https://asciinema.org/a/41308.png)](https://asciinema.org/a/41308)

Free form exercises give you a task to perform, and free access to the shell. This is to give the user a realistic environment in which to hone their skills. You can check man pages, look around the directories, search for useful utils (even install new ones!). When you are finished, a pre-specified command is run to check the system is in an appropriate state. Here's an example for the [basics of git](github.com/ianmiell/git-101-tutorial/blob/master/git_101_tutorial.py):

[![git 101 Tutorial](https://asciinema.org/a/44937.png)](https://asciinema.org/a/44937)

If you use a Docker-based tutorial and you mess the environment up, the state can be restored to a known one by hitting CTRL-G.


What Does it Do (Vagrant)?
==========================
Uses a bash build to set up n vagrant machines, and uses Landrush to give them useful hostnames accessible from the hosts and in the guest VMs.

It supports both Virtualbox and Libvirt providers.

This allows another kind of contained environment for more infrastructural projects than Docker allows for.

This example demonstrates a reproducible build that sets up Docker on an Ubuntu VM (on a Linux host), then runs a CentOS image within Docker within the Ubuntu VM.

It deposits the user into a shell mid-build to interrogate the environment, after which the user re-runs the build to add a directive to ensure ps is installed in the image.

[![Docker on Ubuntu VM running a CentOS image](https://asciinema.org/a/47078.png)](https://asciinema.org/a/47078)



Auto-Generate Modules
=====================

ShutIt provides a means for auto-generation of modules (either bare ones, or from existing Dockerfiles) with its skeleton command. See [here](http://ianmiell.github.io/shutit/) for an example.

[Really Quick Start](http://ianmiell.github.io/shutit)
====================

[Full User Guide](http://github.com/ianmiell/shutit-docs/blob/master/USER_GUIDE.md)
==============

[API](http://github.com/ianmiell/shutit-docs/blob/master/API.md)
======

[Installation](http://github.com/ianmiell/shutit-docs/blob/master/INSTALL.md)
==============

Known Issues
=============
Since a core technology used in this application is pexpect - and a typical usage pattern is to expect the prompt to return.
Unusual shell prompts and escape sequences have been known to cause problems. Use the shutit.setup_prompt() function to help manage this by setting up a more sane prompt.
Use of COMMAND_PROMPT with echo -ne has been seen to cause problems with overwriting of shells and pexpect patterns.

[![ScreenShot](https://raw.github.com/GabLeRoux/WebMole/master/ressources/WebMole_Youtube_Video.png)](https://www.youtube.com/watch?v=gsEtaX207a4)

Licence
------------
The MIT License (MIT)

Copyright (C) 2014 OpenBet Limited

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in 
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies 
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL 
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

