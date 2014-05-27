#Copyright (C) 2014 OpenBet Limited
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from shutit_module import ShutItModule

class prompt_command(ShutItModule):

	def is_installed(self,shutit):
		return False

	def build(self,shutit):
		cfg = shutit.cfg
		# Breaks unless we set the PROMPT_COMMAND manually on a login
		shutit.send_and_expect("""cat >> /root/.bashrc << END
PROMPT_COMMAND='echo -ne "a"'
END""")
		shutit.send_and_expect('su',expect=cfg['expect_prompts']['base_prompt'],check_exit=False)
		shutit.setup_prompt('test_tmp_prompt')
		shutit.send_and_expect('echo abc',expect=cfg['expect_prompts']['test_tmp_prompt'])
		shutit.send_and_expect('exit', cfg['expect_prompts']['root_prompt'])
		return True

def module():
	return prompt_command('shutit.tk.prompt_command',1000.00,depends=['shutit.tk.setup'])

