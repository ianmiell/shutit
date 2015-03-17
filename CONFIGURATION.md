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

Defaults are the config items set in the code.

If a setting is required but not present, an error is thrown on startup.

### Host Config

A file is automatically created in ~/.shutit/config which is read in by ShutIt after the defaults stage.

This file should contain configuration specific to your host environment, for example:

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


### Command Line

Arguments can be passed in on the command line using the -s flag. For example:

```sh
shutit build -m /opt/git/shutit/library -s host docker_executable mydockerbinary
```

## Module Configuration Sections

Module-level configuration uses the module's string id for the section name, eg:

```sh
[com.mycorp.mymodule]
myname:myvalue
```


## Global Configuration Sections

These are documented in the shutit_util.py file (search for "Default core config file for ShutIt.").

## Global Configuaration Names

Some configuration name:value pairs are required for each module:

| name | Description | Example | Default |
|------|--------|----|----|
| shutit.core.module.build | Whether to build this module | yes | no |
| shutit.core.module.allowed_images | ["debian:.*","ubuntu:trusty","johnsmith/.*"] | [".*"] |
| shutit.core.module.remove | Whether to remove this module at the start of the build | yes | no |
| shutit.core.module.tag | Whether to tag this module when building it is complete | yes | no |


eg to ensure the com.mycorp.mymodule module is built, and to allow it to be 
build against any base image, the computed configuration must be:

```sh
[com.mycorp.mymodule]
shutit.core.module.build:yes
shutit.core.module.allowed_images:[.*]
```



## Tools

```sh
shutit list_configs -m /path/to/modules
```

Runs a built to the point where its configuration is calculated.


```sh
shutit list_configs -m /path/to/modules --history
```

Also tells you where the configuration was taken from.

Note that any name:value pair where the name is "password" is sha1'd when printed out.

## File permissions

All .cnf files must be secure (ie have permissions of 0600) for ShutIt to successfully start up. This is because they may have plain text passwords or keys in them.
