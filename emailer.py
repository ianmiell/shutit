from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from collections import OrderedDict
from smtplib import SMTP
import os, gzip

# Util to send an email during shutit build
#
# Currently this needs to be symlinked into the main shutit folder in order to work - see TODOs
#
# TODO
#  - make part of core shutit properly
#  - copy attachments properly (e.g. not using /resources),
#    thereby removing the need for root hopefully. I have considered
#    running an smtp server inside the container but this seems dirty for
#    our purposes. Ultimately there needs to be an easy way of getting files out of shutit
#
class emailer():

	# cfg_section - where to take email configs from inside shutit.config:
	#               (mailto, mailfrom, smtp_server, subject, signature, send_mail)
	def __init__(
		self,
		cfg_section,
		shutit
	):
		self._set_config(cfg_section,shutit.cfg)
		self.shutit    = shutit
		self.lines     = []
		self.attaches  = []
		self._chmod_resources(self.shutit)

	def _set_config(self,cfg_section,cfg):

		self.config    = {}
		defaults = [
			'mailto','',
			'mailfrom','angry@shutit.com',
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
					raise Exception('emailer._set_config: ' + name + ' must be set')
				else:
					self.config[name] = default
			i += 1

	def _chmod_resources(self,shutit):
		if shutit.get_file_perms('/resources') == "777":
			return True
		user = shutit.send_and_get_output('whoami').strip()
		# revert to root to do attachments
		if user != 'root':
			shutit.logout()
		shutit.send('chmod 777 /resources')
		# we've done what we need to do as root, go home
		if user != 'root':
			shutit.login(user)

	# Add a line to the email
	def add_line(self,line):
		self.lines.append(line)

	# Add an entire message as string (will overwrite anything added as lines thus far)
	def add_msg(self,msg):
		self.lines = msg.rsplit('\n')

	# Attach a file - currently needs to be entered as root (shutit)
	#
	# - Filename: absolute path, relative to the docker container!
	# - filetype: MIMEApplication._subtype
	def attach(self,filename,filetype="txt"):
		shutit = self.shutit
		# move to dockerresources to the emailer can have visibility
		resources_dir = self.shutit.cfg['host']['resources_dir']
		shutit.send('cp ' + filename + ' /resources')
		if self.config['compress']:
			filetype='x-gzip-compressed'
			filename = self.gzip(filename)
		# the file name is different on the host (running shutit), than it is on docker
		host_filename = os.path.join(resources_dir,os.path.basename(filename))
		fp = open(host_filename, 'rb')
		attach = MIMEApplication(fp.read(),_subtype=filetype)
		fp.close()
		attach.add_header('Content-Disposition','attachment',filename=os.path.basename(filename))
		self.attaches.append(attach)
		shutit.send('rm -f /resources/' + os.path.basename(filename))

	# Compress a file returning the new filename.
	def gzip(self,filename):
		resources_dir = self.shutit.cfg['host']['resources_dir']
		host_filename = os.path.join(resources_dir,os.path.basename(filename))
		zn = host_filename + '.gz'
		fp = open(host_filename,'rb')
		zp = gzip.open(zn,'wb')
		zp.writelines(fp)
		fp.close()
		zp.close()
		# delete the original file, we've got a shiny new compressed one
		self.shutit.send('rm -f /resources/' + os.path.basename(filename))
		return zn

	def send(self):
		if not self.config['send_mail']:
			print 'emailer.send: Not configured to send mail!'
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
		s.sendmail(self.config['mailfrom'], self.config['mailto'], msg.as_string())
		s.quit()

