"""Contains all the core ShutIt methods and functionality.
"""

#The MIT License (MIT)
#
#Copyright (C) 2014 OpenBet Limited
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of
#this software and associated documentation files (the "Software"), to deal in
#the Software without restriction, including without limitation the rights to
#use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#of the Software, and to permit persons to whom the Software is furnished to do
#so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#ITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

import sys
import os
import shutil
import socket
import time
import util
import random
import string
import re
import textwrap
import base64
import getpass
import package_map
import datetime
from shutit_module import ShutItFailException


def random_id(size=5, chars=string.ascii_letters + string.digits):
    """Generates a random string of given size from the given chars.
    size    - size of random string
    chars   - constituent pool of characters to draw random characters from
    """
    return ''.join(random.choice(chars) for _ in range(size))


class ShutIt(object):
    """ShutIt build class.
    Represents an instance of a ShutIt build with associated config.
    """


    def __init__(self, **kwargs):
        """Constructor.
        Sets up:

        - pexpect_children   - pexpect objects representing shell interactions
        - shutit_modules     - representation of loaded shutit modules
        - shutit_main_dir    - directory in which shutit is located
        - cfg                - dictionary of configuration of build
        - cwd                - working directory of build
        - shutit_map         - maps module_ids to module objects
        """
        # These used to be in shutit_global, so we pass them in as args so
        # the original reference can be put in shutit_global
        self.pexpect_children       = kwargs['pexpect_children']
        self.shutit_modules         = kwargs['shutit_modules']
        self.shutit_main_dir        = kwargs['shutit_main_dir']
        self.cfg                    = kwargs['cfg']
        self.cwd                    = kwargs['cwd']
        self.shutit_command_history = kwargs['shutit_command_history']
        self.shutit_map             = kwargs['shutit_map']
        # These are new members we dont have to provide compaitibility for
        self.conn_modules = set()

        # Hidden attributes
        self._default_child      = [None]
        self._default_expect     = [None]
        self._default_check_exit = [None]


    def module_method_start(self):
        """Gets called automatically by the metaclass decorator in
        shutit_module when a module method is called.
        This allows setting defaults for the 'scope' of a method.
        """
        if self._default_child[-1] is not None:
            self._default_child.append(self._default_child[-1])
        if self._default_expect[-1] is not None:
            self._default_expect.append(self._default_expect[-1])
        if self._default_check_exit[-1] is not None:
            self._default_check_exit.append(self._default_check_exit[-1])


    def module_method_end(self):
        """Gets called automatically by the metaclass decorator in
        shutit_module when a module method is finished.
        This allows setting defaults for the 'scope' of a method.
        """
        if len(self._default_child) != 1:
            self._default_child.pop()
        if len(self._default_expect) != 1:
            self._default_expect.pop()
        if len(self._default_check_exit) != 1:
            self._default_check_exit.pop()


    def get_default_child(self):
        """Returns the currently-set default pexpect child.
        """
        if self._default_child[-1] is None:
            shutit.fail("Couldn't get default child")
        return self._default_child[-1]


    def get_default_expect(self):
        """Returns the currently-set default pexpect string (usually a prompt).
        """
        if self._default_expect[-1] is None:
            shutit.fail("Couldn't get default expect")
        return self._default_expect[-1]


    def get_default_check_exit(self):
        """Returns default value of check_exit. See send method.
        """
        if self._default_check_exit[-1] is None:
            shutit.fail("Couldn't get default check exit")
        return self._default_check_exit[-1]


    def set_default_child(self, child):
        """Sets the default pexpect child.
        """
        self._default_child[-1] = child


    def set_default_expect(self, expect=None, check_exit=True):
        """Sets the default pexpect string (usually a prompt).
                Defaults to the configured root_prompt if no
        argument is passed.
        """
        if expect == None:
            expect = self.cfg['expect_prompts']['root_prompt']
        self._default_expect[-1] = expect
        self._default_check_exit[-1] = check_exit


    # TODO: Manage exits of containers on error
    def fail(self, msg, child=None):
        """Handles a failure, pausing if a pexpect child object is passed in.
        """
        # Note: we must not default to a child here
        if child is not None:
            self.pause_point('Pause point on fail: ' + msg, child=child)
        print >> sys.stderr, 'ERROR!'
        print >> sys.stderr
        raise ShutItFailException(msg)


    def log(self, msg, code=None, pause=0, prefix=True, force_stdout=False):
        """Logging function.

        - code         - Colour code for logging. Ignored if we are in serve mode.
        - pause        - Length of time to pause after logging (default: 0)
        - prefix       - Whether to output logging prefix (LOG: <time>) (default: True)
        - force_stdout - If we are not in debug, put this in stdout anyway (default: False)
        """
        if prefix:
            prefix = 'LOG: ' + time.strftime("%Y-%m-%d %H:%M:%S", 
                time.localtime())
            msg = prefix + ' ' + str(msg)
        # Don't colour message if we are in serve mode.
        if code != None and not self.cfg['action']['serve']:
            msg = util.colour(code, msg)
        if self.cfg['build']['debug'] or force_stdout:
            print >> sys.stdout, msg
            sys.stdout.flush()
        if self.cfg['build']['build_log']:
            print >> cfg['build']['build_log'], msg
            self.cfg['build']['build_log'].flush()
        time.sleep(pause)


    def send(self,
             send,
             expect=None,
             child=None,
             timeout=3600,
             check_exit=None,
             fail_on_empty_before=True,
             record_command=None,
             exit_values=None,
             echo=None):
        """Send string as a shell command, and wait until the expected output
        is seen (either a string or any from a list of strings) before
        returning. The expected string will default to the currently-set
        default expected string (see get_default_expect)

        Returns the pexpect return value (ie which expected string in the list
        matched)

        Arguments:

        - child                      - pexpect child to issue command to.
        - send                       - String to send, ie the command being
                                       issued.
        - expect                     - String that we expect to see in the
                                       output. Usually a prompt. Defaults to
                                       currently-set expect string (see
                                       set_default_expect)
        - timeout                    - Timeout on response
                                       (default=3600 seconds).
        - check_exit                 - Whether to check the shell exit code of
                                       the passed-in command.  If the exit value
                                       was non-zero an error is thrown.
                                       (default=None, which takes the
                                       currently-configured check_exit value)
                                       See also fail_on_empty_before.
        - fail_on_empty_before       - If debug is set, fail on empty match
                                       output string (default=True)
                                       If this is set to False, then we don't
                                       check the exit value of the command.
        - record_command             - Whether to record the command for output
                                       at end (default=True). As a safety
                                       measure, if the command matches any
                                       'password's then we don't record it.
        - exit_values                - Array of acceptable exit values
                                       (default [0])
        - echo                       - Whether to suppress any logging output
                                       from pexpect to the terminal or not.
                                       We don't record the command if this is
                                       set to False unless record_command is
                                       explicitly passed in as True.
        """
        child = child or self.get_default_child()
        expect = expect or self.get_default_expect()
        # If check_exit is not passed in
        # - if the expect matches the default, use the default check exit
        # - otherwise, default to doing the check
        if check_exit == None:
            if expect == self.get_default_expect():
                check_exit = self.get_default_check_exit()
            else:
                # If expect given doesn't match the defaults and no argument
                # was passed in (ie check_exit was passed in as None), set
                # check_exit to true iff it matches a prompt.
                expect_matches_prompt = False
                for prompt in cfg['expect_prompts']:
                    if prompt == expect:
                        expect_matches_prompt = True
                if not expect_matches_prompt:
                    check_exit = False
                else:
                    check_exit = True
        ok_to_record = False
        if echo == False and record_command == None:
            record_command = False
        if record_command == None or record_command:
            ok_to_record = True
            for i in cfg.keys():
                if isinstance(cfg[i], dict):
                    for j in cfg[i].keys():
                        if ((j == 'password' or j == 'passphrase') 
                                and cfg[i][j] == send):
                            self.shutit_command_history.append \
                                ('#redacted command, password')
                            ok_to_record = False
                            break
                    if not ok_to_record:
                        break
            if ok_to_record:
                self.shutit_command_history.append(send)
        if cfg['build']['debug']:
            self.log('===================================================' + 
                '=============================')
            self.log('Sending>>>' + send + '<<<')
            self.log('Expecting>>>' + str(expect) + '<<<')
        # Don't echo if echo passed in as False
        if echo == False:
            oldlog = child.logfile_send
            child.logfile_send = None
            child.sendline(send)
            expect_res = child.expect(expect, timeout)
            child.logfile_send = oldlog
        else:
            child.sendline(send)
            expect_res = child.expect(expect, timeout)
        if cfg['build']['debug']:
            self.log('child.before>>>' + child.before + '<<<')
            self.log('child.after>>>' + child.after + '<<<')
        if fail_on_empty_before == True:
            if child.before.strip() == '':
                shutit.fail('before empty after sending: ' + send +
                    '\n\nThis is expected after some commands that take a ' + 
                    'password.\nIf so, add fail_on_empty_before=False to ' + 
                    'the send call', child=child)
        elif fail_on_empty_before == False:
            # Don't check exit if fail_on_empty_before is False
            self.log('' + child.before + '<<<')
            check_exit = False
            for prompt in cfg['expect_prompts']:
                if prompt == expect:
                    # Reset prompt
                    self.setup_prompt('reset_tmp_prompt', child=child)
                    self.revert_prompt('reset_tmp_prompt', expect,
                        child=child)
        cfg['build']['last_output'] = child.before
        if check_exit == True:
            # store the output
            self._check_exit(send, expect, child, timeout, exit_values)
        return expect_res
    # alias send to send_and_expect
    send_and_expect = send


    def _check_exit(self,
                    send,
                    expect=None,
                    child=None,
                    timeout=3600,
                    exit_values=None):
        """Internal function to check the exit value of the shell. Do not use.
        """
        expect = expect or self.get_default_expect()
        child = child or self.get_default_child()
        if exit_values is None:
            exit_values = ['0']
        # TODO: check that all values are strings.
        # Don't use send here (will mess up last_output)!
        child.sendline('echo EXIT_CODE:$?')
        child.expect(expect, timeout)
        res = self.get_re_from_child(child.before, 
            '^EXIT_CODE:([0-9][0-9]?[0-9]?)$')
        if res not in exit_values or res == None:
            if res == None:
                res = str(res)
            self.log('child.after: \n' + child.after + '\n')
            self.log('Exit value from command+\n' + send + '\nwas:\n' + res)
            msg = ('\nWARNING: command:\n' + send + 
                  '\nreturned unaccepted exit code: ' + 
                  res + 
                  '\nIf this is expected, pass in check_exit=False or ' + 
                  'an exit_values array into the send function call.')
            cfg['build']['report'] = cfg['build']['report'] + msg
            if cfg['build']['interactive'] >= 1:
                shutit.pause_point(msg + '\n\nPause point on exit_code != 0 (' +
                    res + '). CTRL-C to quit', child=child)
            else:
                raise Exception('Exit value from command\n' + send +
                    '\nwas:\n' + res)


    def run_script(self, script, expect=None, child=None, in_shell=True):
        """Run the passed-in string as a script on the container's command line.

        - script   - String representing the script. It will be de-indented
                     and stripped before being run.
        - expect   - See send()
        - child    - See send()
        - in_shell - Indicate whether we are in a shell or not.
        """
        child = child or self.get_default_child()
        expect = expect or self.get_default_expect()
        # Trim any whitespace lines from start and end of script, then dedent
        lines = script.split('\n')
        while len(lines) > 0 and re.match('^[ \t]*$', lines[0]):
            lines = lines[1:]
        while len(lines) > 0 and re.match('^[ \t]*$', lines[-1]):
            lines = lines[:-1]
        if len(lines) == 0:
            return True
        script = '\n'.join(lines)
        script = textwrap.dedent(script)
        # Send the script and run it in the manner specified
        if in_shell:
            script = ('set -o xtrace \n\n' + script + '\n\nset +o xtrace')
        self.send_file('/tmp/shutit_script.sh', script)
        self.send('chmod +x /tmp/shutit_script.sh', expect, child)
        self.shutit_command_history.append\
            ('    ' + script.replace('\n', '\n    '))
        if in_shell:
            ret = self.send('. /tmp/shutit_script.sh', expect, child)
        else:
            ret = self.send('/tmp/shutit_script.sh', expect, child)
        self.send('rm /tmp/shutit_script.sh', expect, child)
        return ret


    def send_file(self, path, contents, expect=None, child=None, log=True):
        """Sends the passed-in string as a file to the passed-in path on the
        container.

        - path     - Target location of file in container.
        - contents - Contents of file as a string. See log.
        - expect   - See send()
        - child    - See send()
        - log      - Log the file contents if in debug.
        """
        child = child or self.get_default_child()
        expect = expect or self.get_default_expect()
        if cfg['build']['debug']:
            self.log('=====================================================' + 
                '===========================')
            self.log('Sending file to' + path)
            if log:
                self.log('contents >>>' + contents + '<<<')
        # Try and echo as little as possible
        oldlog = child.logfile_send
        child.logfile_send = None
        # Prepare to send the contents as base64 so we don't have to worry about
        # special shell characters
        # TODO: hide the gory details:
        # http://stackoverflow.com/questions/5633472
        #stty_orig=`stty -g`
        #stty -echo
        #echo 'hidden section'
        #stty $stty_orig && echo forcenewline
        contents64 = base64.standard_b64encode(contents)
        # if replace funny chars
        path = path.replace(' ', '\ ')
        child.sendline("base64 --decode > " + path)
        child.expect('\r\n')
        # We have to batch the file up to avoid hitting pipe buffer limit. This
        # is 4k on modern machines (it seems), but we choose 1k for safety
        # https://github.com/pexpect/pexpect/issues/55
        batchsize = 1024
        for batch in range(0, len(contents64), batchsize):
            child.sendline(contents64[batch:batch + batchsize])
        # Make sure we've synced the prompt before we send EOF. I don't know why
        # this requires three sendlines to generate 2x'\r\n'.
        # Note: we can't rely on a '\r\n' from the batching because the file
        # being sent may validly be empty.
        child.sendline()
        child.sendline()
        child.sendline()
        child.expect('\r\n\r\n', timeout=999999)
        child.sendeof()
        # Done sending the file
        child.expect(expect)
        self._check_exit("#send file to " + path, expect, child)
        # Go to old echo
        child.logfile_send = oldlog


    def send_host_file(self,
                       path,
                       hostfilepath,
                       expect=None,
                       child=None,
                       log=True):
        """Send file from host machine to given path

        - path         - Path to send file to.
        - hostfilepath - Path to file from host to send to container.
        - expect       - See send()
        - child        - See send()
        - log          - arg to pass to send_file (default True)
        """
        child = child or self.get_default_child()
        expect = expect or self.get_default_expect()
        if os.path.isfile(hostfilepath):
            self.send_file(path, open(hostfilepath).read(), expect=expect, 
                child=child, log=log)
        elif os.path.isdir(hostfilepath):
            self.send_host_dir(path, hostfilepath, expect=expect,
                child=child, log=log)
        else:
            shutit.fail('send_host_file - file: ' + hostfilepath +
                ' does not exist as file or dir. cwd is: ' + os.getcwd(),
                child=child)


    def send_host_dir(self,
                      path,
                      hostfilepath,
                      expect=None,
                      child=None,
                      log=True):
        """Send directory and all contents recursively from host machine to
        given path.  It will automatically make directories on the container.

        - path         - Path to send file to
        - hostfilepath - Path to file from host to send to container
        - expect       - See send()
        - child        - See send()
        - log          - Arg to pass to send_file (default True)
        """
        child = child or self.get_default_child()
        expect = expect or self.get_default_expect()
        self.log('entered send_host_dir in: ' + os.getcwd())
        for root, subfolders, files in os.walk(hostfilepath):
            subfolders.sort()
            files.sort()
            for subfolder in subfolders:
                self.send('mkdir -p ' + path + '/' + subfolder)
                self.log('send_host_dir recursing to: ' + hostfilepath +
                    '/' + subfolder)
                self.send_host_dir(path + '/' + subfolder, hostfilepath +
                    '/' + subfolder, expect=expect, child=child, log=log)
            for fname in files:
                hostfullfname = os.path.join(root, fname)
                containerfname = os.path.join(path, fname)
                self.log('send_host_dir sending file hostfullfname to ' + 
                    'container file: ' + containerfname)
                self.send_file(containerfname, open(hostfullfname).read(), 
                    expect=expect, child=child, log=log)


    def file_exists(self, filename, expect=None, child=None, directory=False):
        """Return True if file exists on the container being built, else False

        - filename     - Filename to determine the existence of.
        - expect       - See send()
        - child        - See send()
        - directory    - Indicate that the file is a directory.
        """
        child = child or self.get_default_child()
        expect = expect or self.get_default_expect()
        test = 'test %s %s' % ('-d' if directory is True else '-a', filename)
        self.send(test +
            ' && echo FILEXIST-""FILFIN || echo FILNEXIST-""FILFIN',
            expect=expect, child=child, check_exit=False, record_command=False)
        res = self.get_re_from_child(child.before,
            '^(FILEXIST|FILNEXIST)-FILFIN$')
        ret = False
        if res == 'FILEXIST':
            ret = True
        elif res == 'FILNEXIST':
            pass
        else:
            # Change to log?
            print repr('before>>>>:%s<<<< after:>>>>%s<<<<' %
                (child.before, child.after))
            self.pause_point('Did not see FIL(N)?EXIST in before', child)
        return ret


    def get_file_perms(self, filename, expect=None, child=None):
        """Returns the permissions of the file on the container as an octal
        string triplet.

        - filename  - Filename to get permissions of.
        - expect    - See send()
        - child     - See send()
        """
        child = child or self.get_default_child()
        expect = expect or self.get_default_expect()
        cmd = 'stat -c %a ' + filename + r" | sed 's/.\(.*\)/\1/g'"
        self.send(cmd, expect, child=child, check_exit=False)
        res = self.get_re_from_child(child.before, '([0-9][0-9][0-9])')
        return res


    def add_line_to_file(self,
                         line,
                         filename, 
                         expect=None,
                         child=None,
                         match_regexp=None,
                         force=False,
                         literal=False):
        """Adds line to file if it doesn't exist (unless Force is set).
        Creates the file if it doesn't exist.
        Must be exactly the line passed in to match.
        Returns True if line added, False if not.
        If you have a lot of non-unique lines to add, it's a good idea to
        have a sentinel value to add first, and then if that returns true,
        force the remainder.
    
        - line         - Line to add.
        - filename     - Filename to add it to.
        - expect       - See send()
        - child        - See send()
        - match_regexp - If supplied, a regexp to look for in the file
                         instead of the line itself,
                         handy if the line has awkward characters in it.
        - force        - Always write the line to the file.
        - literal      - If true, then simply grep for the exact string without
                         bash interpretation.
        """
        child = child or self.get_default_child()
        expect = expect or self.get_default_expect()
        # assume we're going to add it
        res = '0'
        bad_chars    = '"'
        tmp_filename = '/tmp/' + random_id()
        if match_regexp == None and re.match('.*[' + bad_chars + '].*',
                line) != None:
            shutit.fail('Passed problematic character to add_line_to_file.\n' +
                'Please avoid using the following chars: ' + 
                bad_chars +
                '\nor supply a match_regexp argument.\nThe line was:\n' +
                line, child=child)
        if not self.file_exists(filename, expect=expect, child=child):
            # The above cat doesn't work so we touch the file if it
            # doesn't exist already.
            self.send('touch ' + filename, expect=expect, child=child,
                check_exit=False)
        elif not force:
            if literal:
                if match_regexp == None:
                    self.send("""grep -w '^""" + 
                              line +
                              """$' """ +
                              filename +
                              ' > ' + 
                              tmp_filename, 
                              expect=expect,
                              child=child,
                              exit_values=['0', '1'])
                else:
                    self.send("""grep -w '^""" + 
                              match_regexp + 
                              """$' """ +
                              filename +
                              ' > ' +
                              tmp_filename,
                              expect=expect,
                              child=child, 
                              exit_values=['0', '1'])
            else:
                if match_regexp == None:
                    self.send('grep -w "^' +
                              line +
                              '$" ' +
                              filename +
                              ' > ' +
                              tmp_filename,
                              expect=expect,
                              child=child,
                              exit_values=['0', '1'])
                else:
                    self.send('grep -w "^' +
                              match_regexp +
                              '$" ' +
                              filename +
                              ' > ' +
                              tmp_filename,
                              expect=expect,
                              child=child,
                              exit_values=['0', '1'])
            self.send('cat ' + tmp_filename + ' | wc -l',
                      expect=expect, child=child, exit_values=['0', '1'],
                      check_exit=False)
            res = self.get_re_from_child(child.before, '^([0-9]+)$')
        if res == '0' or force:
            self.send('cat >> ' + filename + """ <<< '""" + line + """'""",
                expect=expect, child=child, check_exit=False)
            self.send('rm -f ' + tmp_filename, expect=expect, child=child,
                exit_values=['0', '1'])
            return True
        else:
            self.send('rm -f ' + tmp_filename, expect=expect, child=child,
                exit_values=['0', '1'])
            return False


    def add_to_bashrc(self, line, expect=None, child=None):
        """Takes care of adding a line to everyone's bashrc
        (/etc/bash.bashrc, /etc/profile).

        - line   - Line to add.
        - expect - See send()
        - child  - See send()
        """
        child = child or self.get_default_child()
        expect = expect or self.get_default_expect()
        self.add_line_to_file(line, '/etc/bash.bashrc', expect=expect)
        return self.add_line_to_file(line, '/etc/profile', expect=expect)


    def user_exists(self, user, expect=None, child=None):
        """Returns true if the specified username exists.
        
        - user   - username to check for
        - expect - See send()
        - child  - See send()
        """
        child = child or self.get_default_child()
        expect = expect or self.get_default_expect()
        exist = False
        if user == '': return exist
        ret = shutit.send(
            'id %s && echo E""XIST || echo N""XIST' % user,
            expect=['NXIST', 'EXIST'], child=child
        )
        if ret:
            exist = True
        # sync with the prompt
        child.expect(expect)
        return exist


    def package_installed(self, package, expect=None, child=None):
        """Returns True if we can be sure the package is installed.

        - package - Package as a string, eg 'wget'.
        - expect  - See send()
        - child   - See send()
        """
        child = child or self.get_default_child()
        expect = expect or self.get_default_expect()
        if self.cfg['container']['install_type'] == 'apt':
            self.send("""dpkg -l | awk '{print $2}' | grep "^""" +
                package + """$" | wc -l""", expect, check_exit=False)
        elif self.cfg['container']['install_type'] == 'yum':
            self.send("""yum list installed | awk '{print $1}' | grep "^""" +
                package + """$" | wc -l""", expect, check_exit=False)
        else:
            return False
        if self.get_re_from_child(child.before, '^([0-9]+)$') != '0':
            return True
        else:
            return False


    def ls(self, directory):
        """Helper proc to list files in a directory

        Returns list of files.

        directory - directory to list
        """
        # should this blow up?
        if not shutit.file_exists(directory,directory=True):
            shutit.fail('ls: directory\n\n' + directory + '\n\ndoes not exist')
        files = shutit.send_and_get_output('ls ' + directory)
        files = files.split(' ')
        # cleanout garbage from the terminal - all of this is necessary cause there are
        # random return characters in the middle of the file names
        files = filter(bool, files)
        files = [file.strip() for file in files]
        f = []
        for file in files:
            spl = file.split('\r')
            f = f + spl
        files = f
        # this is required again to remove the '\n's
        files = [file.strip() for file in files]
        return files


    def mount_tmp(self):
        """mount a temporary file system as a workaround for the AUFS /tmp issues
            not necessary if running devicemapper
        """
        shutit.send('mkdir -p /tmpbak') # Needed?
        shutit.send('touch /tmp/' + cfg['build']['build_id']) # Needed?
        shutit.send('cp -r /tmp/* /tmpbak') # Needed?
        shutit.send('mount -t tmpfs tmpfs /tmp')
        shutit.send('cp -r /tmpbak/* /tmp') # Needed?
        shutit.send('rm -rf /tmpbak') # Needed?
        shutit.send('rm -f /tmp/' + cfg['build']['build_id']) # Needed?


    def get_file(self,container_path,host_path):
        """Copy a file from the docker container to the host machine, via the resources mount

            container_path - path to file in the container
            host_path      - path to file on the host machine (e.g. copy test)
        """
        filename = os.path.basename(container_path)
        resources_dir = shutit.cfg['host']['resources_dir']
        if shutit.get_file_perms('/resources') != "777":
            user = shutit.send_and_get_output('whoami').strip()
            # revert to root to do attachments
            if user != 'root':
                shutit.logout()
            shutit.send('chmod 777 /resources')
            # we've done what we need to do as root, go home
            if user != 'root':
                shutit.login(user)
        shutit.send('cp ' + container_path + ' /resources')
        shutil.copyfile(os.path.join(resources_dir,filename),os.path.join(host_path,filename))
        shutit.send('rm -f /resources/' + filename)


    def prompt_cfg(self, msg, sec, name, ispass=False):
        """Prompt for a config value, optionally saving it to the user-level
        cfg. Only runs if we are in an interactive mode.

        msg    - Message to display to user.
        sec    - Section of config to add to.
        name   - Config item name.
        ispass - Hide the input from the terminal.
        """
        cfgstr        = '[%s]/%s' % (sec, name)
        config_parser = cfg['config_parser']
        usercfg       = os.path.join(cfg['shutit_home'], 'config')

        if not cfg['build']['interactive']:
            shutit.fail('ShutIt is not in interactive mode so cannnot prompt ' +
                'for values.')

        print util.colour('34', '\nPROMPTING FOR CONFIG: %s' % (cfgstr,))
        print util.colour('34', '\n' + msg + '\n')

        if config_parser.has_option(sec, name):
            whereset = config_parser.whereset(sec, name)
            if usercfg == whereset:
                self.fail(cfgstr + ' has already been set in the user ' +
                    'config, edit ' + usercfg + ' directly to change it')
            for subcp, filename, _fp in reversed(config_parser.layers):
                # Is the config file loaded after the user config file?
                if filename == whereset:
                    self.fail(cfgstr + ' is being set in ' + filename + ', ' +
                        'unable to override on a user config level')
                elif filename == usercfg:
                    break
        else:
            # The item is not currently set so we're fine to do so
            pass
        if ispass:
            val = getpass.getpass('>> ')
        else:
            val = raw_input('>> ')
        is_excluded = (
            config_parser.has_option('save_exclude', sec) and
            name in config_parser.get('save_exclude', sec).split()
        )
        # TODO: ideally we would remember the prompted config item for this
        # invocation of shutit
        if not is_excluded:
            usercp = [
                subcp for subcp, filename, _fp in config_parser.layers
                if filename == usercfg
            ][0]
            if raw_input(util.colour('34',
                    'Do you want to save this to your ' +
                    'user settings? y/n: ')) == 'y':
                sec_toset, name_toset, val_toset = sec, name, val
            else:
                # Never save it
                if config_parser.has_option('save_exclude', sec):
                    excluded = config_parser.get('save_exclude', sec).split()
                else:
                    excluded = []
                excluded.append(name)
                excluded = ' '.join(excluded)
                sec_toset, name_toset, val_toset = 'save_exclude', sec, excluded
            if not usercp.has_section(sec_toset):
                usercp.add_section(sec_toset)
            usercp.set(sec_toset, name_toset, val_toset)
            usercp.write(open(usercfg, 'w'))
            config_parser.reload()
        return val


    def pause_point(self, msg, child=None, print_input=True, level=1):
        """Inserts a pause in the build session, which allows the user to try
        things out before continuing. Ignored if we are not in an interactive
        mode, or the interactive level is less than the passed-in one.
        Designed to help debug the build, or drop to on failure so the
        situation can be debugged.

        - msg         - Message to display to user on pause point.
        - child       - See send()
        - print_input - Whether to take input at this point (ie interact), or
                        simply pause pending any input.
        - level       - Minimum level to invoke the pause_point at
        """
        child = child or self.get_default_child()
        if (not self.cfg['build']['interactive'] or 
            self.cfg['build']['interactive'] < level):
            return
        if child and print_input:
            print (util.colour('31', '\n\nPause point:\n\n') + 
                msg + util.colour('31','\n\nYou can now type in commands and ' +
                'alter the state of the container.\nHit return to see the ' +
                'prompt\nHit CTRL and ] at the same time to continue with ' +
                'build\n\nHit CTRL and [ to save the state\n\n'))
            oldlog = child.logfile_send
            child.logfile_send = None
            try:
                child.interact(input_filter=self._pause_input_filter)
            except:
                shutit.fail('Failed to interact, probably because this is run non-interactively')
            child.logfile_send = oldlog
        else:
            print msg
            print util.colour('31', '\n\n[Hit return to continue]\n')
            raw_input('')


    def _pause_input_filter(self, input_string):
        """Input filter for pause point to catch special keystrokes"""
        # Can get errors with eg up/down chars
        if len(input_string) == 1:
            if ord(input_string) == 27:
                self.log('\n\nCTRL and [ caught, forcing a tag at least\n\n',
                    force_stdout=True)
                self.do_repository_work('tagged_by_shutit',
                    password=self.cfg['host']['password'],
                    docker_executable=self.cfg['host']['docker_executable'],
                    force=True)
                self.log('\n\nCommit and tag done\n\n', force_stdout=True)
        return input_string


    def get_output(self, child=None):
        """Helper function to get output from latest command run.

        - child       - See send()
        """
        child = child or self.get_default_child()
        return self.cfg['build']['last_output']


    def get_re_from_child(self, string, regexp):
        """Get regular expression from the first of the lines passed
        in in string that matched.

        Returns None if none of the lines matched.

        Returns True if there are no groups selected in the regexp.

        - string - string to search through lines of
        - regexp - regexp to search for per line
        """
        if cfg['build']['debug']:
            self.log('get_re_from_child:')
            self.log(string)
            self.log(regexp)
        lines = string.split('\r\n')
        for line in lines:
            if cfg['build']['debug']:
                self.log('trying: ' + line + ' against regexp: ' + regexp)
            match = re.match(regexp, line)
            if match != None:
                if len(match.groups()) > 0:
                    if cfg['build']['debug']:
                        self.log('returning: ' + match.group(1))
                    return match.group(1)
                else:
                    return True
        return None


    def send_and_get_output(self, send, expect=None, child=None):
        """Returns the output of a command run.
        send() is called, and exit is not checked.

        - send   - See send()
        - expect - See send()
        - child  - See send()
        """
        child = child or self.get_default_child()
        expect = expect or self.get_default_expect()
        self.send(send, check_exit=False)
        return shutit.get_default_child().before.strip(send)


    def install(self,
                package,
                child=None,
                expect=None,
                options=None,
                timeout=3600,
                force=False):
        """Distro-independent install function.
        Takes a package name and runs the relevant install function.
        Returns true if all ok (ie it's installed), else false.

        - package  - Package to install, which is run through package_map
        - expect   - See send()
        - child    - See send()
        - options  - 
        - timeout  - 
        - force    - force if necessary
        """
        #TODO: Temporary failure resolving
        child = child or self.get_default_child()
        expect = expect or self.get_default_expect()
        if options is None: options = {}
        # TODO: config of maps of packages
        install_type = self.cfg['container']['install_type']
        if install_type == 'apt':
            cmd = 'apt-get install'
            if self.cfg['build']['debug']:
                opts = options['apt'] if 'apt' in options else '-y'
            else:
                if force:
                    opts = options['apt'] if 'apt' in options else '-qq -y --force-yes'
                else:
                    opts = options['apt'] if 'apt' in options else '-qq -y'
        elif install_type == 'yum':
            cmd = 'yum install'
            opts = options['yum'] if 'yum' in options else '-y'
        else:
            # Not handled
            return False
        # Get mapped package.
        package = package_map.map_package(package,
            self.cfg['container']['install_type'])
        if package != '':
            fails = 0
            while True:
                res = self.send('%s %s %s' % (cmd, opts, package),
                    expect=['Unable to fetch some archives',expect],
                    timeout=timeout)
                if res == 1:
                    break
                else:
                    fails += 1
                if fails >= 3:
                    break
        else:
            # package not required
            pass
        return True


    def remove(self,
               package,
               child=None,
               expect=None,
               options=None,
               timeout=3600):
        """Distro-independent remove function.
        Takes a package name and runs relevant remove function.
        Returns true if all ok (ie it's installed now), else false.

        - package  - Package to install, which is run through package_map.
        - expect   - See send()
        - child    - See send()
        - options  - Dict of options to pass to the remove command,
                     mapped by install_type.
        - timeout  - See send()
        """
        child = child or self.get_default_child()
        expect = expect or self.get_default_expect()
        if options is None: options = {}
        # TODO: config of maps of packages
        install_type = self.cfg['container']['install_type']
        if install_type == 'apt':
            cmd = 'apt-get purge'
            opts = options['apt'] if 'apt' in options else '-qq -y'
        elif install_type == 'yum':
            cmd = 'yum erase'
            opts = options['yum'] if 'yum' in options else '-y'
        else:
            # Not handled
            return False
        # Get mapped package.
        package = package_map.map_package(package,
            self.cfg['container']['install_type'])
        self.send('%s %s %s' % (cmd, opts, package), expect, timeout=timeout)
        return True


    def login(self, user='root', command='su -', child=None, password=None):
        """Logs the user in with the passed-in password and command.
        Tracks the login. If used, used logout to log out again.
        Assumes you are root when logging in, so no password required.
        If not, override the default command for multi-level logins.
        If passwords are required, see setup_prompt() and revert_prompt()

        user     - User to login with
        command  - Command to login with
        child    - See send()
        """
        child = child or self.get_default_child()
        r_id = random_id()
        self.cfg['build']['login_stack'].append(r_id)
        res = self.send(command + ' ' + user,expect=['assword',shutit.cfg['expect_prompts']['base_prompt']],check_exit=False)
        if res == 0:
            if password != None:
                self.send(password,expect=shutit.cfg['expect_prompts']['base_prompt'],check_exit=False)
            else:
                shutit.fail('Please supply a password argument to shutit.login.')
        self.setup_prompt(r_id,child=child)


    def logout(self,child=None):
        """Logs the user out. Assumes that login has been called.
        If login has never been called, throw an error.

        - child              - See send()
        """
        child = child or self.get_default_child()
        if len(self.cfg['build']['login_stack']):
             current_prompt_name = self.cfg['build']['login_stack'].pop()
             if len(self.cfg['build']['login_stack']):
                 old_prompt_name     = self.cfg['build']['login_stack'][-1]
                 self.set_default_expect(self.cfg['expect_prompts'][old_prompt_name])
             else:
                 # If none are on the stack, we assume we're going to the root_prompt
                 # set up in setup.py
                 self.set_default_expect()
        else:
             self.fail('Logout called without corresponding login')
        self.send('exit')
        

    def setup_prompt(self,
                     prompt_name,
                     prefix='TMP',
                     child=None,
                     set_default_expect=True):
        """Use this when you've opened a new shell to set the PS1 to something
        sane. By default, it sets up the default expect so you don't have to
        worry about it and can just call shutit.send('a command').

        If you want simple login and logout, please use login() and logout()
        within this module.

        Typically it would be used in this boilerplate pattern:

        shutit.send('su - auser',
                    expect=shutit.cfg['expect_prompts']['base_prompt'],
                    check_exit=False)
        shutit.setup_prompt('tmp_prompt')
        shutit.send('some command')
        [...]
        shutit.set_default_expect()
        shutit.send('exit')

        - prompt_name        - Reference name for prompt.
        - prefix             - Prompt prefix.
        - child              - See send()
        - set_default_expect - Whether to set the default expect to the new prompt.
        """
        child = child or self.get_default_child()
        local_prompt = 'SHUTIT_' + prefix + '#' + random_id() + '>'
        shutit.cfg['expect_prompts'][prompt_name] = '\r\n' + local_prompt
        self.send(
            ("SHUTIT_BACKUP_PS1_%s=$PS1 && PS1='%s' && unset PROMPT_COMMAND") %
                (prompt_name, local_prompt),
            expect=self.cfg['expect_prompts'][prompt_name],
            fail_on_empty_before=False, timeout=5, child=child)
        if set_default_expect:
            shutit.log('Resetting default expect to: ' +
            shutit.cfg['expect_prompts'][prompt_name])
            self.set_default_expect(shutit.cfg['expect_prompts'][prompt_name])


    def revert_prompt(self, old_prompt_name, new_expect=None, child=None):
        """Reverts the prompt to the previous value (passed-in).

        It should be fairly rare to need this. Most of the time you would just
        exit a subshell rather than resetting the prompt.

        - old_prompt_name - 
        - new_expect      - 
        - child              - See send()
        """
        child = child or self.get_default_child()
        expect = new_expect or self.get_default_expect()
        self.send(
            ('PS1="${SHUTIT_BACKUP_PS1_%s}" && unset SHUTIT_BACKUP_PS1_%s') %
                (old_prompt_name, old_prompt_name),
            expect=expect, check_exit=False, fail_on_empty_before=False)
        if not new_expect:
            shutit.log('Resetting default expect to default')
            self.set_default_expect()


    def get_distro_info(self, child=None):
        """Get information about which distro we are using.

        Fails if distro could not be determined.
        Should be called with the container is started up, and uses as core info
        as possible.

        - child              - See send()
        """
        child = child or self.get_default_child()
        cfg['container']['install_type']      = ''
        cfg['container']['distro']            = ''
        cfg['container']['distro_version']    = ''
        install_type_map = {'ubuntu':'apt',
                            'debian':'apt',
                            'red hat':'yum',
                            'centos':'yum',
                            'fedora':'yum'}
        if self.package_installed('lsb_release'):
            self.send('lsb_release -a')
            dist_string = self.get_re_from_child(child.before,
                '^Distributor ID:[\s]*\(.*)$')
            if dist_string:
                cfg['container']['distro']       = dist_string.lower()
                cfg['container']['install_type'] = (
                    install_type_map[dist_string.lower()])
            # TODO: version
            #version = self.get_re_from_child(child.before,
            #    '^Release:[\s]*(.*)$')
        else:
            for key in install_type_map.keys():
                self.send('cat /etc/issue | grep -i "' + key + '" | wc -l',
                    check_exit=False)
                if self.get_re_from_child(child.before, '^([0-9]+)$') == '1':
                    cfg['container']['distro']       = key
                    cfg['container']['install_type'] = install_type_map[key]
                    break
        if (cfg['container']['install_type'] == '' or 
            cfg['container']['distro'] == ''):
            self.send('cat /etc/issue',check_exit=False)
            if self.get_re_from_child(child.before,'^Kernel .*r on an .*m$'):
                cfg['container']['distro']       = 'centos'
                cfg['container']['install_type'] = 'yum'
        if (cfg['container']['install_type'] == '' or 
            cfg['container']['distro'] == ''):
            shutit.fail('Could not determine Linux distro information. ' + 
                        'Please inform maintainers.', child=child)


    def set_password(self, password, user='', child=None, expect=None):
        """Sets the password for the current user or passed-in user.

        - password - 
        - user     - 
        - expect   - See send()
        - child    - See send()
        """
        child = child or self.get_default_child()
        expect = expect or self.get_default_expect()
        self.install('passwd')
        if cfg['container']['install_type'] == 'apt':
            self.send('passwd ' + user,
                      expect='Enter new', child=child, check_exit=False)
            self.send(password, child=child, expect='Retype new',
                      check_exit=False, echo=False)
            self.send(password, child=child, expect=expect, echo=False)
            self.install('apt-utils')
        elif cfg['container']['install_type'] == 'yum':
            self.send('passwd ' + user, child=child, expect='ew password',
                      check_exit=False)
            self.send(password, child=child, expect='ew password',
                      check_exit=False, echo=False)
            self.send(password, child=child, expect=expect, echo=False)


    def is_user_id_available(self, user_id, child=None, expect=None):
        """Determine whether a user_id for a user is available.

        - user_id  - 
        - expect   - See send()
        - child    - See send()
        """
        child = child or self.get_default_child()
        expect = expect or self.get_default_expect()
        self.send('cut -d: -f3 /etc/paswd | grep -w ^' + user_id + '$ | wc -l',
                  child=child, expect=expect, check_exit=False)
        if self.get_re_from_child(child.before, '^([0-9]+)$') == '1':
            return False
        else:
            return True


    def push_repository(self,
                        repository,
                        docker_executable='docker.io',
                        child=None,
                        expect=None):
        """Pushes the repository.

        - repository        - 
        - docker_executable -
        - expect            - See send()
        - child             - See send()
        """
        child = child or self.get_default_child()
        expect = expect or self.get_default_expect()
        send = docker_executable + ' push ' + repository
        expect_list = ['Username', 'Password', 'Email', expect]
        timeout = 99999
        self.log('Running: ' + send, force_stdout=True, prefix=False)
        res = self.send(send, expect=expect_list, child=child, timeout=timeout,
                        check_exit=False, fail_on_empty_before=False)
        while True:
            if res == 3:
                break
            elif res == 0:
                res = self.send(cfg['repository']['user'], child=child,
                                expect=expect_list, timeout=timeout,
                                check_exit=False, fail_on_empty_before=False)
            elif res == 1:
                res = self.send(cfg['repository']['password'], child=child,
                                expect=expect_list, timeout=timeout,
                                check_exit=False, fail_on_empty_before=False)
            elif res == 2:
                res = self.send(cfg['repository']['email'], child=child,
                                expect=expect_list, timeout=timeout,
                                check_exit=False, fail_on_empty_before=False)


    def do_repository_work(self,
                           repo_name,
                           repo_tag=None,
                           expect=None,
                           docker_executable='docker',
                           password=None,
                           force=None):
        """Commit, tag, push, tar the container based on the configuration we
        have.

        - repo_name         - 
        - expect            - See send()
        - docker_executable - 
        - password          - 
        - force             - 
        """
        expect = expect or self.get_default_expect()
        tag    = cfg['repository']['tag']
        push   = cfg['repository']['push']
        export = cfg['repository']['export']
        save   = cfg['repository']['save']
        if not (push or export or save or tag):
            # If we're forcing this, then tag as a minimum
            if force:
                tag = True
            else:
                return

        child     = self.pexpect_children['host_child']
        expect    = cfg['expect_prompts']['real_user_prompt']
        server    = cfg['repository']['server']
        repo_user = cfg['repository']['user']
        repo_tag  = cfg['repository']['tag_name']

        if repo_user and repo_name:
            repository = '%s/%s' % (repo_user, repo_name)
            repository_tar = '%s%s' % (repo_user, repo_name)
        elif repo_user:
            repository = repository_tar = repo_user
        elif repo_name:
            repository = repository_tar = repo_name
        else:
            repository = repository_tar = ''

        if not repository:
            shutit.fail('Could not form valid repository name', child=child)
        if (export or save) and not repository_tar:
            shutit.fail('Could not form valid tar name', child=child)

        if server:
            repository = '%s/%s' % (server, repository)

        if cfg['repository']['suffix_date']:
            suffix_date = time.strftime(cfg['repository']['suffix_format'])
            repository = '%s%s' % (repository, suffix_date)
            repository_tar = '%s%s' % (repository_tar, suffix_date)

        if repository != '':
            repository = repository + ':' + repo_tag

        if server == '' and len(repository) > 30 and push:
            shutit.fail("""repository name: '""" + repository +
                """' too long. If using suffix_date consider shortening""",
                child=child)

        # Commit image
        # Only lower case accepted
        repository = repository.lower()
        if self.send('SHUTIT_TMP_VAR=`' + docker_executable + ' commit ' +
                     cfg['container']['container_id'] + '`',
                     expect=[expect,'assword'], child=child, timeout=99999,
                     check_exit=False) == 1:
            self.send(cfg['host']['password'], expect=expect, check_exit=False,
                      record_command=False, child=child)
        self.send('echo $SHUTIT_TMP_VAR && unset SHUTIT_TMP_VAR', expect=expect,
                  check_exit=False, child=child)
        image_id = child.before.split('\r\n')[1]
        if not image_id:
            shutit.fail('failed to commit to ' + repository +
                        ', could not determine image id', child=child)

        # Tag image
        cmd = docker_executable + ' tag ' + image_id + ' ' + repository
        self.cfg['build']['report'] += '\nBuild tagged as: ' + repository
        self.send(cmd, child=child, expect=expect, check_exit=False)
        if export or save:
            self.pause_point('We are now exporting the container to a ' + 
                             'bzipped tar file, as configured in ' +
                             '\n[repository]\ntar:yes', print_input=False,
                             child=child, level=3)
            if export:
                bzfile = (cfg['host']['resources_dir'] + '/' + 
                          repository_tar + 'export.tar.bz2')
                self.log('\nDepositing bzip2 of exported container into ' +
                         bzfile)
                if self.send(docker_executable + ' export ' +
                             cfg['container']['container_id'] +
                             ' | bzip2 - > ' + bzfile,
                             expect=[expect, 'assword'], timeout=99999,
                             child=child) == 1:
                    self.send(password, expect=expect, child=child)
                self.log('\nDeposited bzip2 of exported container into ' +
                         bzfile, code='31')
                self.log('\nRun:\n\nbunzip2 -c ' + bzfile +
                         ' | sudo docker import -\n\n' +
                         'to get this imported into docker.', code='31')
                cfg['build']['report'] += ('\nDeposited bzip2 of exported' +
                                          ' container into ' + bzfile)
                cfg['build']['report'] += ('\nRun:\n\nbunzip2 -c ' + bzfile +
                                          ' | sudo docker import -\n\n' +
                                          'to get this imported into docker.')
            if save:
                bzfile = (cfg['host']['resources_dir'] +
                          '/' + repository_tar + 'save.tar.bz2')
                self.log('\nDepositing bzip2 of exported container into ' +
                         bzfile)
                if self.send(docker_executable + ' save ' +
                             cfg['container']['container_id'] +
                             ' | bzip2 - > ' + bzfile,
                             expect=[expect, 'assword'],
                             timeout=99999, child=child) == 1:
                    self.send(password, expect=expect, child=child)
                self.log('\nDeposited bzip2 of exported container into ' +
                         bzfile, code='31')
                self.log('\nRun:\n\nbunzip2 -c ' + bzfile +
                         ' | sudo docker import -\n\n' + 
                         'to get this imported into docker.',
                         code='31')
                cfg['build']['report'] += ('\nDeposited bzip2 of exported ' + 
                                          'container into ' + bzfile)
                cfg['build']['report'] += ('\nRun:\n\nbunzip2 -c ' + bzfile +
                                           ' | sudo docker import -\n\n' + 
                                           'to get this imported into docker.')
        if cfg['repository']['push'] == True:
            # Pass the child explicitly as it's the host child.
            self.push_repository(repository,
                                 docker_executable=docker_executable,
                                 expect=expect,
                                 child=child)
            cfg['build']['report'] = (cfg['build']['report'] +
                                      '\nPushed repository: ' + repository)


    def get_config(self,
                   module_id,
                   option,
                   default=None,
                   boolean=False,
                   forcedefault=False,
                   forcenone=False):
        """Gets a specific config from the config files,
        allowing for a default.
        Handles booleans vs strings appropriately.
    
        module_id    - module id this relates to,
                       eg com.mycorp.mymodule.mymodule
        option       - config item to set
        default      - default value if not set in files
        boolean      - whether this is a boolean value or not (default False)
        forcedefault - if set to true, allows you to override any value
                       already set (default False)
        forcenone    - if set to true, allows you to set the value to None
                       (default False)
        """
        if module_id not in self.cfg.keys():
            self.cfg[module_id] = {}
        if not cfg['config_parser'].has_section(module_id):
            self.cfg['config_parser'].add_section(module_id)
        if not forcedefault and self.cfg['config_parser'].has_option(module_id, option):
            if boolean:
                self.cfg[module_id][option] = self.cfg['config_parser'].getboolean(module_id, option)
            else:
                self.cfg[module_id][option] = self.cfg['config_parser'].get(module_id, option)
        else:
            if default == None and forcenone != True:
                self.fail('Config item: ' + option + ':\nin module:\n[' + module_id + ']\nmust be set!\n\nOften this is a deliberate requirement to place in your host-specific /path/to/shutit/configs/$(hostname)_$(whoami).cnf file.')
            self.cfg[module_id][option] = default


    def record_config(self):
        """ Put the config in a file in the container.
        """
        self.send_file(self.cfg['build']['build_db_dir'] +
                       '/' + self.cfg['build']['build_id'] +
                       '/' + self.cfg['build']['build_id'] +
                       '.cfg', util.print_config(self.cfg))

    def get_emailer(self, cfg_section):
        """Sends an email using the mailer
        """
        import emailer
        return emailer.emailer(cfg_section, self)
        


def init():
    """Initialize the shutit object. Called when imported.
    """
    global pexpect_children
    global shutit_modules
    global shutit_main_dir
    global cfg
    global cwd
    global shutit_command_history
    global shutit_map

    pexpect_children       = {}
    shutit_map             = {}
    shutit_modules         = set()
    shutit_command_history = []
    # Store the root directory of this application.
    # http://stackoverflow.com/questions/5137497
    shutit_main_dir = os.path.abspath(os.path.dirname(__file__))
    cwd = os.getcwd()
    cfg = {}
    cfg['action']               = {}
    cfg['build']                = {}
    cfg['build']['interactive'] = 1 # Default to true until we know otherwise
    cfg['build']['build_log']   = None
    cfg['build']['report']      = ''
    cfg['build']['debug']       = False
    cfg['container']            = {}
    cfg['host']                 = {}
    cfg['repository']           = {}
    cfg['expect_prompts']       = {}
    cfg['users']                = {}
    cfg['dockerfile']           = {}

    # If no LOGNAME available,
    cfg['host']['username'] = os.environ.get('LOGNAME', '')
    if cfg['host']['username'] == '':
        if os.getlogin() != '':
            cfg['host']['username'] = os.getlogin()
        if cfg['host']['username'] == '':
            shutit_global.shutit.fail('LOGNAME not set in the environment, ' +
                                      'and login unavailable in puthon; ' +
                                      'please set to your username.')
    cfg['host']['real_user'] = os.environ.get('SUDO_USER',
                                              cfg['host']['username'])
    cfg['build']['build_id'] = (socket.gethostname() + '_' +
                                cfg['host']['real_user'] + '_' +
                                str(time.time()) + '.' +
                                str(datetime.datetime.now().microsecond))

    return ShutIt(
        pexpect_children=pexpect_children,
        shutit_modules=shutit_modules,
        shutit_main_dir=shutit_main_dir,
        cfg=cfg,
        cwd=cwd,
        shutit_command_history=shutit_command_history,
        shutit_map=shutit_map
    )

shutit = init()

