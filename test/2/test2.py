#Copyright (C) 2014 OpenBet Limited
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from shutit_module import ShutItModule

class test2(ShutItModule):

	def is_installed(self, shutit):
		return False

	def build(self, shutit):
		shutit.send_and_expect('touch /tmp/container_touched')
		shutit.add_line_to_file('#test line', '/tmp/newfile')
		shutit.add_line_to_file('#test line', '/tmp/newfile')
		shutit.send_and_expect('useradd testuser')
		shutit.send_and_expect('su - testuser', '\\$ ', check_exit=False)
		shutit.send_and_expect('exit', check_exit=False)
		return True

def module():
	return test2('shutit.tk.test.test2',2, depends=['shutit.tk.setup'])

