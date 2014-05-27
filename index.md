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
git clone https://github.com/ianmiell/shutit.git
```

### Step 2: Create a new module ###

```sh
cd shutit
./shutit skeleton $HOME/shutit_modules/my_module my_module my.domain.com
cd $HOME/shutit_modules/my_module
```

Folder structure:

 - **/configs** - config for your module *(see example below)*
 - **/resources** - files needed that are too big for source control *(see example below)*

An example folder structure:

```
./my_module
├── build.sh
├── configs
│   ├── build.cnf
│   └── defaults.cnf
├── README.md
├── resources
│   └── README.md
├── run.sh
└── test.sh
```

### Step 3: Modify the default module ###

The default module contains examples of many common tasks when installing, e.g.

 - install               - installs packages based on distro ('passwd' install in shutit_module.py)
 - password handling     - automate the inputting of passwords (changing 'password' in shutit_module.py)
 - config to set up apps - allows you to specify build parameters
 - add line to file      - incrementally construct files
 - send file             - or send them in one shot
 - pause_point           - allow you to stop during a build and inspect before continuing
 - handle logins/logouts - to make for safer automated interactions with eg unexpected prompts

It also gives a simple example of each part of the build lifecycle. **Add a package to install to shutit_module.py**

```python
# Make sure passwd is installed
shutit.install('passwd')
# Install mlocate
shutit.install('mlocate')

# Install added by you
shutit.install('your chosen package here')
```

**Running the module requires that in your shutit_module.py, shutit_module(string,float) is set:**

 - **string** is a python string that is not likely to clash, eg **'my.domain.com.myref'** (including quotes)
 - **float** is a unique decimal value that is not clashing with any other modules, and defines the order in which they are built

**Change the above and save the file**

```sh
$ grep -rnwl my.domain.com *
configs/build.cnf
configs/defaults.cnf
[...]
```

**Replace references to my.domain.com with your chosen string in the above files**

### Step 4: Build your module ###

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
	depends=['shutit.tk.setup']
```

to:

```python
	depends=['shutit.tk.setup', 'shutit.tk.mysql.mysql']
```

And change the **build.sh** to include the module in the path

```sh
/path/to/shutit build -m /your/path/to/shutit/example/mysql
```

Rebuild and re-run to get the same container with mysql installed.
