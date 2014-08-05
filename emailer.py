"""Utility object for sending emails reports via shutit

Example code:

        e = Emailer('shutit.tk.mysql.mysql',shutit)
        for line in ['your message line 1', 'your message line 2']:
                e.add_line(line)
        for attach in ['/tmp/filetoattach1','/tmp/filetoattach2']:
                e.attach(attach)
        e.send()

Example cfg:

        [shutit.tk.mysql.mysql]
        mailto:recipient@example.com
        mailfrom:sender@example.com
        smtp_server:localhost
        subject:Shutit Report
        signature:--Angry Shutit
        compress:yes

"""

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

from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from collections import OrderedDict
from smtplib import SMTP
import os, gzip

class Emailer():

    def __init__(
        self,
        cfg_section,
        shutit
    ):
        """Initialise the Emailer object
        cfg_section - section in shutit config to look for email configuration items
                      allowing easier config according to shutit_module.
                      e.g. 'com.my_module','subject': My Module Build Failed!
                      Config Items:
                      mailto      - address to send the mail to (no default)
                      mailfrom    - address to send the mail from (angry@shutit.tk)
                      smtp_server - server to send the mail (localhost)
                      subject     - subject of the email (Shutit Report)
                      signature   - \n\n --Angry Shutit
                      compress    - gzip attachments? (True)
        """
        self.shutit    = shutit
        self.__set_config(cfg_section)
        self.lines     = []
        self.attaches  = []

    def __set_config(self,cfg_section):
        """Set a local config array up according to defaults and main shutit configuration

        cfg_section - see __init__
        """
        cfg = self.shutit.cfg
        self.config    = {}
        defaults = [
            'mailto','',
            'mailfrom','angry@shutit.tk',
            'smtp_server','localhost',
            'send_mail',True,
            'subject','Shutit Report',
            'signature','\n\n --Angry Shutit',
            'compress',True
        ]

        for i in range(len(defaults)-1):
            name    = defaults[i]
            default = defaults[i+1]
            try:
                self.config[name] = cfg[cfg_section][name]
            except KeyError as e:
                if default == '':
                    print e
                    raise Exception('Emailer._set_config: ' + name + ' must be set')
                else:
                    self.config[name] = default
            i += 1


    def __gzip(self,filename):
        """ Compress a file returning the new filename (.gz)
        """
        zn = filename + '.gz'
        fp = open(filename,'rb')
        zp = gzip.open(zn,'wb')
        zp.writelines(fp)
        fp.close()
        zp.close()
        return zn


    def add_line(self,line):
        """Add a single line to the email body
        """
        self.lines.append(line)


    def add_body(self,msg):
        """Add an entire email body message as a string, will be split on newlines
           and overwrite anything currently in the body (e.g added by add_lines)
        """
        self.lines = msg.rsplit('\n')


    def attach(self,filename,filetype="txt"):
        """Attach a file - currently needs to be entered as root (shutit)

        Filename - absolute path, relative to the docker container!
        filetype - MIMEApplication._subtype
        """
        shutit = self.shutit
        host_path = '/tmp'
        host_fn = os.path.join(host_path,os.path.basename(filename))
        shutit.get_file(filename,host_path)
        if self.config['compress']:
            filetype='x-gzip-compressed'
            filename = self.__gzip(host_fn)
        fp = open(host_fn, 'rb')
        attach = MIMEApplication(fp.read(),_subtype=filetype)
        fp.close()
        attach.add_header('Content-Disposition','attachment',filename=os.path.basename(filename))
        self.attaches.append(attach)


    def send(self):
        """Send the email according to the configured setup
        """
        if not self.config['send_mail']:
            print 'Emailer.send: Not configured to send mail!'
            return True
        msg  = MIMEMultipart()
        msg['Subject'] = self.config['subject']
        msg['To']      = self.config['mailto']
        msg['From']    = self.config['mailfrom']
        body = MIMEText('\n'.join(self.lines) + self.config['signature'])
        msg.attach(body)
        for attach in self.attaches:
            msg.attach(attach)
        s = SMTP(self.config['smtp_server'])
        # TODO: send to shutitmodule.maintainer as well
        s.sendmail(self.config['mailfrom'], self.config['mailto'], msg.as_string())
        s.quit()

