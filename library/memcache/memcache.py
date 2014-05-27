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

class memcache(ShutItModule):

	def is_installed(self,shutit):
		return shutit.file_exists('/root/start_memcache.sh')

	def build(self,shutit):
		shutit.install('memcached')
		shutit.install('libmemcached-dev')
		shutit.install('libmemcached-tools')
		shutit.send_and_expect("""cat > /root/start_memcache.sh <<< 'service memcached start'""")
		shutit.send_and_expect("""cat > /root/stop_memcache.sh <<< 'service memcached stop'""")
		shutit.send_and_expect('chmod +x /root/start_memcache.sh')
		shutit.send_and_expect('chmod +x /root/stop_memcache.sh')
		return True

def module():
	return memcache(
		'shutit.tk.memcache.memcache', 0.317,
		description='memcache',
		depends=['shutit.tk.setup']
	)

