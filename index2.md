---
layout: default
markdown: 1
---
# ShutIt #
### Configuration management for the future. ###

## Why? ##

Interested in Docker? Find Dockerfiles limiting?

Are you a programmer annoyed by the obfuscation and indirection Chef/Puppet/Ansible brings to a simple series of commands?

Interested in stable stateless deployments?

Join us!

## Features ##
 - Easy to use
 - Deterministic builds
 - Outputs include a series of shell commands you can port to other CM tools
 - Automate your pushing and deployment in one place
 - Shell-based (minimal learning curve)
 - Implement your own tests of modules that are automatically run
 - Use your python skills to make it work the way you want
 - Extensive debugging tools to make reproducible builds easier
 - Util functions for common tasks (that work across distros)

### Step 1: Get the source ###
```shell
git clone https://github.com/ianmiell/shutit
```

###Step 2: Create a new module
```shell
cd shutit/bin
./create_skeleton.sh /home/username/shutit_modules/shutit_module shutit_module
cd /home/username/shutit_modules/shutit_module
```
