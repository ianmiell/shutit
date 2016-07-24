#!/usr/bin/env pythen

"""ShutIt skeleton functions
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

import ConfigParser
import StringIO
import argparse
import base64
import binascii
import getpass
import glob
import hashlib
import imp
import json
import logging
import operator
import os
import random
import re
import readline
import shutil
import socket
import stat
import string
import sys
import textwrap
import threading
import time
import urllib2
import urlparse
import jinja2
import pexpect
import texttable
import shutit_global
import shutit_main
import shutit_util
from shutit_module import ShutItFailException
from shutit_module import ShutItModule


def create_skeleton():
	"""Creates module based on a template supplied as a git repo.
	"""
	shutit = shutit_global.shutit

	skel_path        = shutit.cfg['skeleton']['path']
	skel_module_name = shutit.cfg['skeleton']['module_name']
	skel_domain      = shutit.cfg['skeleton']['domain']
	skel_domain_hash = shutit.cfg['skeleton']['domain_hash']
	skel_depends     = shutit.cfg['skeleton']['depends']
	skel_shutitfiles = shutit.cfg['skeleton']['shutitfiles']
	skel_delivery    = shutit.cfg['skeleton']['delivery']

	# Check setup
	if len(skel_path) == 0 or skel_path[0] != '/':
		shutit.fail('Must supply a directory and it must be absolute')
	if os.path.exists(skel_path):
		shutit.fail(skel_path + ' already exists')
	if len(skel_module_name) == 0:
		shutit.fail('Must supply a name for your module, eg mymodulename')
	if not re.match('^[a-zA-z_][0-9a-zA-Z_]+$', skel_module_name):
		shutit.fail('Module names must comply with python classname standards: cf: http://stackoverflow.com/questions/10120295/valid-characters-in-a-python-class-name')
	if len(skel_domain) == 0:
		shutit.fail('Must supply a domain for your module, eg com.yourname.madeupdomainsuffix')

	# Create folders and process template_branch
	os.makedirs(skel_path)
	os.chdir(skel_path)
	if shutit.cfg['skeleton']['template_branch'] == 'bash':
		from shutit_templates import bash
		bash.setup_bash_template(skel_path=skel_path,
		                         skel_delivery=skel_delivery,
		                         skel_domain=skel_domain,
		                         skel_module_name=skel_module_name,
		                         skel_shutitfiles=skel_shutitfiles,
		                         skel_domain_hash=skel_domain_hash,
		                         skel_depends=skel_depends)
	elif shutit.cfg['skeleton']['template_branch'] == 'docker':
		from shutit_templates import docker
		docker.setup_docker_template(skel_path=skel_path,
		                             skel_delivery=skel_delivery,
		                             skel_domain=skel_domain,
		                             skel_module_name=skel_module_name,
		                             skel_shutitfiles=skel_shutitfiles,
		                             skel_domain_hash=skel_domain_hash,
		                             skel_depends=skel_depends)
	elif shutit.cfg['skeleton']['template_branch'] == 'vagrant':
		from shutit_templates import vagrant
		vagrant.setup_vagrant_template(skel_path=skel_path,
		                               skel_delivery=skel_delivery,
		                               skel_domain=skel_domain,
		                               skel_module_name=skel_module_name,
		                               skel_shutitfiles=skel_shutitfiles,
		                               skel_domain_hash=skel_domain_hash,
		                               skel_depends=skel_depends)
	elif shutit.cfg['skeleton']['template_branch'] == 'shutitfile':
		from shutit_templates import shutitfile
		shutitfile.setup_shutitfile_template(skel_path=skel_path,
		                                     skel_delivery=skel_delivery,
		                                     skel_domain=skel_domain,
		                                     skel_module_name=skel_module_name,
		                                     skel_shutitfiles=skel_shutitfiles,
		                                     skel_domain_hash=skel_domain_hash,
		                                     skel_depends=skel_depends)
