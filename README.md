[ShutIt](http://shutit.tk)
==========================
Complex Docker Builds Made Simple

ShutIt is a tool for managing your build process that is both structured and flexible:

Structured:

- Modular structure
- Manages the startup and setup of your container ready for the build
- Has a lifecycle that can manage different parts of the lifecycle, eg:
	- Pre-requisites check
	- "Already installed?" check
	- Gather config
	- Start module
	- Stop module
	- Test module
	- Finalize container
- Allows you to set config
- Allows you to manage modules per distro (if needed)
- Forces you to define an order for the modules
- Puts record of build process into container
- Enables continuous regression testing

Flexible:

- Modules model shell interactions, with all the freedom and control that implies
- Modules can be plugged together like legos
- GUI allows to you build and download images for your own needs (see http://shutit.tk)
- Module scripts are in python, allowing full language control
- Many helper functions for common interaction patterns
- Can pause during build or on error to interact, then continue with build



WHAT DOES IT DO?
----------------

![Example Setup]
(https://github.com/ianmiell/shutit/blob/gh-pages/images/ShutIt.png)

We start with a "Unit of Build", similar to a Dockerfile.

In the image above there are five of these. They each have the following attributes:

- a list of zero or more dependencies on other modules
- a unique number that represents its ordering within the available modules
- a set of steps (bash commands) for building the module

In the image we imagine a scenario where we want to build our blog into a docker image, with all its attendant content and config.

We instruct shutit to build the MyBlog module, and it runs the build as per the image on the right.

The container environment is set up, the modules are ordered, and the build steps are run. Finally, the image is committed, tagged and pushed as configured.

This is a core function of ShutIt - to manage dependencies and image building for complex image setups.

But it doesn't just run build steps, it also manages The ShutIt Lifecycle to make the build more robust and flexible.

The ShutIt Lifecycle
--------------------

- gathers all the modules it can find in its path and determines their ordering
- for all modules, it gathers any build-specific config (e.g. passwords etc.)
- it checks dependencies and conflicts across all modules and figures out which modules need to be built
- for all modules, it checks whether the module is already installed
- for all modules, if it needs building, it runs the build
- for all modules, run a test cycle to ensure everything is as we expect
- for all modules, run a finalize function to clean up the container
- do any configured committing, tagging and pushing of the image

These correspond to the various functions that can be implemented.

Auto-Generate MOdules
---------------------

ShutIt provides a means for auto-generation of modules (either bare ones, or from existing Dockerfiles) with its skeleton command. See [here](http://ianmiell.github.io/shutit/) for an example.


[REALLY QUICK START](http://ianmiell.github.io/shutit)
====================

[INSTALLATION](http://github.com/ianmiell/shutit/blob/master/docs/INSTALL.md)
==============

[ShutIt API](http://github.com/ianmiell/shutit/blob/master/docs/API.md)
============


REALLY QUICK OVERVIEW
---------------------
You'll be interested in this if you:

- Want to take your scripts and turn them into stateless containers quickly,
without needing to learn or maintain a configuration management solution.

- Are a programmer who wants highly configurable containers for
differing use cases and environments.

- Find dockerfiles a great idea, but limiting in practice.

- Want to build stateless containers for production.

- Are interested in "phoenix deployment" using Docker.

I WANT TO SEE EXAMPLES
----------------------
See in ```library/*```
eg
```
cd library/mysql/bin
./build.sh
./run.sh
```

Overview
--------
While evaluating Docker for my I reached a point where
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


[ShutIt User Guide](http://github.com/ianmiell/shutit/blob/master/docs/USER_GUIDE.md)

[Tests](http://github.com/ianmiell/shutit/blob/master/docs/TEST.md)

[Known Issues](http://github.com/ianmiell/shutit/blob/master/docs/BUGS.md)

CAN I CONTRIBUTE?
-----------------

We always need help, and with a potentially infinite number of libraries required, it's likely you will be able to contribute. Just mail ian.miell@gmail.com if you want to be assigned a mentor. [He won't bite](https://www.youtube.com/watch?v=zVUPmmUU3yY) 

Mailing List
------------
https://groups.google.com/forum/#!forum/shutit-users
shutit-users@groups.google.com


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

