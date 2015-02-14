Known Issues
--------------
Since a core technology used in this application is pexpect - and a typical
usage pattern is to expect the prompt to return. Unusual shell
prompts and escape sequences have been known to cause problems.
Use the ```shutit.setup_prompt()``` function to help manage this by setting up
a more sane prompt.
Use of ```COMMAND_PROMPT``` with ```echo -ne``` has been seen to cause problems
with overwriting of shells and pexpect patterns.

