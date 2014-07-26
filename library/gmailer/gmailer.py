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

class gmailer(ShutItModule):

    def is_installed(self,shutit):
        return False

    def build(self,shutit):
        shutit.install('mailutils')
        shutit.install('ssmtp')
        shutit.send("""cat > /etc/ssmtp/ssmtp.conf << END
root=""" + shutit.cfg[self.module_id]['email'] + """
AuthUser=""" + shutit.cfg[self.module_id]['email'] + """
AuthPass=""" + shutit.cfg[self.module_id]['password'] + """
mailhub=smtp.gmail.com:587
rewriteDomain=
hostname=smtp.gmail.com:587
UseSTARTTLS=YES
UseTLS=YES
AuthMethod=LOGIN
FromLineOverride=YES
END""") 
        return True

    def get_config(self,shutit):
        shutit.get_config(self.module_id,'email',default='test@gmail.com')
        shutit.get_config(self.module_id,'password',default='')
        return True

def module():
    return gmailer(
        'shutit.tk.gmailer.gmailer', 0.0006,
        description='Allows you to send gmails with mail',
        depends=['shutit.tk.setup']
    )

