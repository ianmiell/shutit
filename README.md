

[ShutIt](http://shutit.tk)
===============
Complex Docker Deployments Made Simple

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
- Modules can be plugged together like lego
- GUI allows to you build and download images for your own needs
- Module scripts are in python, allowing full language control
- Many helper functions for common interaction patterns
- Can pause during build or on error to interact, then continue with build


REALLY QUICK START
------------------

Dependencies
--------------
- python 2.7+
- See [here](https://gist.github.com/ianmiell/947ff3fabc44ace617c6) for a minimal build.

apt-get install git python-bottle docker.io python-pexpect python-cherrypy3
git clone https://github.com/ianmiell/shutit.git && cd shutit
./shutit serve -m library


Videos:
-------

- [Talk on ShutIt](https://www.youtube.com/watch?v=zVUPmmUU3yY) 

- [Setting up a ShutIt server in 3 minutes](https://www.youtube.com/watch?v=ForTMTUMp3s)

- [Steps for above](https://gist.github.com/ianmiell/947ff3fabc44ace617c6)

- [Configuring and uploading a MySql container](https://www.youtube.com/watch?v=snd2gdsEYTQ)

- [Building a win2048 container](https://www.youtube.com/watch?v=Wagof_wnRRY) cf: [Blog](http://zwischenzugs.wordpress.com/2014/05/09/docker-shutit-and-the-perfect-2048-game/)



Docs:
-----
- [User Guide](https://github.com/ianmiell/shutit/blob/master/assets/documentation.md)

- [Walkthrough](http://ianmiell.github.io/shutit/)




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
cd library/mysql
./build.sh
./run.sh
```

Overview
--------
While evaluating Docker for my corp (openbet.com) I reached a point where
using Dockerfiles was somewhat painful or verbose for complex and/or long and/or
configurable interactions. So we wrote our own for our purposes.

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
to get going with docker and start shipping containers (see create\_skeleton.sh
below).

As a by-product of this design, you can use it in a similar way to chef/puppet
(by taking an existing container and configuring it to remove and build a
specific module), but it's not designed for this purpose and probably won't 
be as useful for moving target systems.

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

Directory Structure
--------
Each module directory should contain modules that are grouped together somehow
and all/most often built as an atomic unit.
This grouping is left to the user to decide, but generally speaking a module
will have one relatively simple .py file.

Each module .py file should represent a single unit of build. Again, this unit's
scope is for the user to decide, but it's best that each module doesn't get too
large.

Within each module directory the following directories are placed as part of
`./shutit skeleton`.

- test
    - should contain ```test_`hostname`.sh``` executables which exit with a 
            code of 0 if all is ok.
- configs
    - default configuration files are placed here.
- context
    - equivalent to dockerfile context

These config files are also created, defaulted, and automatically sourced:

```
configs/build.cnf                  - 
```

And these files are also automatically created:

```
configs/README.md                  - README for filling out if required
run.sh                             - Script to run modules built with build.sh
build.sh                           - Script to build the module
```

Configuration
--------
See config files (in configs dirs) for guidance on setting config.

Tests
--------
Run 

```
./test.sh
```




Known Issues
--------------
Since a core technology used in this application is pexpect - and a typical
usage pattern is to expect the prompt to return. Unusual shell
prompts and escape sequences have been known to cause problems.
Use the ```shutit.setup_prompt()``` function to help manage this by setting up
a more sane prompt.
Use of ```COMMAND_PROMPT``` with ```echo -ne``` has been seen to cause problems
with overwriting of shells and pexpect patterns.


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

