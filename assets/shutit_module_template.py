"""ShutIt module. See http://shutit.tk
"""
#Copyright (C) 2014 OpenBet Limited
#
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is furnished
#to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
#FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
#COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
#IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from shutit_module import ShutItModule
import os

class template(ShutItModule):
    # Determines whether the module has been built in this container
    # already.
    #
    # Should return True if it is certain it's there, else False.
    def is_installed(self,shutit):
        return shutit.file_exists('/tmp/container_touched.sh') and shutit.file_exists('/tmp/README.md')

    # Run the build part of the module, which should ensure the module
    # has been set up.
    # If is_installed determines that the module is already there,
    # this is not run.
    #
    # Should return True if it has succeeded in building, else False.
    def build(self,shutit):
        # Line number 42 should be the next one (so bash scripts can be inserted properly)

        # DELETE THIS SECTION WHEN UNDERSTOOD - BEGIN
        shutit.send_and_expect('touch /tmp/deleteme')
        shutit.send_and_expect('touch /tmp/container_touched.sh')
        shutit.add_line_to_file('#This line should only appear once in the file','/tmp/container_touched.sh')
        shutit.add_line_to_file('#This line should only appear once in the file','/tmp/container_touched.sh')
        # We add the match_regexp because the string has a quote in it.
        shutit.add_line_to_file('echo "hello container"','/tmp/container_touched.sh',match_regexp='echo .hello container.')
        shutit.add_line_to_file('sleep 10000000 &','/tmp/container_touched.sh')
        shutit.send_and_expect('chmod +x /tmp/container_touched.sh')
        # Make sure passwd is installed
        shutit.install('passwd')
        shutit.install('sudo')
        # Install mlocate
        shutit.install('mlocate')
        # Example of distro-specific password update
        # record_command=False prevents the password being output at the end on debug. However, if it matches a password stored in config, 
        # it will automatically redact it.
        if shutit.cfg['container']['install_type'] == 'apt': # apt-based password update
            # "check_exit" checks the exit code of the command you are running.
            # We can't check the exit code as the command will not return when we see 'Retype new' on the terminal.
            shutit.send_and_expect('passwd','Enter new',check_exit=False)
            # echo=False ensured it's not output on to the running terminal
            shutit.send_and_expect(shutit.cfg['container']['password'],'Retype new',check_exit=False,echo=False)
            shutit.send_and_expect(shutit.cfg['container']['password'],echo=False)
        elif shutit.cfg['container']['install_type'] == 'yum': # yum-based password update
            # Check_exit checks the exit code of the command you are running.
            # We can't check the exit code as the command will not return when we see 'ew password' on the terminal.
            shutit.send_and_expect('passwd','ew password',check_exit=False)
            shutit.send_and_expect(shutit.cfg['container']['password'],'ew password',check_exit=False,echo=False)
            shutit.send_and_expect(shutit.cfg['container']['password'],echo=False)
        # You can put multiple items you might expect in a list and handle accordingly:
        res = shutit.send_and_expect('sudo ls',['assword',shutit.cfg['expect_prompts']['root_prompt']],check_exit=False)
        if res == 0:
            shutit.send_and_expect(shutit.cfg['container']['password'],echo=False)
        elif res == 1:
            pass
        else:
            # We fail out on this case, as it's not expected.
            shutit.fail('res: ' + str(res) + ' not handled')
        # example of resource use (simple file, copy README.md into the container)
        shutit.send_file('/tmp/copiedfile',file.read(file(os.path.abspath(os.path.dirname(__file__)) + '/README.md')))
        # example of bespoke config use
        # Example of login/logout handling
        # When logging in, use the base prompt to attempt to match all prompts
        # Note that we don't check_exit, because the exit value won't be meaningful.
        shutit.send_and_expect('su',shutit.cfg['expect_prompts']['base_prompt'],check_exit=False)
        # Then call setup_prompt to set and get the bespoke prompt for the session
        shutit.setup_prompt('test_tmp_prompt')
        shutit.set_default_expect(shutit.cfg['expect_prompts']['test_tmp_prompt'])
        shutit.send_and_expect('echo "a command and some output"')
        # Make sure we're expecting the right thing after we exit this subshell
        shutit.set_default_expect(shutit.cfg['expect_prompts']['root_prompt'])
        shutit.send_and_expect('exit')

        # Example of temporary debugging
        orig_debug_val = shutit.cfg['build']['debug']
        shutit.cfg['build']['debug'] = True
        shutit.send_and_expect('echo "Command to look at debug output"')
        shutit.send_and_expect('echo "Another command to look at debug output"')
        shutit.cfg['build']['debug'] = orig_debug_val
        shutit.pause_point("""
                The doubling up of text is expected; try and ignore it :)
                When you're done, "Ctrl" and "]" at the same time.
                You should then see your inputted lines in the output.
                Add them to the module file before the pause_point line as 
                "shutit.send_and_expect" lines (copy and paste), following
                the examples above this one in the file.
                Then "Ctrl" and "]" at the same time again to return to the script.
                Eventually you'll get a docker export to a tar file in your 
                configured resources folder.""")
        # DELETE THIS SECTION WHEN UNDERSTOOD - DONE
        return True

    # get_config
    #
    # each object can handle config here
    # OPTIONAL part of lifecycle - uncomment to include
    def get_config(self,shutit):
        shutit.get_config(self.mod_id,'test_config','some_default_value')
        return True

    # check_ready
    # 
    # Check whether we are ready to build this module.
    # 
    # This is called before the build, to ensure modules have 
    # their requirements in place (eg files required to be mounted 
    # in /resources). Checking whether the build will happen (and
    # therefore whether the check should take place) will be 
    # determined by the framework.
    # 
    # Should return True if it ready, else False.
    # OPTIONAL part of lifecycle - uncomment to include
    #def check_ready(self,shutit):
    #    """This help string is printed if we're not ready.
    #    Advice to failure should be placed here.
    #    """
    #    return shutit.file_exists('/resources/README.md')

    # start
    #
    # Run when module should be installed (is_installed() or configured to build is true)
    # Run after repo work.
    # OPTIONAL part of lifecycle - uncomment to include
    #def start(self,shutit):
    #    # example of starting something
    #    shutit.send_and_expect('cat /tmp/container_touched.sh')
    #    shutit.send_and_expect('sh /tmp/container_touched.sh')
    #    return True

    # stop
    #
    # Run when module should be stopped.
    # Run before repo work, and before finalize is called.
    # OPTIONAL part of lifecycle - uncomment to include
    #def stop(self,shutit):
    #    # example of stopping something
    #    shutit.send_and_expect("""ps -ef | grep -v grep | grep container_touched.sh | awk '{print $1}' | sed 's/\([0-9][0-9]*\)/kill \\1/' | sh""")
    #    return True

    # finalize
    #
    # Finalize the module, ie do things that need doing before we exit.
    # OPTIONAL part of lifecycle - uncomment to include
    #def finalize(self,shutit):
    #    # Right at the end we want to ensure the locate db is up to date.
    #    shutit.send_and_expect('updatedb')
    #    return True

    # remove
    # 
    # Remove the module, which should ensure the module has been deleted 
    # from the system.
    # OPTIONAL part of lifecycle - uncomment to include
    #def remove(self,shutit):
    #    shutit.send_and_expect('rm -f /tmp/container_touched.sh')
    #    shutit.send_and_expect('rm -f /tmp/README.md')
    #    # TODO: remove the installed apps DEPENDS on install tracking being available.
    #    return True

    # test
    #
    # Test the module is OK.
    # Should return True if all is OK, else False.
    # This is run regardless of whether the module is installed or not.
    # OPTIONAL part of lifecycle - uncomment to include
    #def test(self,shutit):
    #    return shutit.package_installed('mlocate') and shutit.package_installed('passwd')

# template(string,float)
# string : Any string you believe to identify this module uniquely, 
#          eg com.my_corp.my_module_dir.my_module
# float:   Float value for ordering module builds, must be > 0.0
def module():
    return template(
        GLOBALLY_UNIQUE_STRING, FLOAT,
        description='',
        depends=['shutit.tk.setup']
    )

