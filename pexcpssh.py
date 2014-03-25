#Copyright (C) 2014 OpenBet Limited
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


# http://stackoverflow.com/questions/373639/running-interactive-commands-in-paramiko
# http://stackoverflow.com/questions/13041732/ssh-password-through-python-subprocess
# http://stackoverflow.com/questions/1939107/python-libraries-for-ssh-handling
# http://stackoverflow.com/questions/11272536/how-to-obtain-pseudo-terminal-master-file-descriptor-from-inside-ssh-session
# http://stackoverflow.com/questions/4022600/python-pty-fork-how-does-it-work

import os
import pty

def ssh_start(host, port, user):

	try:
		(child_pid, fd) = pty.fork()
	except OSError as e:
		print str(e)

	# NOTE - unlike OS fork, in pty fork we MUST read from the fd variable
	#        somewhere in the parent process: if we don't - child process will
	#        never be spawned

	if child_pid == 0:
		# Need to flush sys.stdout and files here

		# The first of these arguments is the name of the new program
		os.execlp('ssh', 'pexcpssh',
				'-p', str(port),
				'-o', 'UserKnownHostsFile=/dev/null', '-o', 'StrictHostKeyChecking=no',
				user + '@' + host)
	else:
		return fd
