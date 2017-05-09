"""Contains all the core ShutIt methods and functionality, and public interface
off to internal objects such as shutit_pexpect.
"""

# The MIT License (MIT)
#
# Copyright (C) 2014 OpenBet Limited
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# ITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import os
import socket
import time
import re
import getpass
import codecs
import datetime
import logging
import tarfile
import pexpect
import shutit_util
import shutit_setup
from shutit_module import ShutItFailException
from shutit_class import ShutIt


class ShutItGlobal(object):
	"""Single object to store all the separate ShutIt sessions.
	"""

	only_one = None
	report_final_messages = ''
	def __init__(self):
		"""Constructor.
		"""
		self.shutit_objects = []
		# Primitive singleton enforcer.
		assert self.only_one is None
		self.only_one         = True

		self.secret_words_set = set()
		self.logfile          = None
		self.loglevel         = None
		self.shutit_signal_id = None


	def add_shutit_session(self, shutit):
		self.shutit_objects.append(shutit)

	def create_session(self, session_type='bash', docker_image=None, rm=None):
		assert isinstance(session_type, str)
		new_shutit = ShutIt()
		self.add_shutit_session(new_shutit)
		# TODO: only makes sense in session that's already bash - check this
		if session_type == 'bash':
			shutit_util.parse_args(new_shutit)
			shutit_util.load_configs(shutit=new_shutit)
			shutit_setup.setup_host_child_environment(new_shutit)
			return new_shutit
		elif session_type == 'docker':
			shutit_util.parse_args(new_shutit)
			# Set the configuration up appropriately using overrides.
			if docker_image:
				new_shutit.build['config_overrides'].append(['build','base_image',docker_image])
			if rm:
				new_shutit.target['rm'] = True
			# Now 'load' the configs
			shutit_util.load_configs(new_shutit)
			target_child = shutit_setup.conn_docker_start_container(new_shutit,'target_child')
			shutit_setup.setup_host_child_environment(new_shutit)
			shutit_setup.setup_target_child_environment(new_shutit, target_child)
			return new_shutit
		else:
			new_shutit.fail('unhandled session type: ' + session_type)


	def do_final_messages(self):
		# Show final report messages (ie messages to show after standard report).
		if self.report_final_messages != '':
			self.shutit_objects[0].log(shutit_util.colourise(31,'\r\n\r\n' + self.report_final_messages + '\r\n\r\n'), level=logging.INFO, transient=True)


	def log(self, msg, add_final_message=False, level=logging.INFO, transient=False, newline=True, mask_password=True):
		"""Logging function.

		@param add_final_message: Add this log line to the final message output to the user
		@param level:             Python log level
		@param transient:         Just write to terminal, no new line. If not a
		                          terminal, write nothing.
		"""
		if mask_password:
			for password in shutit_global_object.secret_words_set:
				if password in msg:
					msg.replace(password,'REDACTED')
		if transient:
			if sys.stdout.isatty():
				if newline:
					msg += '\r\n'
				sys.stdout.write(msg)
			else:
				return True
		else:
			logging.log(level,msg)
			if add_final_message:
				self.report_final_messages = self.report_final_messages + '\r\n' + msg + '\r\n'
		return True

shutit_global_object = ShutItGlobal()
shutit_global_object.add_shutit_session(ShutIt())
