[ShutIt](http://shutit.tk)
==========================

[![Join the chat at https://gitter.im/ianmiell/shutit](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/ianmiell/shutit?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
Complex Docker Builds Made Simple.

ShutIt is a tool for managing your image building process that is both structured and flexible.

If you want to know more about Docker, see the
[official site](https://www.docker.com/) or take a look at the book by the
creators of ShutIt - [Docker in Practice](http://docker-in-practice.github.io/).

Really Quick Overview
=====================
You'll be interested in this if you:

- Are a programmer who wants highly configurable containers for differing use cases and environments.

- Find dockerfiles a great idea, but limiting in practice.

- Want to build stateless containers for development, testing, and production.

- Want to [build everything from source](https://github.com/ianmiell/shutit-distro/blob/master/README.md) in a way that's comprehensible and auditable.

- Want to take your scripts and turn them into stateless containers quickly, without needing to maintain (or learn) a configuration management solution designed for moving target systems.

- Are interested in "phoenix deployment" using Docker.


What Does it Do?
================

![Example Setup]
(https://github.com/ianmiell/shutit/blob/gh-pages/images/ShutIt.png)

We start with a "ShutIt Module", similar to a Dockerfile.

In the image above there are five of these. At a high level they each have the following attributes:

- a list of zero or more dependencies on other modules
- a unique number that represents its ordering within the available modules
- a set of steps (bash commands) for building the module

In the image we imagine a scenario where we want to build our blog into a docker image, with all its attendant content and config.

We instruct ShutIt to build the MyBlog module, and it runs the build as per the image on the right.

The container environment is set up, the modules are ordered, and the build steps are run. Finally, the image is committed, tagged and pushed as configured.

This is a core function of ShutIt - to manage dependencies and image building for complex image setups.

But it doesn't just run build steps, it also manages The ShutIt Lifecycle to make the build more robust and flexible.

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

Background
==========
While evaluating Docker for my $corp we reached a point where
using Dockerfiles was somewhat painful or verbose for complex and/or long and/or
configurable interactions. So we wrote our own.

ShutIt works in the following way:

- It runs a docker container (base image configurable)
- Within this container it runs through configurable set of modules (each with
  a globally unique module id) that runs in a defined order with a standard
  lifecycle:
     - dependency checking
     - conflict checking
     - remove configured modules
     - build configured modules
     - tag (and optionally push) configured modules (to return to that point
       of the build if desired)
     - test
     - finalize module ready for closure (ie not going to start/stop anything)
     - tag (and optionally push) finished container
- These modules must implement an abstract base class that forces the user to
  follow a lifecycle (like many test frameworks)
- It's written in python
- It's got a bunch of utility functions already written, eg:
     - pause_point (stop during build and give shell until you decide to 
       return to the script (v useful for debugging))
     - add_line_to_file (if line is not already there)
     - add_to_bashrc (to add something to everyone's login)
     - setup_prompt (to handle shell prompt oddities in a 
       reliable/predictable way)
     - is user_id_available
     - set_password (package-management aware)
     - file_exists
     - get_file_perms
     - package_installed (determine whether package is already installed)
     - loads more to come

If you have an existing bash script it is relatively trivial to port to this 
to get going with docker and start shipping containers. 
You can also use this to prototype builds before porting to whatever
configuration management tool you ultimately choose.

As a by-product of this design, you can use it in a similar way to chef/puppet
(by taking an existing container and configuring it to remove and build a
specific module), but it's not designed primarily for this purpose.

Chef/Puppet were suggested as alternatives, but for several reasons I didn't go
with them:

- I had to deliver something useful, and fast (spare time evaluation), so 
  taking time out to learn chef was not an option
- It struck me that what I was trying to do was the opposite of what chef is
  trying to do, ie I'm building static containers for a homogeneous environment
  rather than defining state for a heterogeneous machine estate and hoping
  it'll all work out
- I was very familiar with (p)expect, which was a good fit for this job and
  relatively easy to debug
- Anecdotally I'd heard that chef debugging was painful ("It works 100% of the
  time 60% of the time")
- I figured we could move quite easily to whatever CM tool was considered
  appropriate once we had a deterministic set of steps that also documented
  server requirements

If you are a sysadmin looking for something to manage dynamic, moving target
systems stick with chef/puppet. If you're a programmer who wants to manage a
bunch of existing scripts in a painless way, keep on reading.



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

