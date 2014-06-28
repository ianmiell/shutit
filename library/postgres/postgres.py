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

class postgres(ShutItModule):

	def is_installed(self,shutit):
		return shutit.file_exists('/root/start_postgres.sh')

	def build(self,shutit):
		shutit.install('postgresql')
		shutit.add_line_to_file('# postgres','/root/start_postgres.sh')
		shutit.add_line_to_file("echo Setting shmmax for postgres",'/root/start_postgres.sh')
		shutit.add_line_to_file('sysctl -w kernel.shmmax=268435456','/root/start_postgres.sh',force=True)
		shutit.add_line_to_file('service postgresql start','/root/start_postgres.sh',force=True)
		shutit.send_and_expect("""cat > /root/stop_postgres.sh <<< 'service postgresql stop'""")
		shutit.send_and_expect('chmod +x /root/start_postgres.sh')
		shutit.send_and_expect('chmod +x /root/stop_postgres.sh')
		return True

	def start(self,shutit):
		shutit.send_and_expect('/root/start_postgres.sh',check_exit=False)
		return True

	def stop(self,shutit):
		shutit.send_and_expect('/root/stop_postgres.sh',check_exit=False)
		return True

def module():
	return postgres(
		'shutit.tk.postgres.postgres', 0.320,
		description='installs postgres and handles shm settings changes',
		depends=['shutit.tk.setup']
	)

