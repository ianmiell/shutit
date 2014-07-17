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

from shutit_module import ShutItModule

class ssh_server(ShutItModule):

    def is_installed(self, shutit):
        shutit.file_exists('/root/start_ssh_server.sh')

    def build(self, shutit):
        shutit.install('openssh-server')
        shutit.send('mkdir -p /var/run/sshd')
        shutit.send('chmod 700 /var/run/sshd')
        # Set up root bashrcs once
        # Root bash files seem to be inconsistent, so this the canonical one...
        shutit.add_line_to_file('export HOME=/root', '/root/.bashrc')
        # ... and the others point to it.
        shutit.add_line_to_file('. /root/.bashrc', '/root/.bash_profile.sh')
        shutit.add_line_to_file('. /root/.bashrc', '/.bashrc')
        shutit.add_line_to_file('. /root/.bashrc', '/.bash_profile')
        shutit.add_line_to_file('# sshd', '/root/start_ssh_server.sh')
        ## To get sshd to work, we need to create a privilege separation directory.
        ## see http://docs.docker.io/en/latest/examples/running_ssh_service/
        shutit.add_line_to_file('mkdir -p /var/run/sshd', '/root/start_ssh_server.sh')
        shutit.add_line_to_file('chmod 700 /var/run/sshd', '/root/start_ssh_server.sh')
        shutit.add_line_to_file('start-stop-daemon --start --quiet --oknodo --pidfile /var/run/sshd.pid --exec /usr/sbin/sshd', '/root/start_ssh_server.sh')
        shutit.add_line_to_file('start-stop-daemon --stop --quiet --oknodo --pidfile /var/run/sshd.pid', '/root/stop_ssh_server.sh')
        shutit.send('chmod +x /root/start_ssh_server.sh')
        shutit.send('chmod +x /root/stop_ssh_server.sh')
        return True

    def start(self, shutit):
        shutit.send('/root/start_ssh_server.sh', check_exit=False)
        return True

    def stop(self, shutit):
        shutit.send('/root/stop_ssh_server.sh', check_exit=False)
        return True


def module():
    return ssh_server(
        'shutit.tk.ssh_server.ssh_server', 0.321,
        description='ssh server',
        depends=['shutit.tk.setup']
    )

