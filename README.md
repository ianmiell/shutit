[ShutIt](http://shutit.tk)
==========================


[![Join the chat at https://gitter.im/ianmiell/shutit](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/ianmiell/shutit?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
A versatile automation framework.

ShutIt is an automation tool that models a user's actions on a terminal.

It can automate any process that can be run by a human on the command line with little effort.

It was originally written to manage complex Docker builds, but is a now general-purpose automation tool that supports bash, Docker, Vagrant, ssh and arbitrary build contexts.

If you want to know more about Docker, see the [official site](https://www.docker.com/) or take a look at the book by the creators of ShutIt - [Docker in Practice](http://docker-in-practice.github.io/).

ShutIt is also an educational tool, as it can produce videos of demos, capture reproducible steps required to set environments up, and even challenge you to get the right output (see [grep-scales](https://github.com/ianmiell/grep-scales)).

Really Quick Overview
=====================
Some use cases:

- You like bash, want to automate tasks, have structure and support, but don't want to learn a configuration management framework that takes you away from the command line you know and love.

- Are a programmer who wants highly configurable stateless containers development, testing, and production.

- Want to [build everything from source](https://github.com/ianmiell/shutit-distro/blob/master/README.md) in a way that's comprehensible and auditable.

- Want to create instructive [walkthroughs](https://asciinema.org/a/30598?t=70): 

- Want to take your scripts and turn them into stateless containers quickly, without needing to maintain (or learn) a configuration management solution designed for moving-target systems.

- Are interested in "phoenix deployment".


What Does it Do (bash Builds)?
==============================

ShutIt acts as a modular and easy to use wrapper around [https://github.com/pexpect/pexpect](pexpect).

TODO: example


What Does it Do (Tutorials)?
============================

This builds on the docker features (see below), but allows you to interrupt the run at points of your choosing with 'challenges' for the user to overcome.

Two types of 'challenge' exist in ShutIt:

- scales
- free form

Scales tell you to run a specific command before continuing. This is useful when you want to get certain commands or flags 'under your fingers', which does not happen without dedicated and direct practice.
Scales tell you to run a specific command before continuing. This is useful when you want to get certain commands 'under your fingers'. Here's an example:

[![grep Scales](https://asciinema.org/a/41308.png)](https://asciinema.org/a/41308)

Free form exercises give you a task to perform, and free access to the shell. This is to give the user a realistic environment in which to hone their skills. You can check man pages, look around the directories, search for useful utils (even install new ones!). When you are finished, a pre-specified command is run to check the system is in an appropriate state. Here's an example 

[![git 101 Tutorial](https://asciinema.org/a/44937.png)](https://asciinema.org/a/44937)

TODO: git 101 example

If using Docker and you mess the environment up, the state can be restored to a known one by hitting CTRL-G.


What Does it Do (Docker Builds)?
================================

![Example Setup]
(https://github.com/ianmiell/shutit/blob/gh-pages/images/ShutIt.png)

We start with a "ShutIt Module", similar to a or a shell script, or a Dockerfile (see bash builds above).

In the image above there are five of these. At a high level they each have the following attributes:

- a list of zero or more dependencies on other modules
- a unique number that represents its ordering within the available modules
- a set of steps (bash commands) for building the module

In the image we imagine a scenario where we want to build our blog into a docker image, with all its attendant content and config.

We instruct ShutIt to build the MyBlog module, and it runs the build as per the image on the right.

The container environment is set up, the modules are ordered, and the build steps are run. Finally, the image is committed, tagged and pushed as configured.

This is a core function of ShutIt - to manage dependencies and image building for complex image setups.

But it doesn't just run build steps, it also manages The ShutIt Lifecycle to make the build more robust and flexible.


What Does it Do (Vagrant)?
==========================
Uses a bash build to set up a vagrant machine. This allows another kind of contained environment for more infrastructural projects than Docker allows for.

There is a multinode option for Vagrant multinode projects.


The ShutIt Lifecycle
====================

- gathers all the modules it can find in its path and determines their ordering
- for all modules, it gathers any build-specific config (e.g. passwords etc.)
- it checks dependencies and conflicts across all modules and figures out which modules need to be built
- for all modules, it checks whether the module is already installed
- for all modules, if it needs building, it runs the build
- for all modules, run a test cycle to ensure everything is as we expect
- for all modules, run a finalize function to clean up the container
- do any configured committing, tagging and pushing of the image

These correspond to the various functions that can be implemented.


Auto-Generate Modules
=====================

ShutIt provides a means for auto-generation of modules (either bare ones, or from existing Dockerfiles) with its skeleton command. See [here](http://ianmiell.github.io/shutit/) for an example.


[Really Quick Start](http://ianmiell.github.io/shutit)
====================

[Full User Guide](http://github.com/ianmiell/shutit/blob/master/docs/USER_GUIDE.md)
==============

[API](http://github.com/ianmiell/shutit/blob/master/docs/API.md)
======

[Installation](http://github.com/ianmiell/shutit/blob/master/docs/INSTALL.md)
==============

Contributing
============

We always need help, and with a potentially infinite number of libraries required, it's likely you will be able to contribute. Just mail ian.miell@gmail.com if you want to be assigned a mentor. [He won't bite](https://www.youtube.com/watch?v=zVUPmmUU3yY) 

[Tests](http://github.com/ianmiell/shutit/blob/master/docs/TEST.md)

Mailing List
------------
https://groups.google.com/forum/#!forum/shutit-users
shutit-users@groups.google.com

Known Issues
=============
Since a core technology used in this application is pexpect - and a typical usage pattern is to expect the prompt to return. Unusual shell prompts and escape sequences have been known to cause problems. Use the shutit.setup_prompt() function to help manage this by setting up a more sane prompt. Use of COMMAND_PROMPT with echo -ne has been seen to cause problems with overwriting of shells and pexpect patterns.


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

