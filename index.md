---
layout: default
markdown: 1
---
# ShutIt #

Configuration management for the future.

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
```sh
git clone https://github.com/ianmiell/shutit
```

### Step 2: Create a new module ###

```sh
cd shutit/bin
./create_skeleton.sh /home/username/shutit_modules/shutit_module shutit_module
cd /home/username/shutit_modules/shutit_module
```

Folder structure:

 - **/bin** - scripts for this module *(see example below)*
 - **/configs** - config for your module *(see example below)*
 - **/resources** - files needed that are too big for source control *(see example below)*

An example folder structure:

```
./shutit_module
├──  bin
│   ├── create_skeleton.sh
│   ├── README.md
│   └── test.sh
├── build.sh
├── configs
│   ├── build.cnf
│   └── defaults.cnf
├── README.md
├── resources
│   └── README.md
└── run.sh
```

### Step 3: Modify the default module ###

The default module contains examples of many common tasks when installing, e.g.

 - util.install                               - installs packages based on distro (eg 'passwd' install in shutit_module.py)
 - password handling                          - automate the inputting of passwords (eg 'passwd' install in shutit_module.py)
 - config to set up apps                      - (eg 'passwd' install in shutit_module.py)
 - add line to file                           - automate the input-ing of passwords
 - util.pause_point                           - to allow you to stop during a build and inspect before continuing
 - handle logins/logouts                      - to make for safer automated interactions with eg unexpected prompts
 - pull resources in and out of the container - for objects too big for source control

It also gives a simple example of each part of the build lifecycle. **Add a package to install to shutit_module.py**

```python
# Make sure passwd is installed
util.install(container_child,config_dict,'passwd',root_prompt_expect)
# Install mlocate
util.install(container_child,config_dict,'mlocate',root_prompt_expect)

# Install added by you
util.install(container_child,config_dict,'your chosen package here',root_prompt_expect)
```

**Running the module requires that in your shutit_module.py, shutit_module(string,float) is set:**

 - **string** is a python string that is not likely to clash, eg **'com.mydomain.mysubmodule.myref'** (including quotes)
 - **float** is a unique decimal value that is not clashing with any other modules, and defines the order in which they are built

**Change the above and save the file**

```sh
$ grep -rnwl com.mycorp.shutit_module *
configs/build.cnf
configs/defaults.cnf
[...]
```

**Replace references to com.mycorp.shutit_module with your chosen string in the above files**

### Step 4: Build your module ###

```sh
$ ./build.sh
ERROR!
Files are not secure, mode should be 0600. Run the following commands to correct:

chmod 0600 [...]/defaults.cnf
```

**Secure your files:**

```sh
chmod 0600 configs/defaults.cnf
```

**Build module:**

```sh
$ ./build.sh
SHUTIT_BACKUP_PS1=$PS1 && unset PROMPT_COMMAND && PS1="SHUTIT_PROMPT_REAL_USER#195886238"
SHUTIT_BACKUP_PS1=$PS1 && unset PROMPT_COMMAND && PS1="SHUTIT_PROMPT_REAL_USER#195886238"
set PROMPT_COMMAND && PS1="SHUTIT_PROMPT_REAL_USER#195886238"CKUP_PS1=$PS1 && un 
SHUTIT_PROMPT_REAL_USER#195886238SHUTIT_BACKUP_PS1=$PS1 && unset PROMPT_COMMAND && PS1="SHUTIT_PROMPT_PRE_BUILD#1454501189"
PT_PRE_BUILD#1454501189"& unset PROMPT_COMMAND && PS1="SHUTIT_PROM
```

### Step 5: Run your module ###

```sh
$ ./run.sh
root@138ed0fd3728:/#
```

You are now in your bespoke container!

### Step 6: Mix and match ###

Let's add mysql to the container build. Change this in your **shutit_module.py:**

```python
obj.add_dependency('shutit.tk.setup')
```

to:

```python
obj.add_dependency('shutit.tk.setup')
obj.add_dependency('shutit.tk.mysql.mysql')
```

And change the **build.sh** to include the module in the path

```sh
python /tmp/a/shutit/bin/../shutit_main.py --shutit_module_path /your/path/to/shutit/example/mysql
```

Rebuild and re-run to get the same container with mysql installed.
