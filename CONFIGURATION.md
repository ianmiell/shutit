Configuration
=============

Configuration in shutit is computed in the following order:

- Defaults      (code)
- Host Config   (~/.shutit/config)
- Built Modules (/path/to/module/build.cnf)
- Pushed Module (/path/to/module/push.cnf)
- Command Line  (-s section name value)

Configuration follows the standard Python configuration form of:

```sh
[section]
name:value
```





Module Configuration Sections
=============================
Modules' configuration is 




Global Configuration Sections
=============================


Global Configuaration Names
===========================



Tools
=====

```sh
shutit sc -m /path/to/modules
```

Runs a built to the point where its configuration is calculated.


```sh
shutit sc -m /path/to/modules --history
```

Also tells you where the configuration was taken from.


Passwords
=========
Any 
