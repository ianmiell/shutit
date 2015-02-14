

[ShutIt](http://shutit.tk)
===============
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


REALLY QUICK START
------------------

See here:

http://ianmiell.github.io/shutit/

INSTALLATION
------------

See [INSTALL](http://github.com/ianmiell/shutit/blob/master/INSTALL.md)


WHAT DOES IT DO?
----------------
We start with a "Unit of Build", similar to a Dockerfile.

Unit of Build for Mongodb:

```
module:com.mycorp.mongo.mongodb
run order: 1234.1234
|---------------------------------------------------------------------------------------------------------------------------|
|apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10                                                               |
|echo "deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen" | tee -a /etc/apt/sources.list.d/10gen.list  |
|apt-get update                                                                                                             |
|apt-get -y install apt-utils                                                                                               |
|apt-get -y install mongodb-10gen                                                                                           |
|---------------------------------------------------------------------------------------------------------------------------|
```

We call this a ShutIt module. In this case, we'll give this the id: 

```
com.mycorp.mongo.mongodb
```

and the run order

```
1234.1234
```

Say we want to plug these together with other modules. ShutIt allows you do this.

But what if one module depends on another, eg mymongomodule which trivially adds a line to a config?

Unit of Build for MyMongoDB (com.mycorp.mongo.mymongodb):

```
module: com.mycorp.mongo.mymongodb
run order: 1235.1235
|-----------------------------------------------|
|(depend on com.mycorp.mongo.mongodb)           |
|echo "config item" >> /etc/somewhere/somefile  |
|-----------------------------------------------|
```

and give it a run order of 1235.1235. Note that the run order is higher, as we depend on the com.mycorp.mongo.mongodb module being there (ShutIt checks all this for you).

As you plug together more and more modules, you'll find you need a build lifecycle to manage how these modules interact and build.

What ShutIt does to manage this is:

- gathers all the modules it can find in its path and determines their ordering
- for all modules, it gathers any build-specific config (e.g. passwords etc.)
- it checks dependencies and conflicts across all modules and figures out which modules need to be built
- for all modules, it checks whether the module is already installed
- for all modules, if it needs building, it runs the build
- for all modules, run a test cycle to ensure everything is as we expect
- for all modules, run a finalize function to clean up the container
- do any configured committing, tagging and pushing of the image

These correspond to the various functions that can be implemented.

ShutIt provides a means for auto-generation of modules (either bare ones, or from existing Dockerfiles) with its skeleton command. See [here](http://ianmiell.github.io/shutit/) for an example.

CAN I CONTRIBUTE?
-----------------

We always need help, and with a potentially infinite number of libraries required, it's likely you will be able to contribute. Just mail ian.miell@gmail.com if you want to be assigned a mentor. [He won't bite](https://www.youtube.com/watch?v=zVUPmmUU3yY) 

Mailing List
------------
https://groups.google.com/forum/#!forum/shutit-users
shutit-users@groups.google.com

Dependencies
--------------
- python 2.7+
- pip
- See [here](https://gist.github.com/ianmiell/947ff3fabc44ace617c6) for a minimal build.


Videos:
-------

- [Talk on ShutIt](https://www.youtube.com/watch?v=zVUPmmUU3yY) 

- [Setting up a ShutIt server in 3 minutes](https://www.youtube.com/watch?v=ForTMTUMp3s)

- [Steps for above](https://gist.github.com/ianmiell/947ff3fabc44ace617c6)

- [Configuring and uploading a MySql container](https://www.youtube.com/watch?v=snd2gdsEYTQ)

- [Building a win2048 container](https://www.youtube.com/watch?v=Wagof_wnRRY) cf: [Blog](http://zwischenzugs.wordpress.com/2014/05/09/docker-shutit-and-the-perfect-2048-game/)



Docs:
-----

- [Walkthrough](http://ianmiell.github.io/shutit/)
- [Config](https://github.com/ianmiell/shutit/blob/master/util.py#L55)


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


# ShutIt User Guide

## Design goals

ShutIt was built originally to facilitate the deployment of complex Docker containers, so that developers can quickly prototype builds in a structured and flexible way with as shallow a learning curve as possible.

A ShutIt build is a programmable way of managing builds by modelling shell interactions.


## Key concepts
	
### Build

A ShutIt build consists of all the modules available going through the ShutIt Build lifecycle. This results in a container in a state from which it can be tagged, saved, exported, and/or pushed depending on your configuration.

### Module

A ShutIt module is a directory containing the configuration for the setup of a discrete unit of configuration.

This can be as simple as an apt-get install, a sequence of steps to get your package configured correctly, or a series of steps to set up networking for the a build, or anything else you deem useful to encapsulate as part of your build.

A module must inherit from ShutItModule and implement, as a mimimum, "is_installed" and "build" methods.

Each module has several attributes whose implications should be understood as they handle build order and dependency management:

#### module_id

A string - which should be globally unique - that represents this module's place in the ShutIt universe. By convention this follows the Java namespacing model of domain_name.namespace.module, eg

com.openbet.web.application

#### run_order

A float which represents the order in which this should be run in the ShutIt universe. 

The integer part should be a hash (in util.get_hash(string))of the domain used within themodule_id, eg com.openbet hashes to 1003189494. This is autogenerated by the "shutit skeleton" command (see below), which takes the domain as an argument.

The decimal part should be the order in which this module should be run within that ShutIt domain. 

This allows you to define a specific build order that is predictable.

#### description

Free text description of the module's purpose.

#### depends

List of module_ids of modules that are pre-requisites of this module.

#### conflicts

List of module_ids of modules that conflict with this module.


 

### ShutIt Build Lifecycle

#### Details

- Gather modules

Searches the modules directories given in the -m/--shutit_modules_dir argument for valid .py files to consider as part of the build.

- Gather configuration

Configuration is gathered in the following order:

1) Defaults loaded within the code

2) The following (auto-created) file is searched for: ~/.shutit/config 

This file can contain host-specific overrides, and is optional

3) configs/build.cnf is loaded from the current working directory of the shutit invocation

4) 0-n config files passed in with --config arguments are loaded

5) Command-line overrides, eg "-s com.mycorp.mymodule.module name value"

All config files need to have permissions 0x00.

- Check for conflicts

Module dependencies are checked to see whether there are any marked conflicts

- Check ready on all modules

Allows modules to determine whether the install can go ahead, eg are the requisite files in place?

- Record configuration

Gets the configuration and places it in the container in case it's useful later. Passwords are obfuscated with a repeated SHA-1 hash.

- Remove modules configured for removal

If you start with a full build image and want to test the rebuild of a module, then you can configure modules for removal as part of the build and they will be removed before being built.

- Build modules

Builds the module given the commands that are programmed.

At the end of each module, each module can be configured to tag, export, save, or push the resulting container.

- Test modules

Modules are tested using the test hooks for each module.

- Finalize modules

There's a final cleanup function that's run on each module before the end

- Finalize container

The container is finalized by the core setup module. As part of this it will tag, export, save, or push the resulting image depending on configuration.



#### Module hook functions

These all return True if OK (or the answer is "yes" for is\_installed), or False if not OK (or the answer is "no" for is\_installed).

If False is returned for all functions (except is\_installed), the build will fail.

- is\_installed

Used by "Check ready" part of lifecycle to determine whether the module is installed or not.

- remove

Handles the removal of the module. Useful for quick test of a recently-changed module.

- build

Handles the building of the module

- start

Handles the starting of the module. When tests are run all modules that have been built or are installed are started up.

- stop

Handles the stopping of the module. When any kind of persistence is performed, all modules that have been built or are installed are stopped first, then started again once done.

- test

Handles the testing of the module.

- get\_config

Gathers configuration for the module.


#### Module dependencies

Module conflicts

	


	
## Invocation

General help:

```
$ shutit -h
```

Build:

```
$ shutit build -h
```

Create new skeleton module:

```
$ shutit skeleton -h
```

Show computed configuration:

```
$ shutit list-config -h
```



## ShutIt API

### Introduction

The shutit object represents a build with an associated config. In theory multiple builds could be represented within one run, but this is functionality yet to be implemented. 

Calling methods on the object effect and affect the build in various ways and help manage the build process for you.

### Configuration

Configuration is specified in .cnf files.

Default config is shown [here](https://github.com/ianmiell/shutit/blob/master/util.py#L55)


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

Tests
--------
Run 

```
cd test && ./test.sh
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

