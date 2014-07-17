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

class docker(ShutItModule):

    def build(self, shutit):
        shutit.send('echo deb http://archive.ubuntu.com/ubuntu precise universe > /etc/apt/sources.list.d/universe.list')
        shutit.send('apt-get update -qq')
        shutit.install('iptables')
        shutit.install('ca-certificates')
        shutit.install('lxc')
        shutit.install('curl')
        shutit.install('aufs-tools')
        shutit.send('pushd /usr/bin')
        shutit.send('curl https://get.docker.io/builds/Linux/x86_64/docker-latest > docker')
        shutit.send('chmod +x docker')
        wrapdocker = """cat > /usr/bin/wrapdocker << 'END'
#!/bin/bash

# First, make sure that cgroups are mounted correctly.
CGROUP=/sys/fs/cgroup

[ -d $CGROUP ] ||
mkdir $CGROUP

mountpoint -q $CGROUP ||
mount -n -t tmpfs -o uid=0, gid=0, mode=0755 cgroup $CGROUP || {
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
        # (respectively "cpu" and "cpuacct") with "-o cpuacct, cpu"
        # but on a directory called "cpu, cpuacct" (note the inversion
        # in the order of the groups). This tries to work around it.
        [ $SUBSYS = cpuacct, cpu ] && ln -s $SUBSYS $CGROUP/cpu, cpuacct
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
        shutit.send(wrapdocker)
        shutit.send('chmod +x /usr/bin/wrapdocker')
        start_docker = """cat > /root/start_docker.sh << 'END'
#!/bin/bash
/root/start_ssh_server.sh
docker -d &
/usr/bin/wrapdocker
echo "SSH Server up"
echo "Docker daemon running"
END"""
        shutit.send(start_docker)
        shutit.send('chmod +x /root/start_docker.sh')
        shutit.send('popd')
        return True

    def is_installed(self, shutit):
        return False

    def check_ready(self, shutit):
        # Only apt-based systems are supported support atm
        return shutit.cfg['container']['install_type'] == 'apt'


def module():
    return docker(
        'shutit.tk.docker.docker', 0.396,
        description='docker server (communicates with host\'s docker daemon)',
        depends=['shutit.tk.setup', 'shutit.tk.ssh_server.ssh_server']
    )

