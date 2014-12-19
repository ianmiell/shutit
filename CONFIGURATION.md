# ShutIt Configuration

## Basics

Configuration follows the standard Python configuration form of:

```sh
[section]
name:value
```

## Precedence

Configuration in shutit is processed in the following order:

| Type          | Whence |
| -------------- | ------ |
| Defaults      | code |
| Host Config   | `~/.shutit/config` |
| Built Modules | `/path/to/module_marked_for_build/build.cnf` |
| Passed-in Config Files | `--config /path/to/config` |
| Command Line  | `-s section name value` |

### Defaults

Defaults exist in the code somewhere.

### Host Config

A file is automatically created in ~/.shutit/config which is read first by ShutIt.

This file should contain configuration specific to your host, for example 

```sh
[host]
docker_executable:sudo docker

[build]
net:host
```

which will ensure that docker is called with `sudo docker` and the net:host option is used when invoking docker for the build.

### Built Modules

Modules that are configured to be built then have their code's config/build.cnf read in.

By default the directory you are running in will have any config/build.cnf read in. Generally this
build.cnf will have the shutit.core.module.build setting set to "yes" for the local module but
if it doesn't, your module will not get built! This setting is automatically set to yes when 
using the ```shutit skeleton``` command, so you normally never see this problem.

Just because a module is visible to ShutIt does not mean that it will have its build.cnf 
included. It will only be included if the module is a dependency of another module marked for
building.

### Passed-in Config Files

Any files passed in with the command line argument `--config` are processed immediately prior to
any `-s` options.


## Module Configuration Sections

Modules' configuration uses the module id as the section name, eg:

```sh
[com.mycorp.mymodule]
myname:myvalue
```


## Global Configuration Sections


## Global Configuaration Names

Some configuration name:value pairs are required for each module:

shutit.core.module.build 
shutit.core.module.allowed_images
shutit.core.module.remove
shutit.core.module.tag


eg to ensure the com.mycorp.mymodule module is built, and to allow it to be 
build against any base image, the computed configuration must be:

```sh
[com.mycorp.mymodule]
shutit.core.module.build:yes
shutit.core.module.allowed_images:[.*]
```



## Tools

```sh
shutit sc -m /path/to/modules
```

Runs a built to the point where its configuration is calculated.


```sh
shutit sc -m /path/to/modules --history
```

Also tells you where the configuration was taken from.

Note that any name:value pair where the name is "password" is sha1'd when printed out.

## File permissions
