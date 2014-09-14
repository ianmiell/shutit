"""ShutIt module. See http://shutit.tk
"""

import glob

from shutit_module import ShutItModule

class aws_example(ShutItModule):

    def is_installed(self,shutit):
        return False

    def build(self,shutit):
        shutit.send_host_dir('/root','context/pems')
        shutit.send('chmod 400 /root/' + shutit.cfg[self.module_id]['pem_name'] + '.pem')
        return True

    def get_config(self, shutit):
        shutit.get_config(self.module_id,'pem_name')
        return True


def module():
    return aws_example(
        'shutit.tk.aws_example.aws_example', 0.011,
        description='Sets up pems in aws',
        maintainer='ian.miell@gmail.com',
        depends=['shutit.tk.setup','shutit.tk.aws.aws']
    )

