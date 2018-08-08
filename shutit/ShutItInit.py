"""Contains all the core ShutIt methods and functionality, and public interface
off to internal objects such as shutit_pexpect.
"""

from __future__ import print_function
from distutils.dir_util import mkpath
from distutils import spawn
try:
	from StringIO import StringIO
except ImportError: # pragma: no cover
	from io import StringIO
import argparse
import base64
import codecs
import getpass
import glob
import hashlib
import imp
import json
import logging
import operator
import os
import tarfile
import re
import readline
import string
import sys
import subprocess
import time
import uuid
import texttable
import pexpect
from . import shutit
from . import shutit_util
from . import shutit_global
from . import shutit_skeleton
from . import shutit_exam
try:
	import ConfigParser
except ImportError: # pragma: no cover
	import configparser as ConfigParser
from shutit.shutit_sendspec import ShutItSendSpec
from shutit.shutit_module import ShutItFailException, ShutItModule
from shutit.shutit_pexpect import ShutItPexpectSession


class ShutItInit(object):
	"""Object used to initialise a shutit object.
	"""

	def __init__(self,
	             action,
	             logfile='',
	             loglevel='',
	             nocolor=False,
	             delivery='bash',
	             accept=False,
	             shutitfiles=None,
	             script=None,
	             base_image='ubuntu:16.04',
	             depends='shutit.tk.setup',
	             name='',
	             domain='',
	             pattern='',
	             output_dir=False,
	             vagrant_ssh_access=False,
	             vagrant_num_machines=None,
	             vagrant_machine_prefix=None,
	             vagrant_docker=None,
	             vagrant_snapshot=None,
	             vagrant_upload=None,
	             vagrant_image_name=None,
	             push=False,
	             export=False,
	             save=False,
	             distro='',
	             mount_docker=False,
	             walkthrough=False,
	             walkthrough_wait=-1,
	             training=False,
	             choose_config=False,
	             config=[],
	             set=[],
	             ignorestop=False,
	             ignoreimage=False,
	             imageerrorok=False,
	             tag_modules=False,
	             image_tag='',
	             video=-1,
	             deps_only=False,
	             echo=False,
	             history=False,
	             long_modules=False,
	             sort='id',
	             interactive=1,
	             trace=False,
	             shutit_module_path=None,
	             exam=False):

		assert isinstance(action,str), shutit_util.print_debug()
		assert isinstance(loglevel,str), shutit_util.print_debug()

		self.action   = action
		self.logfile  = logfile
		self.loglevel = loglevel
		self.nocolor  = nocolor

		if self.action == 'version':
			return
		elif self.action == 'skeleton':
			self.accept                 = accept
			self.shutitfiles            = shutitfiles
			self.script                 = script
			self.base_image             = base_image
			self.depends                = depends
			self.name                   = name
			self.domain                 = domain
			self.pattern                = pattern
			self.output_dir             = output_dir
			self.vagrant_ssh_access     = vagrant_ssh_access
			self.vagrant_num_machines   = vagrant_num_machines
			self.vagrant_machine_prefix = vagrant_machine_prefix
			self.vagrant_docker         = vagrant_docker
			self.vagrant_snapshot       = vagrant_snapshot
			self.vagrant_upload         = vagrant_upload
			self.vagrant_image_name     = vagrant_image_name
			self.delivery               = delivery
			assert self.accept in (True,False,None), shutit_util.print_debug()
			assert not (self.shutitfiles and self.script), shutit_util.print_debug(msg='Cannot have any two of script, -d/--shutitfiles <files> as arguments')
			assert isinstance(self.base_image,str), shutit_util.print_debug()
			assert isinstance(self.depends,str), shutit_util.print_debug()
			#assert isinstance(self.shutitfiles,list)
			assert isinstance(self.name,str), shutit_util.print_debug()
			assert isinstance(self.domain,str), shutit_util.print_debug()
			assert isinstance(self.pattern,str), shutit_util.print_debug()
			assert isinstance(self.output_dir,bool), shutit_util.print_debug()
			assert isinstance(self.vagrant_ssh_access,bool), shutit_util.print_debug()
			#assert isinstance(self.delivery,str), shutit_util.print_debug()
		elif self.action == 'run':
			self.shutitfiles = shutitfiles
			self.delivery    = delivery
			self.echo        = echo
			#assert isinstance(self.delivery,str), shutit_util.print_debug()
			#assert isinstance(self.shutitfiles,list), shutit_util.print_debug()
		elif self.action == 'build' or self.action == 'list_configs' or self.action == 'list_modules':
			self.push               = push
			self.export             = export
			self.save               = save
			self.distro             = distro
			self.mount_docker       = mount_docker
			self.walkthrough        = walkthrough
			self.walkthrough_wait   = walkthrough_wait
			self.training           = training
			self.choose_config      = choose_config
			self.config             = config
			self.set                = set
			self.ignorestop         = ignorestop
			self.ignoreimage        = ignoreimage
			self.imageerrorok       = imageerrorok
			self.tag_modules        = tag_modules
			self.image_tag          = image_tag
			self.video              = video
			self.deps_only          = deps_only
			self.echo               = echo
			self.delivery           = delivery
			self.interactive        = interactive
			self.trace              = trace
			self.shutit_module_path = shutit_module_path
			self.exam               = exam
			self.history            = history
			self.sort               = sort
			self.long               = long_modules
			# Video/exam/training logic
			if self.exam and not self.training:
				shutit_global.shutit_global_object.shutit_print('Exam starting up')
				self.training = True
			if (self.exam or self.training) and not self.walkthrough:
				if not self.exam:
					shutit_global.shutit_global_object.shutit_print('--training or --exam implies --walkthrough, setting --walkthrough on!')
				self.walkthrough = True
			if isinstance(self.video, list) and self.video[0] >= 0:
				self.walkthrough      = True
				self.walkthrough_wait = self.video[0]
				self.video            = True
			if (self.video != -1 and self.video) and self.training:
				shutit_global.shutit_global_object.shutit_print('--video and --training mode incompatible')
				shutit_global.shutit_global_object.handle_exit(exit_code=1)
			if (self.video != -1 and self.video) and self.exam:
				shutit_global.shutit_global_object.shutit_print('--video and --exam mode incompatible')
				shutit_global.shutit_global_object.handle_exit(exit_code=1)
			#assert isinstance(self.delivery,str), shutit_util.print_debug()
			# If the image_tag has been set then ride roughshod over the ignoreimage value if not supplied
			if self.image_tag != '' and self.ignoreimage is None:
				self.ignoreimage = True
			# If ignoreimage is still not set, then default it to False
			if self.ignoreimage is None:
				self.ignoreimage = False
			if self.delivery in ('bash',):
				if self.image_tag != '': # pragma: no cover
					shutit_global.shutit_global_object.shutit_print('delivery method specified (' + self.delivery + ') and image_tag argument make no sense')
					shutit_global.shutit_global_object.handle_exit(exit_code=1)
