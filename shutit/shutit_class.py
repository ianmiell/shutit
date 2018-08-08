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
from shutit import shutit
from shutit import shutit_util
from shutit import shutit_global
from shutit import shutit_skeleton
from shutit import shutit_exam
from shutit import shutitclass
from shutit import ShutItInit
try:
	import ConfigParser
except ImportError: # pragma: no cover
	import configparser as ConfigParser
from shutit.shutit_sendspec import ShutItSendSpec
from shutit.shutit_module import ShutItFailException, ShutItModule
from shutit.shutit_pexpect import ShutItPexpectSession


def get_module_file(shutit, module):
	shutit.shutit_file_map[module.module_id] = module.__module_file
	return shutit.shutit_file_map[module.module_id]


def do_finalize():
	"""Runs finalize phase; run after all builds are complete and all modules
	have been stopped.
	"""
	def _finalize(shutit):
		# Stop all the modules
		shutit.stop_all()
		# Finalize in reverse order
		shutit.log('PHASE: finalizing object ' + str(shutit), level=logging.DEBUG)
		# Login at least once to get the exports.
		for module_id in shutit.module_ids(rev=True):
			# Only finalize if it's thought to be installed.
			if shutit.is_installed(shutit.shutit_map[module_id]):
				shutit.login(prompt_prefix=module_id,command=shutit_global.shutit_global_object.bash_startup_command,echo=False)
				if not shutit.shutit_map[module_id].finalize(shutit):
					shutit.fail(module_id + ' failed on finalize', shutit_pexpect_child=shutit.get_shutit_pexpect_session_from_id('target_child').pexpect_child) # pragma: no cover
				shutit.logout(echo=False)
		for fshutit in shutit_global.shutit_global_object.shutit_objects:
			_finalize(fshutit)


class LayerConfigParser(ConfigParser.RawConfigParser):

	def __init__(self):
		ConfigParser.RawConfigParser.__init__(self)
		self.layers = []

	def read(self, filenames):
		if not isinstance(filenames, list):
			filenames = [filenames]
		for filename in filenames:
			cp = ConfigParser.RawConfigParser()
			cp.read(filename)
			self.layers.append((cp, filename, None))
		return ConfigParser.RawConfigParser.read(self, filenames)

	def readfp(self, fp, filename=None):
		cp = ConfigParser.RawConfigParser()
		fp.seek(0)
		cp.readfp(fp, filename)
		self.layers.append((cp, filename, fp))
		fp.seek(0)
		ret = ConfigParser.RawConfigParser.readfp(self, fp, filename)
		return ret

	def whereset(self, section, option):
		for cp, filename, fp in reversed(self.layers):
			fp = fp # pylint
			if cp.has_option(section, option):
				return filename
		raise ShutItFailException('[%s]/%s was never set' % (section, option)) # pragma: no cover

	def get_config_set(self, section, option):
		"""Returns a set with each value per config file in it.
		"""
		values = set()
		for cp, filename, fp in self.layers:
			filename = filename # pylint
			fp = fp # pylint
			if cp.has_option(section, option):
				values.add(cp.get(section, option))
		return values

	def reload(self):
		"""
		Re-reads all layers again. In theory this should overwrite all the old
		values with any newer ones.
		It assumes we never delete a config item before reload.
		"""
		oldlayers = self.layers
		self.layers = []
		for cp, filename, fp in oldlayers:
			cp = cp # pylint
			if fp is None:
				self.read(filename)
			else:
				self.readfp(fp, filename)

	def remove_section(self, *args, **kwargs):
		raise NotImplementedError('''Layer config parsers aren't directly mutable''') # pragma: no cover

	def remove_option(self, *args, **kwargs):
		raise NotImplementedError('''Layer config parsers aren't directly mutable''') # pragma: no cover

	def set(self, *args, **kwargs):
		raise NotImplementedError('''Layer config parsers aren\'t directly mutable''') # pragma: no cover

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


def check_dependee_order(depender, dependee, dependee_id):
	"""Checks whether run orders are in the appropriate order.
	"""
	# If it depends on a module id, then the module id should be higher up
	# in the run order.
	shutit_global.shutit_global_object.yield_to_draw()
	if dependee.run_order > depender.run_order:
		return 'depender module id:\n\n' + depender.module_id + '\n\n(run order: ' + str(depender.run_order) + ') ' + 'depends on dependee module_id:\n\n' + dependee_id + '\n\n(run order: ' + str(dependee.run_order) + ') ' + 'but the latter is configured to run after the former'
	return ''


def make_dep_graph(depender):
	"""Returns a digraph string fragment based on the passed-in module
	"""
	shutit_global.shutit_global_object.yield_to_draw()
	digraph = ''
	for dependee_id in depender.depends_on:
		digraph = (digraph + '"' + depender.module_id + '"->"' + dependee_id + '";\n')
	return digraph


# TODO: change default_cnf - see above
default_cnf = '''
################################################################################
# Default core config file for ShutIt.
################################################################################

# Details relating to the target you are building to (container or bash)
[target]
# Root password for the target - replace with your chosen password
# If left blank, you will be prompted for a password
password:
# Hostname for the target - replace with your chosen target hostname
# (where applicable, eg docker container)
hostname:
# space separated list of ports to expose
# e.g. "ports:2222:22 8080:80" would expose container ports 22 and 80 as the
# host's 2222 and 8080 (where applicable)
ports:
# volume arguments, eg /tmp/postgres:/var/lib/postgres:ro
volumes:
# volumes-from arguments
volumes_from:
# Name to give the docker container (where applicable).
# Empty means "let docker default a name".
name:
# Whether to remove the docker container when finished (where applicable).
rm:no

# Information specific to the host on which the build runs.
[host]
# Ask the user if they want shutit on their path
add_shutit_to_path: yes
# Docker executable on your host machine
docker_executable:docker
# space separated list of dns servers to use
dns:
# Password for the username above on the host (only needed if sudo is needed)
password:
# Log file - will be set to 0600 perms, and defaults to /tmp/<YOUR_USERNAME>_shutit_log_<timestamp>
# A timestamp will be added to the end of the filename.
logfile:
# ShutIt paths to look up modules in separated by ":", eg /path1/here:/opt/path2/there
shutit_module_path:.
# Whether to colorize output
nocolor:no

# Repository information
[repository]
# Whether to tag
tag:yes
# Whether to suffix the date to the tag
suffix_date:no
# Suffix format (default is epoch seconds (%s), but %Y%m%d_%H%M%S is an option if the length is ok with the index)
suffix_format:%s
# tag name
name:my_module
# Whether to tar up the docker image exported
export:no
# Whether to tar up the docker image saved
save:no
# Whether to push to the server
push:no
# User on registry to namespace repo - can be set to blank if not docker.io
user:
#Must be set if push is true/yes and user is not blank
password:YOUR_INDEX_PASSWORD_OR_BLANK
#Must be set if push is true/yes and user is not blank
email:YOUR_INDEX_EMAIL_OR_BLANK
# repository server
# make blank if you want this to be sent to the main docker index on docker.io
server:
# tag suffix, defaults to "latest", eg registry/username/repository:latest.
# empty is also "latest"
tag_name:latest

# Root setup script
# Each module should set these in a config
[shutit.tk.setup]
shutit.core.module.build:yes

[shutit.tk.conn_bash]
# None

# Aspects of build process
[build]
# How to connect to target
conn_module:shutit.tk.conn_docker
# Run any docker container in privileged mode
privileged:no
# Base image can be over-ridden by --image_tag defaults to this.
base_image:ubuntu:14.04
# Whether to perform tests.
dotest:yes
# --net argument to docker, eg "bridge", "none", "container:<name|id>" or "host". Empty means use default (bridge).
net:
'''
