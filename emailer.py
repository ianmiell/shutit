"""Utility object for sending emails reports via shutit

Example code::

	e = shutit.get_emailer('shutit.tk.mysql.mysql',shutit)
	for line in ['your message line 1', 'your message line 2']:
		e.add_line(line)
	for attach in ['/tmp/filetoattach1','/tmp/filetoattach2']:
		e.attach(attach)
	e.send()

Example cfg::

	[shutit.tk.mysql.mysql]
	shutit.core.alerting.emailer.mailto:recipient@example.com
	shutit.core.alerting.emailer.mailfrom:sender@example.com
	shutit.core.alerting.emailer.smtp_server:localhost
	shutit.core.alerting.emailer.subject:Shutit Report
	shutit.core.alerting.emailer.signature:--Angry Shutit
	shutit.core.alerting.emailer.compress:yes
	shutit.core.alerting.emailer.username:
	shutit.core.alerting.emailer.password:
	shutit.core.alerting.emailer.safe_mode: True
	shutit.core.alerting.emailer.mailto_maintainer: True

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
from smtplib import SMTP, SMTP_SSL, SMTPSenderRefused
import os, gzip

class Emailer():
	""" Emailer class definition
	"""

	def __init__( self, cfg_section, shutit):
		"""Initialise the emailer object
		cfg_section - section in shutit config to look for email configuration items, allowing easier config according to shutit_module.
		e.g. 'com.my_module','shutit.core.alerting.emailer.subject': My Module Build Failed!
		Config Items:
		shutit.core.alerting.emailer.mailto      - address to send the mail to (no default)
		shutit.core.alerting.emailer.mailfrom    - address to send the mail from (angry@shutit.tk)
		shutit.core.alerting.emailer.smtp_server - server to send the mail (localhost)
		shutit.core.alerting.emailer.smtp_port   - port to contact the smtp server on (587)
		shutit.core.alerting.emailer.use_tls     - should we use tls to connect (True)
		shutit.core.alerting.emailer.subject     - subject of the email (Shutit Report)
		shutit.core.alerting.emailer.signature   - --Angry Shutit
		shutit.core.alerting.emailer.compress    - gzip attachments? (True)
		shutit.core.alerting.emailer.username    - mail username
		shutit.core.alerting.emailer.password    - mail password
		shutit.core.alerting.emailer.safe_mode   - don't fail the build if we get an exception
		shutit.core.alerting.emailer.mailto_maintainer - email the maintainer of the module as well as the shutit.core.alerting.emailer.mailto address
		"""
		self.shutit    = shutit
		self.config    = {}
		self.__set_config(cfg_section)
		self.lines     = []
		self.attaches  = []

	def __set_config(self, cfg_section):
		"""Set a local config array up according to
		defaults and main shutit configuration

		cfg_section - see __init__
		"""
		defaults = [
			'shutit.core.alerting.emailer.mailto', None,
			'shutit.core.alerting.emailer.mailfrom', 'angry@shutit.tk',
			'shutit.core.alerting.emailer.smtp_server', 'localhost',
			'shutit.core.alerting.emailer.smtp_port', 25,
			'shutit.core.alerting.emailer.use_tls', True,
			'shutit.core.alerting.emailer.send_mail', True,
			'shutit.core.alerting.emailer.subject', 'Shutit Report',
			'shutit.core.alerting.emailer.signature', '--Angry Shutit',
			'shutit.core.alerting.emailer.compress', True,
			'shutit.core.alerting.emailer.username', '',
			'shutit.core.alerting.emailer.password', '',
			'shutit.core.alerting.emailer.safe_mode', True,
			'shutit.core.alerting.emailer.maintainer','',
			'shutit.core.alerting.emailer.mailto_maintainer', True
		]

		for cfg_name, cfg_default in zip(defaults[0::2], defaults[1::2]):
			try:
				self.config[cfg_name] = self.shutit.cfg[cfg_section][cfg_name]
			except KeyError:
				if cfg_default is None:
					raise Exception(cfg_section + ' ' + cfg_name + ' must be set')
				else:
					self.config[cfg_name] = cfg_default

		# only send a mail to the module's maintainer if configured correctly
		if self.config['shutit.core.alerting.emailer.mailto_maintainer'] and \
			(self.config['shutit.core.alerting.emailer.maintainer'] == "" or \
			self.config['shutit.core.alerting.emailer.maintainer'] == self.config['shutit.core.alerting.emailer.mailto']):
			self.config['shutit.core.alerting.emailer.mailto_maintainer'] = False
			self.config['shutit.core.alerting.emailer.maintainer'] = ""

	@staticmethod
	def __gzip(filename):
		""" Compress a file returning the new filename (.gz)
		"""
		zipname = filename + '.gz'
		file_pointer = open(filename,'rb')
		zip_pointer = gzip.open(zipname,'wb')
		zip_pointer.writelines(file_pointer)
		file_pointer.close()
		zip_pointer.close()
		return zipname

	def __get_smtp(self):
		""" Return the appropraite smtplib depending on wherther we're using TLS
		"""
		use_tls = self.config['shutit.core.alerting.emailer.use_tls']
		if use_tls:
			smtp = SMTP(self.config['shutit.core.alerting.emailer.smtp_server'], self.config['shutit.core.alerting.emailer.smtp_port'])
			smtp.starttls()
		else:
			smtp = SMTP_SSL(self.config['shutit.core.alerting.emailer.smtp_server'], self.config['shutit.core.alerting.emailer.smtp_port'])
		return smtp

	def add_line(self, line):
		"""Add a single line to the email body
		"""
		self.lines.append(line)

	def add_body(self, msg):
		"""Add an entire email body as a string, will be split on newlines
		   and overwrite anything currently in the body (e.g added by add_lines)
		"""
		self.lines = msg.rsplit('\n')

	def attach(self, filename, filetype="txt"):
		"""Attach a file - currently needs to be entered as root (shutit)

		Filename - absolute path, relative to the target host!
		filetype - MIMEApplication._subtype
		"""
		shutit = self.shutit
		host_path = '/tmp'
		host_fn = shutit.get_file(filename, host_path)
		if self.config['shutit.core.alerting.emailer.compress']:
			filetype = 'x-gzip-compressed'
			filename = self.__gzip(host_fn)
			host_fn = os.path.join(host_path, os.path.basename(filename))
		file_pointer = open(host_fn, 'rb')
		attach = MIMEApplication(file_pointer.read(), _subtype=filetype)
		file_pointer.close()
		attach.add_header('Content-Disposition', 'attachment', filename=os.path.basename(filename))
		self.attaches.append(attach)

	def __compose(self):
		""" Compose the message, pulling together body, attachments etc
		"""
		msg  = MIMEMultipart()
		msg['Subject'] = self.config['shutit.core.alerting.emailer.subject']
		msg['To']      = self.config['shutit.core.alerting.emailer.mailto']
		msg['From']    = self.config['shutit.core.alerting.emailer.mailfrom']
		# add the module's maintainer as a CC if configured
		if self.config['shutit.core.alerting.emailer.mailto_maintainer']:
			msg['Cc'] = self.config['shutit.core.alerting.emailer.maintainer']
		if self.config['shutit.core.alerting.emailer.signature'] != '':
			signature = '\n\n' + self.config['shutit.core.alerting.emailer.signature']
		else:
			signature = self.config['shutit.core.alerting.emailer.signature']
		body = MIMEText('\n'.join(self.lines) + signature)
		msg.attach(body)
		for attach in self.attaches:
			msg.attach(attach)
		return msg

	def send(self, attachment_failure=False):
		"""Send the email according to the configured setup

		   attachment_failure - used to indicate a recursive call after the
		   smtp server has refused based on file size.
		   Should not be used externally
		"""
		if not self.config['shutit.core.alerting.emailer.send_mail']:
			self.shutit.log('emailer.send: Not configured to send mail!', force_stdout=True)
			return True
		msg = self.__compose()
		mailto = [self.config['shutit.core.alerting.emailer.mailto']]
		smtp = self.__get_smtp()
		if self.config['shutit.core.alerting.emailer.username'] != '':
			smtp.login(self.config['shutit.core.alerting.emailer.username'], self.config['shutit.core.alerting.emailer.password'])
		if self.config['shutit.core.alerting.emailer.mailto_maintainer']:
			mailto.append(self.config['shutit.core.alerting.emailer.maintainer'])
		try:
			self.shutit.log('Attempting to send email', force_stdout=True)
			smtp.sendmail(self.config['shutit.core.alerting.emailer.mailfrom'], mailto, msg.as_string())
		except SMTPSenderRefused as refused:
			code = refused.args[0]
			if code == 552 and not attachment_failure:
				self.shutit.log("Mailserver rejected message due to " + "oversize attachments, attempting to resend without", force_stdout=True)
				self.attaches = []
				self.lines.append("Oversized attachments not sent")
				self.send(attachment_failure=True)
			else:
				self.shutit.log("Unhandled SMTP error:" + str(refused), force_stdout=True)
				if not self.config['shutit.core.alerting.emailer.safe_mode']:
					raise refused
		except Exception as error:
			self.shutit.log('Unhandled exception: ' + str(error), force_stdout=True)
			if not self.config['shutit.core.alerting.emailer.safe_mode']:
				raise error
		finally:
			smtp.quit()

