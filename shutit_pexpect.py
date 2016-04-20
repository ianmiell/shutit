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
"""Represents and manages a pexpect object for ShutIt's purposes.
"""

import pexpect


class ShutItPexpectChild(object):

	def __init__(self,
	             shutit,
	             pexpect_child_id):
		"""
		"""
		self.check_exit             = True
		self.expect                 = shutit.cfg['expect_prompts']['base_prompt']
		self.pexpect_child          = None
		self.pexpect_child_id       = pexpect_child_id
		TODO: move login stack into here and login_stack_append
		TODO: update login function
		self.login_stack            = []


	def login_stack_append(self,
	                       r_id,
	                       expect=None,
	                       new_user=''):
		child = self.pexpect_child
        self.login_stack.append(r_id)


    def expect(self,
	           expect,
	           timeout=None):
    	"""Handle child expects, with EOF and TIMEOUT handled
		"""
        if type(expect) == str:
            expect = [expect]
        return self.pexpect_child.expect(expect + [pexpect.TIMEOUT] + [pexpect.EOF], timeout=timeout)




	def spawn_child(self,
	                command,
	                args=[],
                    timeout=30,
                    maxread=2000,
	                searchwindowsize=None,
                    logfile=None,
                    cwd=None,
                    env=None,
                    ignore_sighup=False,
                    echo=True,
                    preexec_fn=None,
                    encoding=None,
                    codec_errors='strict',
                    dimensions=None,
                    delaybeforesend=0):
		"""spawn a child, and manage the delaybefore send setting to 0"""
		if self.pexpect_child != None:
			shutit_util.handle_exit(exit_code=1,msg='Cannot overwrite pexpect_child in object')
		self.pexpect_child = pexpect.spawn(command,
		                     args=args,
		                     timeout=timeout,
			                 maxread=maxread,
		                     searchwindowsize=searchwindowsize,
		                     logfile=logfile,
		                     cwd=cwd,
		                     env=env,
		                     ignore_sighup=ignore_sighup,
		                     echo=echo,
		                     preexec_fn=preexec_fn,
		                     encoding=encoding,
		                     codec_errors=codec_errors,
		                     dimensions=dimensions)
		self.pexpect_child.delaybeforesend=delaybeforesend
		shutit.pexpect_children.append({self.pexpect_child_id:self.pexpect_child})
		return True


	def send(self, string):
		self.pexpect_child.send(string)
	def sendline(self, string):
		self.pexpect_child.sendline(string)

	#DONE: update references to check exit etc
	#DONE: replace get_default_child/set_default_child and expect with get_current_session or similar - shutit.current_shutit_pexpect_child
	#DONE: replace set default expect with 'set default pexpect child/expect'
	TODO: replace shutit.login and logout and manage that in here
	TODO: check shutit_pexpect_children references make sense (ie expect correct object)
	TODO: replace shutit.child_expect
	TODO: replace child.send and child.sendline
	TODO: replace refernces to 'host_child' and 'target_child'
	TODO: replace shutit_global.pexpect_children / self.pexpect_children
	TODO: replace get_pexpect_child
	TODO: child.logfile_send?
	TODO: child.interact
	TODO: child.before / child.after
	TODO: child.expect
	TODO: setup_host_child
	TODO: setup_target_child
	TODO: child.close()
	TODO: child.exitstatus
	TODO: self.start_container
	TODO: _default_child, _default_expect
	
	FINALLY: any mention of child!


	def spawn_child
		TODO: move function from util into here, or make args into init
		      replace spawns in code



