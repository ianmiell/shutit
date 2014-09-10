"""ShutIt module. See http://shutit.tk
"""

import glob

from shutit_module import ShutItModule

class ianmiellaws(ShutItModule):

    def is_installed(self,shutit):
        return False

    def build(self,shutit):
        shutit.send_host_dir('/root','context/pems')
        shutit.send('chmod 400 /root/*.pem')
        return True

    def check_ready(self, shutit):
        if len(glob.glob('context/pems/*pem')) == 0:
            shutit.log('\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!' + 
                '\nNo pems in context/pems/*pem' + 
                '\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!',
                force_stdout=True)
            return False
        return True


def module():
    return ianmiellaws(
        'tk.ianandsarah.ianmiellaws.ianmiellaws', 1159697827.00,
        description='Sets up pems in aws',
        maintainer='ian.miell@gmail.com',
        depends=['shutit.tk.setup','shutit.tk.aws.aws']
    )

