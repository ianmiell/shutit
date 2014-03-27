ShutIt
===============

REALLY QUICK START
------------------

 ```
 cd bin
 ./create_skeleton.sh <new_directory (absolute path)> <new module name>
 ```

and follow instructions.


REALLY QUICK OVERVIEW
---------------------
You'll be interested in this if you:

- Want to take your scripts and turn them into stateless containers quickly,
without needing to learn or maintain a configuration management solution.

- Are a programmer who wants to highly configurable containers for
differing use cases and environments.

- Find dockerfiles a great idea, but limiting in practise.

Overview
--------
While evaluating Docker for my corp I reached a point where using Dockerfiles
was somewhat painful or verbose for complex and/or long and/or configurable
interactions. So we wrote our own for our purposes.

ShutIt works in the following way:

- It runs a docker container (base image configurable)
- Within this container it runs through configurable set of modules (each with
  a globally unique module id) that runs in a defined order with a standard lifecycle:
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
     - handle_login/revert_login (to handle shell prompt oddities in a 
       reliable/predictable way)
     - is user_id_available
     - set_password (package-management aware)
     - file_exists
     - get_file_perms
     - get_distro_info
     - package_installed (determine whether package is already installed)
     - loads more to come

If you have an existing bash script it is relatively trivial to port to this 
to get going with docker and start shipping containers (see create\_skeleton.sh
below).

As a by-product of this design, you can use it in a similar way to chef/puppet
(by taking an existing container and configuring it to remove and build a
specific module), but it's not designed for this purpose and probably won't 
be as useful for moving target systems.

Chef/Puppet were suggested as alternatives, but for several reasons I didn't go with them:

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



It is designed to:

- create static containers in as deterministic and predictable way as manageable
- handle complex inputs and outputs
- easy to learn
- easy to convert existing shell scripts
- have (limited) functionality for rebuilding specific modules

If you are a sysadmin looking for something to manage dynamic, moving target systems
stick with chef/puppet. If you're a programmer who wants to manage a bunch of 
existing scripts in a painless way, keep on reading.

Directory Structure
--------
Each module directory should contain modules that are grouped together somehow
and all/most often built as an atomic unit.
This grouping is left to the user to decide, but generally speaking a module will
have one relatively simple .py file.

Each module .py file should represent a single unit of build. Again, this unit's
scope is for the user to decide, but it's best that each module doesn't get too
large.

Within each module directory the following directories are placed as part of
create\_skeleton.sh:

- test
    - should contain ```test_`hostname`.sh``` executables which exit with a 
            code of 0 if all is ok.
- resources
    - mount point for container during build. Files too big to be part of
      source control can be  or read from here. Can be controlled through
      cnf files ([host]/resources_dir:directory); it's suggested you set
      this in ```/path/to/shutit/configs/`hostname`_`username`.cnf``` to 
      ```/path/to/shutit/resources```
- configs
    - default configuration files are placed here

The following files are also created, defaulted, and automatically sourced
(where applicable):

```
configs/defaults.cnf               - 
configs/build.cnf                  - 
configs/`hostname`_`whoami`.cnf    - 
configs/README.md                  - README for filling out if required
resources/README.md                - README for filling out if required
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
 pushd bin
 ./test.sh
 popd
 ```

Known Issues
--------------
Since a core technology used in this application is pexpect, unusual shell
prompts and escape sequences have been known to cause problems.
Use ```util.handle_login()``` and ```util.handle_revert_prompt()``` functions to help
manage this.
Use of ```COMMAND_PROMPT``` with ```echo -ne``` has been seen to cause problems with
overwriting of shells and pexpect patterns.


Licence
------------

The MIT License (MIT)

Copyright (C) 2014 OpenBet Limited

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

