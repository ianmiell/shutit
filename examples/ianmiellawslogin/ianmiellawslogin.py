"""ShutIt module. See http://shutit.tk
"""

import json

from shutit_module import ShutItModule

class ianmiellawslogin(ShutItModule):

    def build(self,shutit):
        # Have we got any up?
        shutit.send('aws ec2 describe-instances --filter Name=instance-state-name,Values=running')
        json_dict = json.loads(shutit.get_output())
        if len(json_dict['Reservations']) != 0:
            # Terminate instance running.
            shutit.cfg[self.module_id]['instance_id'] = json_dict['Reservations'][0]['Instances'][0]['InstanceId']
            shutit.send('aws ec2 terminate-instances --instance-ids ' + shutit.cfg[self.module_id]['instance_id'])
        # TODO - check with describe rather than pause
        shutit.send('sleep 30')
        shutit.send('aws ec2 run-instances --image-id ' + shutit.cfg[self.module_id]['image_id'] + ' --instance-type ' + shutit.cfg[self.module_id]['instance_type'] + ' --key-name imiell_aws_eu --security-groups ' + shutit.cfg[self.module_id]['security_groups'])
        json_dict = json.loads(shutit.get_output())
        shutit.cfg[self.module_id]['instance_id'] = json_dict['Instances'][0]['InstanceId']
        # TODO - check with describe rather than pause
        shutit.send('sleep 500')
        # Get the ip address
        shutit.send('aws ec2 describe-instances --filter Name=instance-state-name,Values=running')
        json_dict = json.loads(shutit.get_output())
        shutit.cfg[self.module_id]['ec2_ip'] = json_dict['Reservations'][0]['Instances'][0]['PublicIpAddress']

        shutit.login(command='ssh -i imiell_aws_eu.pem ec2-user@' + shutit.cfg[self.module_id]['ec2_ip'])
        shutit.send('sudo yum install -y docker')
        shutit.send('sudo service docker start')
        # Exit back to the "real container"
        shutit.logout()
        return True

    def get_config(self,shutit):
        shutit.get_config(self.module_id, 'image_id', 'ami-672ce210')
        shutit.get_config(self.module_id, 'instance_type', 't1.micro')
        shutit.get_config(self.module_id, 'security_groups', 'launch-wizard-1')
        if shutit.cfg[self.module_id]['image_id'] == '':
            return False
        return True

    def finalize(self, shutit):
        shutit.send('aws ec2 terminate-instances --instance-ids ' + shutit.cfg[self.module_id]['instance_id'])
        return True

    def is_installed(self,shutit):
        return False

def module():
    return ianmiellawslogin(
        'shutit.tk.ianmiellawslogin.ianmiellawslogin', 0.013235,
        description='Creates AMI',
        maintainer='ian.miell@gmail.com',
        depends=['shutit.tk.setup','tk.ianandsarah.ianmiellaws.ianmiellaws']
    )

