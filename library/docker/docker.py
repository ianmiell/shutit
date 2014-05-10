#Copyright (C) 2014 OpenBet Limited
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
import util

class docker(ShutItModule):

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
	def check_ready(self,shutit):
		config_dict = shutit.cfg
		return True

	# is_installed
	#
	# Determines whether the module has been built in this container
	# already.
	#
	# Should return True if it is certain it's there, else False.
	def is_installed(self,shutit):
		config_dict = shutit.cfg
		return False

	# build
	#
	# Run the build part of the module, which should ensure the module
	# has been set up.
	# If is_installed determines that the module is already there,
	# this is not run.
	#
	# Should return True if it has succeeded in building, else False.
	def build(self,shutit):
		config_dict = shutit.cfg
		container_child = util.get_pexpect_child('container_child') # Let's get the container child object from pexpect.
		root_prompt_expect = config_dict['expect_prompts']['root_prompt'] # Set the string we expect to see once commands are done.
		util.send_and_expect(container_child,'echo deb http://archive.ubuntu.com/ubuntu precise universe > /etc/apt/sources.list.d/universe.list',root_prompt_expect)
		util.send_and_expect(container_child,'apt-get update -qq',root_prompt_expect)
		util.install(container_child,config_dict,'iptables',root_prompt_expect)
		util.install(container_child,config_dict,'ca-certificates',root_prompt_expect)
		util.install(container_child,config_dict,'lxc',root_prompt_expect)
		util.install(container_child,config_dict,'curl',root_prompt_expect)
		util.install(container_child,config_dict,'aufs-tools',root_prompt_expect)
		util.send_and_expect(container_child,'pushd /usr/bin',root_prompt_expect)
		util.send_and_expect(container_child,'curl https://get.docker.io/builds/Linux/x86_64/docker-latest > docker',root_prompt_expect)
		util.send_and_expect(container_child,'chmod +x docker',root_prompt_expect)
		wrapdocker = """cat > /usr/bin/wrapdocker << 'END'
#!/bin/bash

# First, make sure that cgroups are mounted correctly.
CGROUP=/sys/fs/cgroup

[ -d $CGROUP ] ||
mkdir $CGROUP

mountpoint -q $CGROUP ||
mount -n -t tmpfs -o uid=0,gid=0,mode=0755 cgroup $CGROUP || {
echo "Could not make a tmpfs mount. Did you use -privileged?"
exit 1
}

if [ -d /sys/kernel/security ] && ! mountpoint -q /sys/kernel/security
then
mount -t securityfs none /sys/kernel/security || {
        echo "Could not mount /sys/kernel/security."
        echo "AppArmor detection and -privileged mode might break."
    }
fi

# Mount the cgroup hierarchies exactly as they are in the parent system.
for SUBSYS in $(cut -d: -f2 /proc/1/cgroup)
do
        [ -d $CGROUP/$SUBSYS ] || mkdir $CGROUP/$SUBSYS
        mountpoint -q $CGROUP/$SUBSYS ||
                mount -n -t cgroup -o $SUBSYS cgroup $CGROUP/$SUBSYS

        # The two following sections address a bug which manifests itself
        # by a cryptic "lxc-start: no ns_cgroup option specified" when
        # trying to start containers withina container.
        # The bug seems to appear when the cgroup hierarchies are not
        # mounted on the exact same directories in the host, and in the
        # container.

        # Named, control-less cgroups are mounted with "-o name=foo"
        # (and appear as such under /proc/<pid>/cgroup) but are usually
        # mounted on a directory named "foo" (without the "name=" prefix).
        # Systemd and OpenRC (and possibly others) both create such a
        # cgroup. To avoid the aforementioned bug, we symlink "foo" to
        # "name=foo". This shouldn't have any adverse effect.
        echo $SUBSYS | grep -q ^name= && {
                NAME=$(echo $SUBSYS | sed s/^name=//)
                ln -s $SUBSYS $CGROUP/$NAME
        }

        # Likewise, on at least one system, it has been reported that
        # systemd would mount the CPU and CPU accounting controllers
        # (respectively "cpu" and "cpuacct") with "-o cpuacct,cpu"
        # but on a directory called "cpu,cpuacct" (note the inversion
        # in the order of the groups). This tries to work around it.
        [ $SUBSYS = cpuacct,cpu ] && ln -s $SUBSYS $CGROUP/cpu,cpuacct
done

# Note: as I write those lines, the LXC userland tools cannot setup
# a "sub-container" properly if the "devices" cgroup is not in its
# own hierarchy. Let's detect this and issue a warning.
grep -q :devices: /proc/1/cgroup ||
echo "WARNING: the 'devices' cgroup should be in its own hierarchy."
grep -qw devices /proc/1/cgroup ||
echo "WARNING: it looks like the 'devices' cgroup is not mounted."

# Now, close extraneous file descriptors.
pushd /proc/self/fd >/dev/null
for FD in *
do
case "$FD" in
# Keep stdin/stdout/stderr
[012])
;;
# Nuke everything else
*)
eval exec "$FD>&-"
;;
esac
done
popd >/dev/null


# If a pidfile is still around (for example after a container restart),
# delete it so that docker can start.
rm -rf /var/run/docker.pid

# If we were given a PORT environment variable, start as a simple daemon;
# otherwise, spawn a shell as well
if [ "$PORT" ]
then
exec docker -d -H 0.0.0.0:$PORT
else

docker -d &
exec bash
fi
END"""
		util.send_and_expect(container_child,wrapdocker,root_prompt_expect)
		util.send_and_expect(container_child,'chmod +x /usr/bin/wrapdocker',root_prompt_expect)
		util.send_and_expect(container_child,'popd',root_prompt_expect)
		return True

	# start
	#
	# Run when module should be installed (is_installed() or configured to build is true)
	# Run after repo work.
	def start(self,shutit):
		config_dict = shutit.cfg
		return True

	# stop
	#
	# Run when module should be stopped.
	# Run before repo work, and before finalize is called.
	def stop(self,shutit):
		config_dict = shutit.cfg
		return True

	# cleanup
	#
	# Cleanup the module, ie clear up stuff not needed for the rest of the build, eg tar files removed, apt-get cleans.
	# Should return True if all is OK, else False.
	# Note that this is only run if the build phase was actually run.
	def cleanup(self,shutit):
		config_dict = shutit.cfg
		return True

	# finalize
	#
	# Finalize the module, ie do things that need doing before we exit.
	def finalize(self,shutit):
		config_dict = shutit.cfg
		return True

	# remove
	# 
	# Remove the module, which should ensure the module has been deleted 
	# from the system.
	def remove(self,shutit):
		config_dict = shutit.cfg
		return True

	# test
	#
	# Test the module is OK.
	# Should return True if all is OK, else False.
	# This is run regardless of whether the module is installed or not.
	def test(self,shutit):
		config_dict = shutit.cfg
		return True

	# get_config
	#
	# each object can handle config here
	def get_config(self,shutit):
		config_dict = shutit.cfg
		return True


# docker(string,float)
# string : Any string you believe to identify this module uniquely, 
#          eg com.my_corp.my_module_dir.my_module
# float:   Float value for ordering module builds, must be > 0.0
if not util.module_exists('shutit.tk.docker.docker'):
	obj = docker('shutit.tk.docker.docker',1000.00)
	obj.add_dependency('shutit.tk.setup')
	util.get_shutit_modules().add(obj)
	ShutItModule.register(docker)

