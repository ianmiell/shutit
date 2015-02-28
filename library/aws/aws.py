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

class aws(ShutItModule):

	def is_installed(self,shutit):
		return False


	def build(self,shutit):
		shutit.install('wget')
		shutit.install('zip')
		shutit.install('python-pip')
		shutit.install('openssh-client') # required to log into ec2 instances
		shutit.install('groff') # required for help
		shutit.install('less') # required for help
		shutit.install('vim') # not required just handy
		# http://docs.aws.amazon.com/cli/latest/userguide/installing.html
		shutit.send('wget --no-check-certificate https://s3.amazonaws.com/aws-cli/awscli-bundle.zip')
		shutit.send('unzip awscli-bundle.zip')
		shutit.send('./awscli-bundle/install -i /usr/local/aws -b /usr/local/bin/aws')
		shutit.send('complete -C aws_completer aws')
		shutit.send('aws configure',expect="Access Key ID")
		shutit.send(shutit.cfg[self.module_id]['access_key_id'],expect="Secret Access Key")
		shutit.send(shutit.cfg[self.module_id]['secret_access_key'],expect="Default region name")
		shutit.send(shutit.cfg[self.module_id]['region'],expect="Default output format")
		shutit.send(shutit.cfg[self.module_id]['output'])
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id, 'region', '')
		shutit.get_config(self.module_id, 'output', '')
		shutit.get_config(self.module_id, 'access_key_id', '')
		shutit.get_config(self.module_id, 'secret_access_key', '')
		return True

def module():
	return aws(
		'shutit.tk.aws.aws', 0.00123,
		description='aws client setup',
		depends=['shutit.tk.setup']
	)

