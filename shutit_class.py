"""Contains all the core ShutIt methods and functionality, and public interface
off to internal objects such as shutit_pexpect.
"""

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
import textwrap
import time
from distutils.dir_util import mkpath
import texttable
import pexpect
import shutit
import shutit_util
import shutit_global
import shutit_skeleton
import shutit_exam
try:
	import ConfigParser
except ImportError: # pragma: no cover
	import configparser as ConfigParser
from shutit_sendspec import ShutItSendSpec
from shutit_module import ShutItFailException, ShutItModule
from shutit_pexpect import ShutItPexpectSession

PY3 = (sys.version_info[0] >= 3)


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
	             log='',
	             delivery=None,
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
	             push=False,
	             export=False,
	             save=False,
	             distro='',
	             mount_docker=False,
	             walkthrough=False,
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
	             long=False,
	             sort='id',
	             interactive=1,
	             trace=False,
	             shutit_module_path=None,
	             exam=False):

		assert isinstance(action,str)
		assert isinstance(logfile,str)
		assert isinstance(log,str)

		self.action  = action
		self.logfile = logfile
		self.log     = log

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
			self.delivery               = delivery
			assert self.accept in (True,False,None)
			assert not (self.shutitfiles and self.script),'Cannot have any two of script, -d/--shutitfiles <files> as arguments'
			assert isinstance(self.base_image,str)
			assert isinstance(self.depends,str)
			#assert isinstance(self.shutitfiles,list)
			assert isinstance(self.name,str)
			assert isinstance(self.domain,str)
			assert isinstance(self.pattern,str)
			assert isinstance(self.output_dir,bool)
			assert isinstance(self.vagrant_ssh_access,bool)
			# TODO: other asserts in other things.
		elif self.action == 'run':
			self.shutitfiles = shutitfiles
			self.delivery    = delivery
			#assert isinstance(self.shutitfiles,list)
		elif self.action == 'build' or self.action == 'list_configs' or self.action == 'list_modules':
			self.push               = push
			self.export             =  export
			self.save               = save
			self.distro             = distro
			self.mount_docker       = mount_docker
			self.walkthrough        = walkthrough
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
			self.history = history
			self.sort = sort
			self.long = long




class ShutIt(object):
	"""ShutIt build class.
	Represents an instance of a ShutIt run/session/build with associated config.
	"""

	def __init__(self):
		"""Constructor.
		Sets up:

				- shutit_modules          - representation of loaded shutit modules
				- shutit_main_dir         - directory in which shutit is located
				- cfg                     - dictionary of configuration of build
				- shutit_map              - maps module_ids to module objects
		"""
		# Store the root directory of this application.
		# http://stackoverflow.com/questions/5137497
		self.config_parser                   = None
		self.build                           = {}
		self.build['report']                 = ''
		self.build['mount_docker']           = False
		self.build['distro_override']        = ''
		self.build['shutit_command_history'] = []
		self.build['walkthrough']            = False # Whether to honour 'walkthrough' requests
		self.build['walkthrough_wait']       = -1 # mysterious problems setting this to 1 with fixterm
		self.repository                      = {}
		# If no LOGNAME available,
		self.host                            = {}
		self.host['shutit_path']             = sys.path[0]
		self.host['calling_path']            = os.getcwd()
		self.build['asciinema_session']      = None
		self.build['asciinema_session_file'] = None

		# These used to be in shutit_global, so we pass them in as args so
		# the original reference can be put in shutit_global
		self.shutitfile                     = {}
		# Needed for patterns
		self.expect_prompts                 = {}
		self.list_configs                   = {}
		self.target                         = {}
		self.shutit_signal                  = {}
		self.action                         = {}
		self.current_shutit_pexpect_session = None
		self.shutit_pexpect_sessions        = {}
		self.shutit_modules                 = set()
		self.shutit_main_dir                = os.path.abspath(os.path.dirname(__file__))
		self.shutit_map                     = {}
		self.shutit_file_map                = {}
		# These are new members we dont have to provide compatibility for
		self.conn_modules                   = set()
		# Whether to list the modules seen
		self.list_modules                   = {}
		self.cfg = {}                              # used to store module information
		self.cfg['shutitfile'] = self.shutitfile   # required for patterns
		self.cfg['skeleton']   = {}                # required for patterns



	def __str__(self):
		string = 'ShutIt Object:\n'
		string += '==============\n'
		string += str(self.current_shutit_pexpect_session.login_stack)
		return string


	def add_shutit_pexpect_session_environment(self, pexpect_session_environment):
		"""Adds an environment object to a shutit_pexpect_session object.
		"""
		shutit_global.shutit_global_object.shutit_pexpect_session_environments.add(pexpect_session_environment)


	def get_shutit_pexpect_session_environment(self, environment_id):
		"""Returns the first shutit_pexpect_session object related to the given
		environment-id
		"""
		if not isinstance(environment_id, str):
			self.fail('Wrong argument type in get_shutit_pexpect_session_environment') # pragma: no cover
		for env in shutit_global.shutit_global_object.shutit_pexpect_session_environments:
			if env.environment_id == environment_id:
				return env
		return None


	def get_current_shutit_pexpect_session_environment(self, note=None):
		"""Returns the current environment from the currently-set default
		pexpect child.
		"""
		self.handle_note(note)
		res = self.get_current_shutit_pexpect_session().current_environment
		self.handle_note_after(note)
		return res


	def get_current_shutit_pexpect_session(self, note=None):
		"""Returns the currently-set default pexpect child.

		@return: default shutit pexpect child object
		"""
		self.handle_note(note)
		res = self.current_shutit_pexpect_session
		self.handle_note_after(note)
		return res


	def get_default_shutit_pexpect_session_expect(self):
		"""Returns the currently-set default pexpect string (usually a prompt).

		@return: default pexpect string
		"""
		return self.current_shutit_pexpect_session.default_expect


	def get_default_shutit_pexpect_session_check_exit(self):
		"""Returns default value of check_exit. See send method.

		@rtype:  boolean
		@return: Default check_exit value
		"""
		return self.current_shutit_pexpect_session.check_exit


	def set_default_shutit_pexpect_session(self, shutit_pexpect_session):
		"""Sets the default pexpect child.

		@param shutit_pexpect_session: pexpect child to set as default
		"""
		assert isinstance(shutit_pexpect_session, ShutItPexpectSession)
		self.current_shutit_pexpect_session = shutit_pexpect_session
		return True


	def set_default_shutit_pexpect_session_expect(self, expect=None):
		"""Sets the default pexpect string (usually a prompt).
		Defaults to the configured root prompt if no
		argument is passed.

		@param expect: String to expect in the output
		@type expect: string
		"""
		if expect is None:
			self.current_shutit_pexpect_session.default_expect = self.expect_prompts['root']
		else:
			self.current_shutit_pexpect_session.default_expect = expect
		return True


	# TODO: should this be in global? Or fail globally if there is only one un-failed shutit object?
	def fail(self, msg, shutit_pexpect_child=None, throw_exception=False):
		"""Handles a failure, pausing if a pexpect child object is passed in.

		@param shutit_pexpect_child: pexpect child to work on
		@param throw_exception: Whether to throw an exception.
		@type throw_exception: boolean
		"""
		# Note: we must not default to a child here
		if shutit_pexpect_child is not None:
			shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
			shutit_pexpect_session.pause_point('Pause point on fail: ' + msg, colour='31')
		if throw_exception:
			sys.stderr.write('Error caught: ' + msg + '\n')
			sys.stderr.write('\n')
			raise ShutItFailException(msg)
		else:
			# This is an "OK" failure, ie we don't need to throw an exception.
			# However, it's still a failure, so return 1
			self.log(msg,level=logging.CRITICAL)
			self.log('Error seen, exiting with status 1',level=logging.CRITICAL)
			self.handle_exit(exit_code=1,msg=msg)



	def get_current_environment(self, note=None):
		"""Returns the current environment id from the current
		shutit_pexpect_session
		"""
		self.handle_note(note)
		res = self.get_current_shutit_pexpect_session_environment().environment_id
		self.handle_note_after(note)
		return res


	def multisend(self,
	              send,
	              send_dict,
	              expect=None,
	              shutit_pexpect_child=None,
	              timeout=3600,
	              check_exit=None,
	              fail_on_empty_before=True,
	              record_command=True,
	              exit_values=None,
	              escape=False,
	              echo=None,
	              note=None,
	              secret=False,
	              nonewline=False,
	              loglevel=logging.DEBUG):
		"""Multisend. Same as send, except it takes multiple sends and expects in a dict that are
		processed while waiting for the end "expect" argument supplied.

		@param send_dict:            dict of sends and expects, eg: {'interim prompt:','some input','other prompt','some other input'}
		@param expect:               String or list of strings of final expected output that returns from this function. See send()
		@param send:                 See send()
		@param shutit_pexpect_child:                See send()
		@param timeout:              See send()
		@param check_exit:           See send()
		@param fail_on_empty_before: See send()
		@param record_command:       See send()
		@param exit_values:          See send()
		@param echo:                 See send()
		@param note:                 See send()
		"""
		assert isinstance(send_dict, dict)
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		expect = expect or self.get_current_shutit_pexpect_session().default_expect
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.multisend(ShutItSendSpec(shutit_pexpect_session,send=send,
		                                                       send_dict=send_dict,
		                                                       expect=expect,
		                                                       timeout=timeout,
		                                                       check_exit=check_exit,
		                                                       fail_on_empty_before=fail_on_empty_before,
		                                                       record_command=record_command,
		                                                       exit_values=exit_values,
		                                                       escape=escape,
		                                                       echo=echo,
		                                                       note=note,
		                                                       loglevel=loglevel,
		                                                       secret=secret,
		                                                       nonewline=nonewline))


	def send_and_require(self,
	                     send,
	                     regexps,
	                     not_there=False,
	                     shutit_pexpect_child=None,
	                     echo=None,
	                     note=None,
	                     loglevel=logging.INFO):
		"""Send string and require the item in the output.
		See send_until
	    """
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.send_and_require(send,
		                                               regexps,
		                                               not_there=not_there,
		                                               echo=echo,
		                                               note=note,
		                                               loglevel=loglevel)


	def send_until(self,
	               send,
	               regexps,
	               not_there=False,
	               shutit_pexpect_child=None,
	               cadence=5,
	               retries=100,
	               echo=None,
	               note=None,
	               debug_command=None,
	               pause_point_on_fail=True,
	               nonewline=False,
	               loglevel=logging.INFO):
		"""Send string on a regular cadence until a string is either seen, or the timeout is triggered.

		@param send:                 See send()
		@param regexps:              List of regexps to wait for.
		@param not_there:            If True, wait until this a regexp is not seen in the output. If False
		                             wait until a regexp is seen in the output (default)
		@param shutit_pexpect_child:                See send()
		@param echo:                 See send()
		@param note:                 See send()
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.send_until(send,
		                                         regexps,
		                                         not_there=not_there,
		                                         cadence=cadence,
		                                         retries=retries,
		                                         echo=echo,
		                                         note=note,
		                                         loglevel=loglevel,
		                                         debug_command=debug_command,
		                                         nonewline=nonewline,
		                                         pause_point_on_fail=pause_point_on_fail)


	def challenge(self,
	              task_desc,
	              expect=None,
	              hints=[],
	              congratulations='OK',
	              failed='FAILED',
	              expect_type='exact',
	              challenge_type='command',
	              shutit_pexpect_child=None,
	              timeout=None,
	              check_exit=None,
	              fail_on_empty_before=True,
	              record_command=True,
	              exit_values=None,
	              echo=True,
	              escape=False,
	              pause=1,
	              loglevel=logging.DEBUG,
	              follow_on_context=None,
	              num_stages=None):
		"""Set the user a task to complete, success being determined by matching the output.

		Either pass in regexp(s) desired from the output as a string or a list, or an md5sum of the output wanted.

		@param follow_on_context     On success, move to this context. A dict of information about that context.
		                             context              = the type of context, eg docker, bash
		                             ok_container_name    = if passed, send user to this container
		                             reset_container_name = if resetting, send user to this container
		@param challenge_type        Behaviour of challenge made to user
		                             command = check for output of single command
		                             golf    = user gets a pause point, and when leaving, command follow_on_context['check_command'] is run to check the output
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.challenge(self,
		                                        task_desc=task_desc,
  		                                        expect=expect,
		                                        hints=hints,
		                                        congratulations=congratulations,
		                                        failed=failed,
		                                        expect_type=expect_type,
		                                        challenge_type=challenge_type,
		                                        timeout=timeout,
		                                        check_exit=check_exit,
		                                        fail_on_empty_before=fail_on_empty_before,
		                                        record_command=record_command,
		                                        exit_values=exit_values,
		                                        echo=echo,
		                                        escape=escape,
		                                        pause=pause,
		                                        loglevel=loglevel,
		                                        follow_on_context=follow_on_context,
		                                        num_stages=num_stages)
	# Alternate names
	practice = challenge
	golf     = challenge



	def send(self,
	         send,
	         expect=None,
	         shutit_pexpect_child=None,
	         timeout=None,
	         check_exit=None,
	         fail_on_empty_before=True,
	         record_command=True,
	         exit_values=None,
	         echo=None,
	         escape=False,
	         retry=3,
	         note=None,
	         assume_gnu=True,
	         follow_on_commands=None,
	         searchwindowsize=None,
	         maxread=None,
	         delaybeforesend=None,
	         secret=False,
	         nonewline=False,
	         background=False,
	         wait=True,
	         loglevel=logging.INFO):
		"""Send string as a shell command, and wait until the expected output
		is seen (either a string or any from a list of strings) before
		returning. The expected string will default to the currently-set
		default expected string (see get_default_shutit_pexpect_session_expect)

		Returns the pexpect return value (ie which expected string in the list
		matched)

		@param send: See shutit.ShutItSendSpec
		@param expect: See shutit.ShutItSendSpec
		@param shutit_pexpect_child: See shutit.ShutItSendSpec
		@param timeout: See shutit.ShutItSendSpec
		@param check_exit: See shutit.ShutItSendSpec
		@param fail_on_empty_before:See shutit.ShutItSendSpec
		@param record_command:See shutit.ShutItSendSpec
		@param exit_values:See shutit.ShutItSendSpec
		@param echo: See shutit.ShutItSendSpec
		@param escape: See shutit.ShutItSendSpec
		@param retry: See shutit.ShutItSendSpec
		@param note: See shutit.ShutItSendSpec
		@param assume_gnu: See shutit.ShutItSendSpec
		@param wait: See shutit.ShutItSendSpec
		@return: The pexpect return value (ie which expected string in the list matched)
		@rtype: string
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		ignore_background = not wait
		#print('SEND: ' + send)
		return shutit_pexpect_session.send(ShutItSendSpec(shutit_pexpect_session,
		                                                  send,
		                                                  expect=expect,
		                                                  timeout=timeout,
		                                                  check_exit=check_exit,
		                                                  fail_on_empty_before=fail_on_empty_before,
		                                                  record_command=record_command,
		                                                  exit_values=exit_values,
		                                                  echo=echo,
		                                                  escape=escape,
		                                                  retry=retry,
		                                                  note=note,
		                                                  assume_gnu=assume_gnu,
		                                                  loglevel=loglevel,
		                                                  follow_on_commands=follow_on_commands,
		                                                  searchwindowsize=searchwindowsize,
		                                                  maxread=maxread,
		                                                  delaybeforesend=delaybeforesend,
		                                                  secret=secret,
		                                                  nonewline=nonewline,
		                                                  run_in_background=background,
		                                                  ignore_background=ignore_background))
	# alias send to send_and_expect
	send_and_expect = send


	def send_and_return_status(self,
	                           send,
	                           expect=None,
	                           shutit_pexpect_child=None,
	                           timeout=None,
	                           check_exit=None,
	                           fail_on_empty_before=True,
	                           record_command=True,
	                           exit_values=None,
	                           echo=None,
	                           escape=False,
	                           retry=3,
	                           note=None,
	                           assume_gnu=True,
	                           follow_on_commands=None,
	                           loglevel=logging.INFO):
		"""Returns true if a good exit code was received (usually 0)
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		shutit_pexpect_session.send(ShutItSendSpec(shutit_pexpect_session,send=send,
		                            expect=expect,
		                            timeout=timeout,
		                            check_exit=check_exit,
		                            fail_on_empty_before=fail_on_empty_before,
		                            record_command=record_command,
		                            exit_values=exit_values,
		                            echo=echo,
		                            escape=escape,
		                            retry=retry,
		                            note=note,
		                            assume_gnu=assume_gnu,
		                            loglevel=loglevel,
		                            follow_on_commands=follow_on_commands))
		return shutit_pexpect_session.check_last_exit_values(send,
		                                                     expect=expect,
		                                                     exit_values=exit_values,
		                                                     retry=retry,
		                                                     retbool=True)


	def handle_note(self, note, command='', training_input=''):
		"""Handle notes and walkthrough option.

		@param note:                 See send()
		"""
		if self.build['walkthrough'] and note != None and note != '':
			assert isinstance(note, str)
			wait = self.build['walkthrough_wait']
			wrap = '\n' + 80*'=' + '\n'
			message = wrap + note + wrap
			if command != '':
				message += 'Command to be run is:\n\t' + command + wrap
			if wait >= 0:
				self.pause_point(message, colour=31, wait=wait)
			else:
				if training_input != '' and self.build['training']:
					if len(training_input.split('\n')) == 1:
						print(shutit_util.colourise('31',message))
						while self.util_raw_input(prompt=shutit_util.colourise('32','Enter the command to continue (or "s" to skip typing it in): ')) not in (training_input,'s'):
							print('Wrong! Try again!')
						print(shutit_util.colourise('31','OK!'))
					else:
						self.pause_point(message + '\nToo long to use for training, so skipping the option to type in!\nHit CTRL-] to continue', colour=31)
				else:
					self.pause_point(message + '\nHit CTRL-] to continue', colour=31)
		return True


	def handle_note_after(self, note, training_input=''):
		if self.build['walkthrough'] and note != None:
			wait = self.build['walkthrough_wait']
			if wait >= 0:
				time.sleep(wait)
			if training_input != '' and self.build['training']:
				self.pause_point('Training mode - pause point.\nDo what you like, but try not to disturb state too much,\neg by moving directories exiting the/entering a new shell.\nHit CTRL-] to continue.')
		return True


	def expect_allow_interrupt(self,
	                           shutit,
	                           shutit_pexpect_child,
	                           expect,
	                           timeout,
	                           iteration_s=1):
		"""This function allows you to interrupt the run at more or less any
		point by breaking up the timeout into interactive chunks.
		"""
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		accum_timeout = 0
		if isinstance(expect, str):
			expect = [expect]
		if timeout < 1:
			timeout = 1
		if iteration_s > timeout:
			iteration_s = timeout - 1
		if iteration_s < 1:
			iteration_s = 1
		timed_out = True
		while accum_timeout < timeout:
			res = shutit_pexpect_session.expect(expect, timeout=iteration_s)
			if res == len(expect):
				if shutit.build['ctrlc_stop']:
					timed_out = False
					shutit.build['ctrlc_stop'] = False
					break
				accum_timeout += iteration_s
			else:
				return res
		if timed_out and not shutit_global.shutit_global_object.determine_interactive():
			self.log('Command timed out, trying to get terminal back for you', level=logging.DEBUG)
			self.fail('Timed out and could not recover') # pragma: no cover
		else:
			if shutit_global.shutit_global_object.determine_interactive():
				shutit_pexpect_child.send('\x03')
				res = shutit_pexpect_child.expect(expect,timeout=1)
				if res == len(expect):
					shutit_pexpect_child.send('\x1a')
					res = shutit_pexpect_child.expect(expect,timeout=1)
					if res == len(expect):
						self.fail('CTRL-C sent by ShutIt following a timeout, and could not recover') # pragma: no cover
				shutit_pexpect_session.pause_point('CTRL-C sent by ShutIt following a timeout; the command has been cancelled')
				return res
			else:
				if timed_out:
					self.fail('Timed out and interactive, but could not recover') # pragma: no cover
				else:
					self.fail('CTRL-C hit and could not recover') # pragma: no cover
		self.fail('Should not get here (expect_allow_interrupt)') # pragma: no cover
		return True


	def run_script(self,
	               script,
	               shutit_pexpect_child=None,
	               in_shell=True,
	               note=None,
	               loglevel=logging.DEBUG):
		"""Run the passed-in string as a script on the target's command line.

		@param script:   String representing the script. It will be de-indented
						 and stripped before being run.
		@param shutit_pexpect_child:    See send()
		@param in_shell: Indicate whether we are in a shell or not. (Default: True)
		@param note:     See send()

		@type script:    string
		@type in_shell:  boolean
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.run_script(script,in_shell=in_shell,note=note,loglevel=loglevel)


	def send_file(self,
	              path,
	              contents,
	              shutit_pexpect_child=None,
	              truncate=False,
	              note=None,
	              user=None,
	              group=None,
	              loglevel=logging.INFO,
	              encoding=None):
		"""Sends the passed-in string as a file to the passed-in path on the
		target.

		@param path:        Target location of file on target.
		@param contents:    Contents of file as a string.
		@param shutit_pexpect_child:       See send()
		@param note:        See send()
		@param user:        Set ownership to this user (defaults to whoami)
		@param group:       Set group to this user (defaults to first group in groups)

		@type path:         string
		@type contents:     string
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.send_file(path,
		                                        contents,
		                                        truncate=truncate,
		                                        note=note,
		                                        user=user,
		                                        group=group,
		                                        loglevel=loglevel,
		                                        encoding=encoding)


	def chdir(self,
	          path,
	          shutit_pexpect_child=None,
	          timeout=3600,
	          note=None,
	          loglevel=logging.DEBUG):
		"""How to change directory will depend on whether we are in delivery mode bash or docker.

		@param path:          Path to send file to.
		@param shutit_pexpect_child:         See send()
		@param timeout:       Timeout on response
		@param note:          See send()
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.chdir(path,timeout=timeout,note=note,loglevel=loglevel)


	def send_host_file(self,
	                   path,
	                   hostfilepath,
	                   expect=None,
	                   shutit_pexpect_child=None,
	                   note=None,
	                   user=None,
	                   group=None,
	                   loglevel=logging.INFO):
		"""Send file from host machine to given path

		@param path:          Path to send file to.
		@param hostfilepath:  Path to file from host to send to target.
		@param expect:        See send()
		@param shutit_pexpect_child:         See send()
		@param note:          See send()
		@param user:          Set ownership to this user (defaults to whoami)
		@param group:         Set group to this user (defaults to first group in groups)

		@type path:           string
		@type hostfilepath:   string
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		expect = expect or self.get_current_shutit_pexpect_session().default_expect
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		self.handle_note(note, 'Sending file from host: ' + hostfilepath + ' to target path: ' + path)
		self.log('Sending file from host: ' + hostfilepath + ' to: ' + path, level=loglevel)
		if user is None:
			user = shutit_pexpect_session.whoami()
		if group is None:
			group = self.whoarewe()
		# TODO: use gz for both
		if os.path.isfile(hostfilepath):
			shutit_pexpect_session.send_file(path,
			                                 codecs.open(hostfilepath,mode='rb',encoding='iso-8859-1').read(),
			                                 user=user,
			                                 group=group,
			                                 loglevel=loglevel,
			                                 encoding='iso-8859-1')
		elif os.path.isdir(hostfilepath):
			# Need a binary type encoding for gzip(?)
			self.send_host_dir(path,
			                   hostfilepath,
			                   user=user,
			                   group=group,
			                   loglevel=loglevel)
		else:
			self.fail('send_host_file - file: ' + hostfilepath + ' does not exist as file or dir. cwd is: ' + os.getcwd(), shutit_pexpect_child=shutit_pexpect_child, throw_exception=False) # pragma: no cover
		self.handle_note_after(note=note)
		return True


	def send_host_dir(self,
	                  path,
	                  hostfilepath,
	                  expect=None,
	                  shutit_pexpect_child=None,
	                  note=None,
	                  user=None,
	                  group=None,
	                  loglevel=logging.DEBUG):
		"""Send directory and all contents recursively from host machine to
		given path.  It will automatically make directories on the target.

		@param path:          Path to send directory to (places hostfilepath inside path as a subfolder)
		@param hostfilepath:  Path to file from host to send to target
		@param expect:        See send()
		@param shutit_pexpect_child:         See send()
		@param note:          See send()
		@param user:          Set ownership to this user (defaults to whoami)
		@param group:         Set group to this user (defaults to first group in groups)

		@type path:          string
		@type hostfilepath:  string
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		expect = expect or self.get_current_shutit_pexpect_session().default_expect
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		self.handle_note(note, 'Sending host directory: ' + hostfilepath + ' to target path: ' + path)
		self.log('Sending host directory: ' + hostfilepath + ' to: ' + path, level=logging.INFO)
		shutit_pexpect_session.send(ShutItSendSpec(shutit_pexpect_session,send=' command mkdir -p ' + path,
		                                           echo=False,
		                                           loglevel=loglevel))
		if user is None:
			user = shutit_pexpect_session.whoami()
		if group is None:
			group = self.whoarewe()
		# Create gzip of folder
		#import pdb
		#pdb.set_trace()
		if shutit_pexpect_session.command_available('tar'):
			gzipfname = '/tmp/shutit_tar_tmp.tar.gz'
			with tarfile.open(gzipfname, 'w:gz') as tar:
				tar.add(hostfilepath, arcname=os.path.basename(hostfilepath))
			shutit_pexpect_session.send_file(gzipfname,
			                                 codecs.open(gzipfname,mode='rb',encoding='iso-8859-1').read(),
			                                 user=user,
			                                 group=group,
			                                 loglevel=loglevel,
			                                 encoding='iso-8859-1')
			shutit_pexpect_session.send(ShutItSendSpec(shutit_pexpect_session,send=' command mkdir -p ' + path + ' && command tar -C ' + path + ' -zxf ' + gzipfname))
		else:
			# If no gunzip, fall back to old slow method.
			for root, subfolders, files in os.walk(hostfilepath):
				subfolders.sort()
				files.sort()
				for subfolder in subfolders:
					shutit_pexpect_session.send(ShutItSendSpec(shutit_pexpect_session,send=' command mkdir -p ' + path + '/' + subfolder,
					                                           echo=False,
					                                           loglevel=loglevel))
					self.log('send_host_dir recursing to: ' + hostfilepath + '/' + subfolder, level=logging.DEBUG)
					self.send_host_dir(path + '/' + subfolder,
					                   hostfilepath + '/' + subfolder,
					                   expect=expect,
					                   shutit_pexpect_child=shutit_pexpect_child,
					                   loglevel=loglevel)
				for fname in files:
					hostfullfname = os.path.join(root, fname)
					targetfname = os.path.join(path, fname)
					self.log('send_host_dir sending file ' + hostfullfname + ' to ' + 'target file: ' + targetfname, level=logging.DEBUG)
					shutit_pexpect_session.send_file(targetfname,
					                                 codecs.open(hostfullfname,mode='rb',encoding='iso-8859-1').read(),
					                                 user=user,
					                                 group=group,
					                                 loglevel=loglevel,
					                                 encoding='iso-8859-1')
		self.handle_note_after(note=note)
		return True


	def file_exists(self,
	                filename,
	                shutit_pexpect_child=None,
	                directory=False,
	                note=None,
	                loglevel=logging.DEBUG):
		"""Return True if file exists on the target host, else False

		@param filename:   Filename to determine the existence of.
		@param shutit_pexpect_child:      See send()
		@param directory:  Indicate that the file is a directory.
		@param note:       See send()

		@type filename:    string
		@type directory:   boolean

		@rtype: boolean
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.file_exists(filename=filename,directory=directory,note=note,loglevel=loglevel)


	def get_file_perms(self,
	                   filename,
	                   shutit_pexpect_child=None,
	                   note=None,
	                   loglevel=logging.DEBUG):
		"""Returns the permissions of the file on the target as an octal
		string triplet.

		@param filename:  Filename to get permissions of.
		@param shutit_pexpect_child:     See send()
		@param note:      See send()

		@type filename:   string

		@rtype:           string
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.get_file_perms(filename,note=note,loglevel=loglevel)



	def remove_line_from_file(self,
	                          line,
	                          filename,
	                          shutit_pexpect_child=None,
	                          match_regexp=None,
	                          literal=False,
	                          note=None,
	                          loglevel=logging.DEBUG):
		"""Removes line from file, if it exists.
		Must be exactly the line passed in to match.
		Returns True if there were no problems, False if there were.

		@param line:          Line to remove.
		@param filename       Filename to remove it from.
		@param shutit_pexpect_child:         See send()
		@param match_regexp:  If supplied, a regexp to look for in the file
		                      instead of the line itself,
		                      handy if the line has awkward characters in it.
		@param literal:       If true, then simply grep for the exact string without
		                      bash interpretation. (Default: False)
		@param note:          See send()

		@type line:           string
		@type filename:       string
		@type match_regexp:   string
		@type literal:        boolean

		@return:              True if the line was matched and deleted, False otherwise.
		@rtype:               boolean
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.remove_line_from_file(line,filename,match_regexp=match_regexp,literal=literal,note=note,loglevel=loglevel)


	def change_text(self,
	                text,
	                fname,
	                pattern=None,
	                expect=None,
	                shutit_pexpect_child=None,
	                before=False,
	                force=False,
	                delete=False,
	                note=None,
	                replace=False,
	                line_oriented=True,
	                create=True,
	                loglevel=logging.DEBUG):

		"""Change text in a file.

		Returns None if there was no match for the regexp, True if it was matched
		and replaced, and False if the file did not exist or there was some other
		problem.

		@param text:          Text to insert.
		@param fname:         Filename to insert text to
		@param pattern:       Regexp for a line to match and insert after/before/replace.
		                      If none, put at end of file.
		@param expect:        See send()
		@param shutit_pexpect_child:         See send()
		@param before:        Whether to place the text before or after the matched text.
		@param force:         Force the insertion even if the text is in the file.
		@param delete:        Delete text from file rather than insert
		@param replace:       Replace matched text with passed-in text. If nothing matches, then append.
		@param note:          See send()
		@param line_oriented: Consider the pattern on a per-line basis (default True).
		                      Can match any continuous section of the line, eg 'b.*d' will match the line: 'abcde'
		                      If not line_oriented, the regexp is considered on with the flags re.DOTALL, re.MULTILINE
		                      enabled
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		expect = expect or self.get_current_shutit_pexpect_session().default_expect
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.change_text(text,
		                                          fname,
		                                          pattern=pattern,
		                                          before=before,
		                                          force=force,
		                                          delete=delete,
		                                          note=note,
		                                          replace=replace,
		                                          line_oriented=line_oriented,
		                                          create=create,
		                                          loglevel=loglevel)


	def insert_text(self,
	                text,
	                fname,
	                pattern=None,
	                expect=None,
	                shutit_pexpect_child=None,
	                before=False,
	                force=False,
	                note=None,
	                replace=False,
	                line_oriented=True,
	                create=True,
	                loglevel=logging.DEBUG):
		"""Insert a chunk of text at the end of a file, or after (or before) the first matching pattern
		in given file fname.
		See change_text"""
		return self.change_text(text=text,
		                        fname=fname,
		                        pattern=pattern,
		                        expect=expect,
		                        shutit_pexpect_child=shutit_pexpect_child,
		                        before=before,
		                        force=force,
		                        note=note,
		                        line_oriented=line_oriented,
		                        create=create,
		                        replace=replace,
		                        delete=False,
		                        loglevel=loglevel)


	def delete_text(self,
	                text,
	                fname,
	                pattern=None,
	                expect=None,
	                shutit_pexpect_child=None,
	                note=None,
	                before=False,
	                force=False,
	                line_oriented=True,
	                loglevel=logging.DEBUG):
		"""Delete a chunk of text from a file.
		See insert_text.
		"""
		return self.change_text(text,
		                        fname,
		                        pattern,
		                        expect,
		                        shutit_pexpect_child,
		                        before,
		                        force,
		                        note=note,
		                        delete=True,
		                        line_oriented=line_oriented,
		                        loglevel=loglevel)


	def replace_text(self,
	                 text,
	                 fname,
	                 pattern=None,
	                 expect=None,
	                 shutit_pexpect_child=None,
	                 note=None,
	                 before=False,
	                 force=False,
	                 line_oriented=True,
	                 loglevel=logging.DEBUG):
		"""Replace a chunk of text from a file.
		See insert_text.
		"""
		return self.change_text(text,
		                        fname,
		                        pattern,
		                        expect,
		                        shutit_pexpect_child,
		                        before,
		                        force,
		                        note=note,
		                        line_oriented=line_oriented,
		                        replace=True,
		                        loglevel=loglevel)


	def add_line_to_file(self, line, filename, expect=None, shutit_pexpect_child=None, match_regexp=None, loglevel=logging.DEBUG):
		"""Deprecated.

		Use replace/insert_text instead.

		Adds line to file if it doesn't exist (unless Force is set, which it is not by default).
		Creates the file if it doesn't exist.
		Must be exactly the line passed in to match.
		Returns True if line(s) added OK, False if not.
		If you have a lot of non-unique lines to add, it's a good idea to have a sentinel value to add first, and then if that returns true, force the remainder.

		@param line:          Line to add. If a list, processed per-item, and match_regexp ignored.
		@param filename:      Filename to add it to.
		@param expect:        See send()
		@param shutit_pexpect_child:         See send()
		@param match_regexp:  If supplied, a regexp to look for in the file instead of the line itself, handy if the line has awkward characters in it.

		@type line:           string
		@type filename:       string
		@type match_regexp:   string

		"""
		if isinstance(line, str):
			lines = [line]
		elif isinstance(line, list):
			lines = line
			match_regexp = None
		fail = False
		for line in lines:
			if match_regexp is None:
				this_match_regexp = line
			else:
				this_match_regexp = match_regexp
			if not self.replace_text(line,
			                         filename,
			                         pattern=this_match_regexp,
			                         shutit_pexpect_child=shutit_pexpect_child,
			                         expect=expect,
			                         loglevel=loglevel):
				fail = True
		if fail:
			return False
		return True


	def add_to_bashrc(self, line, shutit_pexpect_child=None, match_regexp=None, note=None, loglevel=logging.DEBUG):
		"""Takes care of adding a line to everyone's bashrc
		(/etc/bash.bashrc, /etc/profile).

		@param line:          Line to add.
		@param shutit_pexpect_child:         See send()
		@param match_regexp:  See add_line_to_file()
		@param note:          See send()
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		shutit_pexpect_session.add_to_bashrc(line,match_regexp=match_regexp,note=note,loglevel=loglevel)
		return True


	def get_url(self,
	            filename,
	            locations,
	            command='curl',
	            shutit_pexpect_child=None,
	            timeout=3600,
	            fail_on_empty_before=True,
	            record_command=True,
	            exit_values=None,
	            retry=3,
	            note=None,
	            loglevel=logging.DEBUG):
		"""Handles the getting of a url for you.

		Example:
		get_url('somejar.jar', ['ftp://loc.org','http://anotherloc.com/jars'])

		@param filename:             name of the file to download
		@param locations:            list of URLs whence the file can be downloaded
		@param command:              program to use to download the file (Default: wget)
		@param shutit_pexpect_child:                See send()
		@param timeout:              See send()
		@param fail_on_empty_before: See send()
		@param record_command:       See send()
		@param exit_values:          See send()
		@param retry:                How many times to retry the download
		                             in case of failure. Default: 3
		@param note:                 See send()

		@type filename:              string
		@type locations:             list of strings
		@type retry:                 integer

		@return: True if the download was completed successfully, False otherwise.
		@rtype: boolean
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.get_url(filename,
		                                      locations,
		                                      send=command,
		                                      timeout=timeout,
		                                      fail_on_empty_before=fail_on_empty_before,
		                                      record_command=record_command,
		                                      exit_values=exit_values,
		                                      retry=retry,
		                                      note=note,
		                                      loglevel=loglevel)


	def user_exists(self,
	                user,
	                shutit_pexpect_child=None,
	                note=None,
 	                loglevel=logging.DEBUG):
		"""Returns true if the specified username exists.

		@param user:   username to check for
		@param shutit_pexpect_child:  See send()
		@param note:   See send()

		@type user:    string

		@rtype:        boolean
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session(user,note=note,loglevel=loglevel)


	def package_installed(self,
	                      package,
	                      shutit_pexpect_child=None,
	                      note=None,
	                      loglevel=logging.DEBUG):
		"""Returns True if we can be sure the package is installed.

		@param package:   Package as a string, eg 'wget'.
		@param shutit_pexpect_child:     See send()
		@param note:      See send()

		@rtype:           boolean
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session(package,note=note,loglevel=loglevel)


	def command_available(self,
	                      command,
	                      shutit_pexpect_child=None,
	                      note=None,
	                      loglevel=logging.DEBUG):
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.command_available(command,note=note,loglevel=loglevel)


	def is_shutit_installed(self,
	                        module_id,
	                        note=None,
	                        loglevel=logging.DEBUG):
		"""Helper proc to determine whether shutit has installed already here by placing a file in the db.

		@param module_id: Identifying string of shutit module
		@param note:      See send()
		"""
		shutit_pexpect_session = self.get_current_shutit_pexpect_session()
		return shutit_pexpect_session.is_shutit_installed(module_id,note=note,loglevel=loglevel)


	def ls(self,
	       directory,
	       note=None,
	       loglevel=logging.DEBUG):
		"""Helper proc to list files in a directory

		@param directory:   directory to list.  If the directory doesn't exist, shutit.fail() is called (i.e.  the build fails.)
		@param note:        See send()

		@type directory:    string

		@rtype:             list of strings
		"""
		shutit_pexpect_session = self.get_current_shutit_pexpect_session()
		return shutit_pexpect_session.is_shutit_installed(directory,note=note,loglevel=loglevel)


	def get_file(self,
	             target_path,
	             host_path,
	             note=None,
	             loglevel=logging.DEBUG):
		"""Copy a file from the target machine to the host machine

		@param target_path: path to file in the target
		@param host_path:   path to file on the host machine (e.g. copy test)
		@param note:        See send()

		@type target_path: string
		@type host_path:   string

		@return:           boolean
		@rtype:            string
		"""
		self.handle_note(note)
		# Only handle for docker initially, return false in case we care
		if self.build['delivery'] != 'docker':
			return False
		# on the host, run:
		#Usage:  docker cp [OPTIONS] CONTAINER:PATH LOCALPATH|-
		# Need: host env, container id, path from and path to
		shutit_pexpect_child     = self.get_shutit_pexpect_session_from_id('host_child').pexpect_child
		expect    = self.expect_prompts['ORIGIN_ENV']
		self.send('docker cp ' + self.target['container_id'] + ':' + target_path + ' ' + host_path,
		          shutit_pexpect_child=shutit_pexpect_child,
		          expect=expect,
		          check_exit=False,
		          echo=False,
		          loglevel=loglevel)
		self.handle_note_after(note=note)
		return True


	# TODO: should this be in global object?
	def prompt_cfg(self, msg, sec, name, ispass=False):
		"""Prompt for a config value, optionally saving it to the user-level
		cfg. Only runs if we are in an interactive mode.

		@param msg:    Message to display to user.
		@param sec:    Section of config to add to.
		@param name:   Config item name.
		@param ispass: If True, hide the input from the terminal.
		               Default: False.

		@type msg:     string
		@type sec:     string
		@type name:    string
		@type ispass:  boolean

		@return: the value entered by the user
		@rtype:  string
		"""
		cfgstr        = '[%s]/%s' % (sec, name)
		config_parser = self.config_parser
		usercfg       = os.path.join(self.host['shutit_path'], 'config')

		self.log(shutit_util.colourise('32', '\nPROMPTING FOR CONFIG: %s' % (cfgstr,)),transient=True)
		self.log(shutit_util.colourise('32', '\n' + msg + '\n'),transient=True)

		if not shutit_global.shutit_global_object.determine_interactive():
			self.fail('ShutIt is not in a terminal so cannot prompt for values.', throw_exception=False) # pragma: no cover

		if config_parser.has_option(sec, name):
			whereset = config_parser.whereset(sec, name)
			if usercfg == whereset:
				self.fail(cfgstr + ' has already been set in the user config, edit ' + usercfg + ' directly to change it', throw_exception=False) # pragma: no cover
			for subcp, filename, _ in reversed(config_parser.layers):
				# Is the config file loaded after the user config file?
				if filename == whereset:
					self.fail(cfgstr + ' is being set in ' + filename + ', unable to override on a user config level', throw_exception=False) # pragma: no cover
				elif filename == usercfg:
					break
		else:
			# The item is not currently set so we're fine to do so
			pass
		if ispass:
			val = getpass.getpass('>> ')
		else:
			val = self.util_raw_input(prompt='>> ')
		is_excluded = (
			config_parser.has_option('save_exclude', sec) and
			name in config_parser.get('save_exclude', sec).split()
		)
		# TODO: ideally we would remember the prompted config item for this invocation of shutit
		if not is_excluded:
			usercp = [
				subcp for subcp, filename, _ in config_parser.layers
				if filename == usercfg
			][0]
			if self.util_raw_input(prompt=shutit_util.colourise('32', 'Do you want to save this to your user settings? y/n: '),default='y') == 'y':
				sec_toset, name_toset, val_toset = sec, name, val
			else:
				# Never save it
				if config_parser.has_option('save_exclude', sec):
					excluded = config_parser.get('save_exclude', sec).split()
				else:
					excluded = []
				excluded.append(name)
				excluded = ' '.join(excluded)
				sec_toset, name_toset, val_toset = 'save_exclude', sec, excluded
			if not usercp.has_section(sec_toset):
				usercp.add_section(sec_toset)
			usercp.set(sec_toset, name_toset, val_toset)
			usercp.write(open(usercfg, 'w'))
			config_parser.reload()
		return val


	def step_through(self, msg='', shutit_pexpect_child=None, level=1, print_input=True, value=True):
		"""Implements a step-through function, using pause_point.
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		if (not shutit_global.shutit_global_object.determine_interactive() or not shutit_global.shutit_global_object.interactive or
			shutit_global.shutit_global_object.interactive < level):
			return
		self.build['step_through'] = value
		shutit_pexpect_session.pause_point(msg, print_input=print_input, level=level)
		return True


	def interact(self,
	            msg='SHUTIT PAUSE POINT',
	            shutit_pexpect_child=None,
	            print_input=True,
	            level=1,
	            resize=True,
	            colour='32',
	            default_msg=None,
	            wait=-1):
		"""Same as pause_point, but sets up the terminal ready for unmediated
		interaction."""
		self.pause_point(msg=msg,
		                 shutit_pexpect_child=shutit_pexpect_child,
		                 print_input=print_input,
		                 level=level,
		                 resize=resize,
		                 colour=colour,
		                 default_msg=default_msg,
		                 interact=True,
		                 wait=wait)


	def pause_point(self,
	                msg='SHUTIT PAUSE POINT',
	                shutit_pexpect_child=None,
	                print_input=True,
	                level=1,
	                resize=True,
	                colour='32',
	                default_msg=None,
	                interact=False,
	                wait=-1):
		"""Inserts a pause in the build session, which allows the user to try
		things out before continuing. Ignored if we are not in an interactive
		mode, or the interactive level is less than the passed-in one.
		Designed to help debug the build, or drop to on failure so the
		situation can be debugged.

		@param msg:          Message to display to user on pause point.
		@param shutit_pexpect_child:        See send()
		@param print_input:  Whether to take input at this point (i.e. interact), or
		                     simply pause pending any input.
		                     Default: True
		@param level:        Minimum level to invoke the pause_point at.
		                     Default: 1
		@param resize:       If True, try to resize terminal.
		                     Default: False
		@param colour:       Colour to print message (typically 31 for red, 32 for green)
		@param default_msg:  Whether to print the standard blurb
		@param wait:         Wait a few seconds rather than for input

		@type msg:           string
		@type print_input:   boolean
		@type level:         integer
		@type resize:        boolean
		@type wait:          decimal

		@return:             True if pause point handled ok, else false
		"""
		if (not shutit_global.shutit_global_object.determine_interactive() or shutit_global.shutit_global_object.interactive < 1 or
			shutit_global.shutit_global_object.interactive < level):
			return
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		if shutit_pexpect_child:
			shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
			shutit_pexpect_session.pause_point(msg=msg,print_input=print_input,resize=resize,colour=colour,default_msg=default_msg,wait=wait,interact=interact)
		else:
			self.log(msg,level=logging.DEBUG)
			self.log('Nothing to interact with, so quitting to presumably the original shell',level=logging.DEBUG)
			self.handle_exit(exit_code=1)
		self.build['ctrlc_stop'] = False
		return True



	def send_and_match_output(self,
	                          send,
	                          matches,
	                          shutit_pexpect_child=None,
	                          retry=3,
	                          strip=True,
	                          note=None,
	                          echo=None,
	                          loglevel=logging.DEBUG):
		"""Returns true if the output of the command matches any of the strings in
		the matches list of regexp strings. Handles matching on a per-line basis
		and does not cross lines.

		@param send:     See send()
		@param matches:  String - or list of strings - of regexp(s) to check
		@param shutit_pexpect_child:    See send()
		@param retry:    Number of times to retry command (default 3)
		@param strip:    Whether to strip output (defaults to True)
		@param note:     See send()

		@type send:      string
		@type matches:   list
		@type retry:     integer
		@type strip:     boolean
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.send_and_match_output(send,
		                                                    matches,
		                                                    retry=retry,
		                                                    strip=strip,
		                                                    note=note,
		                                                    echo=echo,
		                                                    loglevel=loglevel)


	def send_and_get_output(self,
	                        send,
	                        shutit_pexpect_child=None,
	                        timeout=None,
	                        retry=3,
	                        strip=True,
	                        preserve_newline=False,
	                        note=None,
	                        record_command=False,
	                        echo=None,
	                        fail_on_empty_before=True,
	                        nonewline=False,
	                        loglevel=logging.DEBUG):
		"""Returns the output of a command run. send() is called, and exit is not checked.

		@param send:     See send()
		@param shutit_pexpect_child:    See send()
		@param retry:    Number of times to retry command (default 3)
		@param strip:    Whether to strip output (defaults to True). Strips whitespace
		                 and ansi terminal codes
		@param note:     See send()
		@param echo:     See send()

		@type retry:     integer
		@type strip:     boolean
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.send_and_get_output(send,
		                                                  timeout=timeout,
		                                                  retry=retry,
		                                                  strip=strip,
		                                                  preserve_newline=preserve_newline,
		                                                  note=note,
		                                                  record_command=record_command,
		                                                  echo=echo,
		                                                  fail_on_empty_before=fail_on_empty_before,
		                                                  nonewline=nonewline,
		                                                  loglevel=loglevel)


	def install(self,
	            package,
	            shutit_pexpect_child=None,
	            options=None,
	            timeout=3600,
	            force=False,
	            check_exit=True,
	            reinstall=False,
	            note=None,
	            loglevel=logging.INFO):
		"""Distro-independent install function.
		Takes a package name and runs the relevant install function.

		@param package:    Package to install, which is run through package_map
		@param shutit_pexpect_child:      See send()
		@param timeout:    Timeout (s) to wait for finish of install. Defaults to 3600.
		@param options:    Dictionary for specific options per install tool.
		                   Overrides any arguments passed into this function.
		@param force:      Force if necessary. Defaults to False
		@param check_exit: If False, failure to install is ok (default True)
		@param reinstall:  Advise a reinstall where possible (default False)
		@param note:       See send()

		@type package:     string
		@type timeout:     integer
		@type options:     dict
		@type force:       boolean
		@type check_exit:  boolean
		@type reinstall:   boolean

		@return: True if all ok (ie it's installed), else False.
		@rtype: boolean
		"""
		# If separated by spaces, install separately
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.install(package,
		                                      options=options,
		                                      timeout=timeout,
		                                      force=force,
		                                      check_exit=check_exit,
		                                      reinstall=reinstall,
		                                      note=note,
		                                      loglevel=loglevel)


	def remove(self,
	           package,
	           shutit_pexpect_child=None,
	           options=None,
	           timeout=3600,
	           note=None):
		"""Distro-independent remove function.
		Takes a package name and runs relevant remove function.

		@param package:  Package to remove, which is run through package_map.
		@param shutit_pexpect_child:    See send()
		@param options:  Dict of options to pass to the remove command,
		                 mapped by install_type.
		@param timeout:  See send(). Default: 3600
		@param note:     See send()

		@return: True if all ok (i.e. the package was successfully removed),
		         False otherwise.
		@rtype: boolean
		"""
		# If separated by spaces, remove separately
		if package.find(' ') != -1:
			for p in package.split(' '):
				self.install(p,shutit_pexpect_child=shutit_pexpect_child,options=options,timeout=timeout,note=note)
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.remove(package,
		                                     options=options,
		                                     timeout=timeout,
		                                     note=note)


	def get_env_pass(self,
	                 user=None,
	                 msg=None,
	                 shutit_pexpect_child=None,
	                 note=None):
		"""Gets a password from the user if one is not already recorded for this environment.

		@param user:    username we are getting password for
		@param msg:     message to put out there
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.get_env_pass(user=user,
		                                           msg=msg,
		                                           note=note)


	def whoarewe(self,
	             shutit_pexpect_child=None,
	             note=None,
	             loglevel=logging.DEBUG):
		"""Returns the current group.

		@param shutit_pexpect_child:    See send()
		@param note:     See send()

		@return: the first group found
		@rtype: string
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.whoarewe(note=note,
		                                       loglevel=loglevel)


	def login(self,
	          command='su -',
	          user=None,
	          password=None,
	          prompt_prefix=None,
	          expect=None,
	          timeout=180,
	          escape=False,
	          echo=None,
	          note=None,
	          go_home=True,
	          fail_on_fail=True,
	          is_ssh=True,
	          loglevel=logging.DEBUG):
		"""Logs user in on default child.
		"""
		shutit_pexpect_session = self.get_current_shutit_pexpect_session()
		#print('class command: ' + str(command))
		#print('class password: ' + str(password))
		return shutit_pexpect_session.login(ShutItSendSpec(shutit_pexpect_session,user=user,
		                                                   send=command,
		                                                   password=password,
		                                                   prompt_prefix=prompt_prefix,
		                                                   expect=expect,
		                                                   timeout=timeout,
		                                                   escape=escape,
		                                                   echo=echo,
		                                                   note=note,
		                                                   go_home=go_home,
		                                                   fail_on_fail=fail_on_fail,
		                                                   is_ssh=is_ssh,
		                                                   loglevel=loglevel))


	def logout(self,
	           command='exit',
	           note=None,
	           echo=None,
	           timeout=300,
	           nonewline=False,
	           loglevel=logging.DEBUG):
		"""Logs the user out. Assumes that login has been called.
		If login has never been called, throw an error.

			@param command:         Command to run to log out (default=exit)
			@param note:            See send()
		"""
		shutit_pexpect_session = self.get_current_shutit_pexpect_session()
		return shutit_pexpect_session.logout(ShutItSendSpec(shutit_pexpect_session,send=command,
		                                                    note=note,
		                                                    timeout=timeout,
		                                                    nonewline=nonewline,
		                                                    loglevel=loglevel,
		                                                    echo=echo))
	exit_shell = logout


	def wait(self, cadence=2):
		shutit_pexpect_session = self.get_current_shutit_pexpect_session()
		return shutit_pexpect_session.wait(cadence=cadence)



	def get_memory(self,
	               shutit_pexpect_child=None,
	               note=None):
		"""Returns memory available for use in k as an int"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.get_memory(note=note)


	def get_distro_info(self,
	                    shutit_pexpect_child=None,
	                    loglevel=logging.DEBUG):
		"""Get information about which distro we are using, placing it in the environment object.

		Fails if distro could not be determined.
		Should be called with the container is started up, and uses as core info
		as possible.

		Note: if the install type is apt, it issues the following:
		    - apt-get update
		    - apt-get install -y -qq lsb-release

		@param shutit_pexpect_child:       See send()
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.get_distro_info(loglevel=loglevel)


	def lsb_release(self,
	                shutit_pexpect_child=None,
	                loglevel=logging.DEBUG):
		"""Get distro information from lsb_release.
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.lsb_release(loglevel=loglevel)


	def set_password(self,
	                 password,
	                 user='',
	                 shutit_pexpect_child=None,
	                 note=None):
		"""Sets the password for the current user or passed-in user.

		As a side effect, installs the "password" package.

		@param user:        username to set the password for. Defaults to '' (i.e. current user)
		@param password:    password to set for the user
		@param shutit_pexpect_child:       See send()
		@param note:        See send()
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.set_password(password,user=user,note=note)


	def whoami(self,
	           note=None,
	           shutit_pexpect_child=None,
	           loglevel=logging.DEBUG):
		"""Returns the current user by executing "whoami".

		@param note:     See send()

		@return: the output of "whoami"
		@rtype: string
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.whoami(note=note,loglevel=loglevel)


	def is_user_id_available(self,
	                         user_id,
	                         shutit_pexpect_child=None,
	                         note=None,
	                         loglevel=logging.DEBUG):
		"""Determine whether the specified user_id available.

		@param user_id:  User id to be checked.
		@param shutit_pexpect_child:    See send()
		@param note:     See send()

		@type user_id:   integer

		@rtype:          boolean
		@return:         True is the specified user id is not used yet, False if it's already been assigned to a user.
		"""
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		shutit_pexpect_session = self.get_shutit_pexpect_session_from_child(shutit_pexpect_child)
		return shutit_pexpect_session.is_user_id_available(user_id,
		                                                   note=note,
		                                                   loglevel=loglevel)


	def push_repository(self,
	                    repository,
	                    docker_executable='docker',
	                    shutit_pexpect_child=None,
	                    expect=None,
	                    note=None,
	                    loglevel=logging.INFO):
		"""Pushes the repository.

		@param repository:          Repository to push.
		@param docker_executable:   Defaults to 'docker'
		@param expect:              See send()
		@param shutit_pexpect_child:               See send()

		@type repository:           string
		@type docker_executable:    string
		"""
		self.handle_note(note)
		shutit_pexpect_child = shutit_pexpect_child or self.get_shutit_pexpect_session_from_id('host_child').pexpect_child
		expect               = expect or self.expect_prompts['ORIGIN_ENV']
		send                 = docker_executable + ' push ' + self.repository['user'] + '/' + repository
		timeout              = 99999
		self.log('Running: ' + send,level=logging.INFO)
		self.multisend(docker_executable + ' login',
		               {'Username':self.repository['user'], 'Password':self.repository['password'], 'Email':self.repository['email']},
		               shutit_pexpect_child=shutit_pexpect_child,
		               expect=expect)
		self.send(send,
		          shutit_pexpect_child=shutit_pexpect_child,
		          expect=expect,
		          timeout=timeout,
		          check_exit=False,
		          fail_on_empty_before=False,
		          loglevel=loglevel)
		self.handle_note_after(note)
		return True



	def do_repository_work(self,
	                       repo_name,
	                       repo_tag=None,
	                       docker_executable='docker',
	                       password=None,
	                       force=None,
	                       loglevel=logging.DEBUG,
	                       note=None,
	                       tag=None,
	                       push=None,
	                       export=None,
	                       save=None):
		"""Commit, tag, push, tar a docker container based on the configuration we have.

		@param repo_name:           Name of the repository.
		@param docker_executable:   Defaults to 'docker'
		@param password:
		@param force:

		@type repo_name:            string
		@type docker_executable:    string
		@type password:             string
		@type force:                boolean
		"""
		# TODO: make host and client configurable
		self.handle_note(note)
		shutit_pexpect_session = self.get_current_shutit_pexpect_session()
		if tag is None:
			tag    = self.repository['tag']
		if push is None:
			push   = self.repository['push']
		if export is None:
			export = self.repository['export']
		if save is None:
			save   = self.repository['save']
		if not (push or export or save or tag):
			# If we're forcing this, then tag as a minimum
			if force:
				tag = True
			else:
				return True

		shutit_pexpect_child = self.get_shutit_pexpect_session_from_id('host_child').pexpect_child
		expect    = self.expect_prompts['ORIGIN_ENV']
		server    = self.repository['server']
		repo_user = self.repository['user']
		if repo_tag is None:
			repo_tag  = self.repository['tag_name']

		if repo_user and repo_name:
			repository = '%s/%s' % (repo_user, repo_name)
			repository_tar = '%s%s' % (repo_user, repo_name)
		elif repo_user:
			repository = repository_tar = repo_user
		elif repo_name:
			repository = repository_tar = repo_name
		else:
			repository = repository_tar = ''

		if not repository:
			self.fail('Could not form valid repository name', shutit_pexpect_child=shutit_pexpect_child, throw_exception=False) # pragma: no cover
		if (export or save) and not repository_tar:
			self.fail('Could not form valid tar name', shutit_pexpect_child=shutit_pexpect_child, throw_exception=False) # pragma: no cover

		if server != '':
			repository = '%s/%s' % (server, repository)

		if self.build['deps_only']:
			repo_tag += '_deps'

		if self.repository['suffix_date']:
			suffix_date = time.strftime(self.repository['suffix_format'])
			repository = '%s%s' % (repository, suffix_date)
			repository_tar = '%s%s' % (repository_tar, suffix_date)

		if repository != '' and len(repository.split(':')) > 1:
			repository_with_tag = repository
			repo_tag = repository.split(':')[1]
		elif repository != '':
			repository_with_tag = repository + ':' + repo_tag

		# Commit image
		# Only lower case accepted
		repository          = repository.lower()
		repository_with_tag = repository_with_tag.lower()

		if server == '' and len(repository) > 30 and push:
			self.fail("""repository name: '""" + repository + """' too long to push. If using suffix_date consider shortening, or consider adding "-s repository push no" to your arguments to prevent pushing.""", shutit_pexpect_child=shutit_pexpect_child, throw_exception=False) # pragma: no cover

		if self.send(docker_executable + ' commit ' + self.target['container_id'] + ' ' + repository_with_tag,
		             expect=[expect,' assword'],
		             shutit_pexpect_child=shutit_pexpect_child,
		             timeout=99999,
		             check_exit=False,
		             loglevel=loglevel) == 1:
			self.send(self.host['password'],
			          expect=expect,
			          check_exit=False,
			          record_command=False,
			          shutit_pexpect_child=shutit_pexpect_child,
			          echo=False,
			          loglevel=loglevel)
		# Tag image, force it by default
		self.build['report'] += '\nBuild tagged as: ' + repository_with_tag
		if export or save:
			shutit_pexpect_session.pause_point('We are now exporting the container to a bzipped tar file, as configured in\n[repository]\ntar:yes', print_input=False, level=3)
			if export:
				bzfile = (repository_tar + 'export.tar.bz2')
				self.log('Depositing bzip2 of exported container into ' + bzfile,level=logging.DEBUG)
				if self.send(docker_executable + ' export ' + self.target['container_id'] + ' | bzip2 - > ' + bzfile,
				             expect=[expect, 'assword'],
				             timeout=99999,
				             shutit_pexpect_child=shutit_pexpect_child,
				             loglevel=loglevel) == 1:
					self.send(password,
					          expect=expect,
					          shutit_pexpect_child=shutit_pexpect_child,
					          loglevel=loglevel)
				self.log('Deposited bzip2 of exported container into ' + bzfile, level=loglevel)
				self.log('Run: bunzip2 -c ' + bzfile + ' | sudo docker import - to get this imported into docker.', level=logging.DEBUG)
				self.build['report'] += ('\nDeposited bzip2 of exported container into ' + bzfile)
				self.build['report'] += ('\nRun:\n\nbunzip2 -c ' + bzfile + ' | sudo docker import -\n\nto get this imported into docker.')
			if save:
				bzfile = (repository_tar + 'save.tar.bz2')
				self.log('Depositing bzip2 of exported container into ' + bzfile,level=logging.DEBUG)
				if self.send(docker_executable + ' save ' + self.target['container_id'] + ' | bzip2 - > ' + bzfile,
				             expect=[expect, 'assword'],
				             timeout=99999,
				             shutit_pexpect_child=shutit_pexpect_child,
				             loglevel=loglevel) == 1:
					self.send(password,
					          expect=expect,
					          shutit_pexpect_child=shutit_pexpect_child,
					          loglevel=loglevel)
				self.log('Deposited bzip2 of exported container into ' + bzfile, level=logging.DEBUG)
				self.log('Run: bunzip2 -c ' + bzfile + ' | sudo docker import - to get this imported into docker.', level=logging.DEBUG)
				self.build['report'] += ('\nDeposited bzip2 of exported container into ' + bzfile)
				self.build['report'] += ('\nRun:\n\nbunzip2 -c ' + bzfile + ' | sudo docker import -\n\nto get this imported into docker.')
		if self.repository['push']:
			# Pass the child explicitly as it's the host child.
			self.push_repository(repository, docker_executable=docker_executable, expect=expect, shutit_pexpect_child=shutit_pexpect_child)
			self.build['report'] = (self.build['report'] + '\nPushed repository: ' + repository)
		self.handle_note_after(note)
		return True




	def get_config(self,
	               module_id,
	               option,
	               default=None,
	               boolean=False,
	               secret=False,
	               forcedefault=False,
	               forcenone=False,
	               hint=None):
		"""Gets a specific config from the config files, allowing for a default.

		Handles booleans vs strings appropriately.

		@param module_id:    module id this relates to, eg com.mycorp.mymodule.mymodule
		@param option:       config item to set
		@param default:      default value if not set in files
		@param boolean:      whether this is a boolean value or not (default False)
		@param secret:       whether the config item is a secret
		@param forcedefault: if set to true, allows you to override any value already set (default False)
		@param forcenone:    if set to true, allows you to set the value to None (default False)
		@param hint:         if we are interactive, then show this prompt to help the user input a useful value

		@type module_id:     string
		@type option:        string
		@type default:       string
		@type boolean:       boolean
		@type secret:        boolean
		@type forcedefault:  boolean
		@type forcenone:     boolean
		@type hint:          string
		"""
		cfg = self.cfg
		if module_id not in cfg.keys():
			cfg[module_id] = {}
		if not self.config_parser.has_section(module_id):
			self.config_parser.add_section(module_id)
		if not forcedefault and self.config_parser.has_option(module_id, option):
			if boolean:
				cfg[module_id][option] = self.config_parser.getboolean(module_id, option)
			else:
				cfg[module_id][option] = self.config_parser.get(module_id, option)
		else:
			if not forcenone:
				if shutit_global.shutit_global_object.interactive > 0:
					if self.build['accept_defaults'] is None:
						answer = None
						# util_raw_input may change the interactive level, so guard for this.
						while answer not in ('yes','no','') and shutit_global.shutit_global_object.interactive > 1:
							answer = self.util_raw_input(prompt=shutit_util.colourise('32', 'Do you want to accept the config option defaults? ' + '(boolean - input "yes" or "no") (default: yes): \n'),default='yes',ispass=secret)
						# util_raw_input may change the interactive level, so guard for this.
						self.build['accept_defaults'] = answer in ('yes','') or shutit_global.shutit_global_object.interactive < 2
					if self.build['accept_defaults'] and default != None:
						cfg[module_id][option] = default
					else:
						# util_raw_input may change the interactive level, so guard for this.
						if shutit_global.shutit_global_object.interactive < 1:
							self.fail('Cannot continue. ' + module_id + '.' + option + ' config requires a value and no default is supplied. Adding "-s ' + module_id + ' ' + option + ' [your desired value]" to the shutit invocation will set this.') # pragma: no cover
						prompt = '\n\nPlease input a value for ' + module_id + '.' + option
						if default != None:
							prompt = prompt + ' (default: ' + str(default) + ')'
						if hint != None:
							prompt = prompt + '\n\n' + hint
						answer = None
						if boolean:
							while answer not in ('yes','no'):
								answer =  self.util_raw_input(prompt=shutit_util.colourise('32',prompt + ' (boolean - input "yes" or "no"): \n'),ispass=secret)
							if answer == 'yes':
								answer = True
							elif answer == 'no':
								answer = False
						else:
							if re.search('assw',option) is None:
								answer =  self.util_raw_input(prompt=shutit_util.colourise('32',prompt) + ': \n',ispass=secret)
							else:
								answer =  self.util_raw_input(ispass=True,prompt=shutit_util.colourise('32',prompt) + ': \n')
						if answer == '' and default != None:
							answer = default
						cfg[module_id][option] = answer
				else:
					if default != None:
						cfg[module_id][option] = default
					else:
						self.fail('Config item: ' + option + ':\nin module:\n[' + module_id + ']\nmust be set!\n\nOften this is a deliberate requirement to place in your ~/.shutit/config file, or you can pass in with:\n\n-s ' + module_id + ' ' + option + ' yourvalue\n\nto the build command', throw_exception=False) # pragma: no cover
			else:
				cfg[module_id][option] = default
		return True


	def begin_asciinema_session(self,
	                            title=None,
	                            max_pause=None,
	                            filename=None,
	                            shutit_pexpect_child=None):
		assert self.build['asciinema_session'] is None
		self.build['asciinema_session'] = True
		self.build['asciinema_session_file'] = False
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		if not self.command_available('asciinema'):
			self.install('asciinema')
		version = self.send_and_get_output("""asciinema --version | awk '{print $2}'""")
		if max_pause:
			max_pause_str = ' -w ' + str(max_pause)
		else:
			max_pause_str = ' -w 5.0'
		opts = '-y'
		if title:
			opts += ' -t "' + str(title) + '"'
		if version < '1.3':
			self.login(command='asciinema rec ' + opts, go_home=False)
		elif filename != None:
			self.login(command='asciinema rec ' + opts + ' ' + max_pause_str + ' ' + filename, go_home=False)
		else:
			self.login(command='asciinema rec ' + opts + ' ' + max_pause_str, go_home=False)
		return True


	def end_asciinema_session(self,
	                          shutit_pexpect_child=None):
		assert self.build['asciinema_session'] is True
		shutit_pexpect_child = shutit_pexpect_child or self.get_current_shutit_pexpect_session().pexpect_child
		output = self.logout(timeout=3000)
		self.log(output,add_final_message=True)
		self.build['asciinema_session'] = None
		self.build['asciinema_session_file'] = None
		return True


	def get_emailer(self, cfg_section):
		"""Sends an email using the mailer
		"""
		import emailer
		return emailer.Emailer(cfg_section, self)


	# eg sys.stdout or None
	def divert_output(self, output):
		for key in self.shutit_pexpect_sessions:
			self.shutit_pexpect_sessions[key].pexpect_child.logfile_send = output
			self.shutit_pexpect_sessions[key].pexpect_child.logfile_read = output
		return True


	def add_shutit_pexpect_session(self, shutit_pexpect_child):
		pexpect_session_id = shutit_pexpect_child.pexpect_session_id
		# Check id is unique
		if self.shutit_pexpect_sessions.has_key(pexpect_session_id) and self.shutit_pexpect_sessions[pexpect_session_id] != shutit_pexpect_child:
			self.fail('shutit_pexpect_child already added and differs from passed-in object',throw_exception=True) # pragma: no cover
		return self.shutit_pexpect_sessions.update({pexpect_session_id:shutit_pexpect_child})


	def remove_shutit_pexpect_session(self, shutit_pexpect_session_id=None, shutit_pexpect_child=None):
		if shutit_pexpect_session_id is None and shutit_pexpect_child is None:
			self.fail('Must pass value into remove_pexpect_child.',throw_exception=True) # pragma: no cover
		if shutit_pexpect_session_id is None:
			shutit_pexpect_session_id = shutit_pexpect_child.pexpect_session_id
		del self.shutit_pexpect_sessions[shutit_pexpect_session_id]
		return True


	def get_shutit_pexpect_session_from_child(self, shutit_pexpect_child):
		"""Given a pexpect/child object, return the shutit_pexpect_session object.
		"""
		if not isinstance(shutit_pexpect_child, pexpect.pty_spawn.spawn):
			self.fail('Wrong type in get_shutit_pexpect_session_child: ' + str(type(shutit_pexpect_child)),throw_exception=True) # pragma: no cover
		for key in self.shutit_pexpect_sessions:
			if self.shutit_pexpect_sessions[key].pexpect_child == shutit_pexpect_child:
				return self.shutit_pexpect_sessions[key]
		return self.fail('Should not get here in get_shutit_pexpect_session',throw_exception=True) # pragma: no cover


	def get_shutit_pexpect_session_id(self, shutit_pexpect_child):
		"""Given a pexpect child object, return the shutit_pexpect_session_id object.
		"""
		if not isinstance(shutit_pexpect_child, pexpect.pty_spawn.spawn):
			self.fail('Wrong type in get_shutit_pexpect_session_id',throw_exception=True) # pragma: no cover
		for key in self.shutit_pexpect_sessions:
			if self.shutit_pexpect_sessions[key].pexpect_child == shutit_pexpect_child:
				return key
		return self.fail('Should not get here in get_shutit_pexpect_session_id',throw_exception=True) # pragma: no cover


	def get_shutit_pexpect_session_from_id(self, shutit_pexpect_id):
		"""Get the pexpect session from the given identifier.
		"""
		for key in self.shutit_pexpect_sessions:
			if self.shutit_pexpect_sessions[key].pexpect_session_id == shutit_pexpect_id:
				return self.shutit_pexpect_sessions[key]
		return self.fail('Should not get here in get_shutit_pexpect_session_from_id',throw_exception=True) # pragma: no cover


	def print_session_state(self):
		ret = '\n'
		for key in self.shutit_pexpect_sessions:
			ret += '===============================================================================\n'
			session_id = self.shutit_pexpect_sessions[key].pexpect_session_id
			session = self.shutit_pexpect_sessions[key]
			ret += 'KEY:                 ' + key + '\n'
			ret += 'SESSION_ID:          ' + session_id + '\n'
			ret += 'SESSION:             ' + str(session) + '\n'
			ret += 'DEFAULT_EXP:         ' + session.default_expect + '\n'
			ret += 'LOGIN_STACK:         ' + str(session.login_stack) + '\n'
			ret += 'CURRENT_ENVIRONMENT: ' + str(session.current_environment) + '\n'
			ret += '===============================================================================\n'
		return ret


	# Pass through to global object
	def create_session(self, session_type='bash', docker_image=None, rm=None):
		return shutit_global.shutit_global_object.create_session(session_type=session_type, docker_image=docker_image, rm=rm)


	# TODO: walkthrough and exam at global level? but see handle_note - looks like that is shutit-specific
	# given a shutit object and an echo value, return the appropriate echo
	# value for the given context.
	def get_echo_override(self, echo):
		if self.build['always_echo'] is True:
			echo = True
		# Should we echo the output?
		if echo is None and shutit_global.shutit_global_object.loglevel <= logging.DEBUG:
			# Yes if it's in debug
			echo = True
		if echo is None and self.build['walkthrough']:
			# Yes if it's in walkthrough and was not explicitly passed in
			echo = True
		if echo is None:
			# No if it was not explicitly passed in
			echo = False
		if self.build['exam']:
			# No if we are in exam mode
			echo = False
		return echo


	# Pass through log to global function.
	def log(self, msg, add_final_message=False, level=logging.INFO, transient=False, newline=True):
		shutit_global.shutit_global_object.log(msg,add_final_message=add_final_message,level=level,transient=transient,newline=newline)


	def check_sudo(self, shutit_pexpect_session=None):
		shutit_pexpect_session = shutit_pexpect_session or self.get_current_shutit_pexpect_session()
		return shutit_pexpect_session.check_sudo()


	def get_exit_value(self, shutit_pexpect_session=None):
		shutit_pexpect_session = shutit_pexpect_session or self.get_current_shutit_pexpect_session()
		return shutit_pexpect_session.get_exit_value(self)


	def get_sudo_pass_if_needed(self, shutit, ignore_brew=False):
		shutit_pexpect_session = self.get_current_shutit_pexpect_session()
		return shutit_pexpect_session.get_sudo_pass_if_needed(shutit, ignore_brew=ignore_brew)


	def get_commands(self):
		"""Gets command that have been run and have not been redacted.
		"""
		s = ''
		for c in self.build['shutit_command_history']:
			if isinstance(c, str):
				#Ignore commands with leading spaces
				if c and c[0] != ' ':
					s += c + '\n'
		return s


	# Build report
	def build_report(self, msg=''):
		"""Resposible for constructing a report to be output as part of the build.
		Returns report as a string.
		"""
		s = '\n'
		s += '################################################################################\n'
		s += '# COMMAND HISTORY BEGIN ' + shutit_global.shutit_global_object.build_id + '\n'
		s += self.get_commands()
		s += '# COMMAND HISTORY END ' + shutit_global.shutit_global_object.build_id + '\n'
		s += '################################################################################\n'
		s += '################################################################################\n'
		s += '# BUILD REPORT FOR BUILD BEGIN ' + shutit_global.shutit_global_object.build_id + '\n'
		s += '# ' + msg + '\n'
		if self.build['report'] != '':
			s += self.build['report'] + '\n'
		else:
			s += '# Nothing to report\n'
		if 'container_id' in self.target:
			s += '# CONTAINER_ID: ' + self.target['container_id'] + '\n'
		s += '# BUILD REPORT FOR BUILD END ' + shutit_global.shutit_global_object.build_id + '\n'
		s += '###############################################################################\n'
		return s


	def util_raw_input(self, prompt='', default=None, ispass=False, use_readline=True):
		"""Handles raw_input calls, and switches off interactivity if there is apparently
		no controlling terminal (or there are any other problems)
		"""
		if use_readline:
			try:
				readline.read_init_file('/etc/inputrc')
			except:
				pass
			readline.parse_and_bind('tab: complete')
		prompt = '\r\n' + prompt
		if ispass:
			prompt += '\r\nInput Secret: '
		shutit_util.sanitize_terminal()
		if shutit_global.shutit_global_object.interactive == 0:
			return default
		if not shutit_global.shutit_global_object.determine_interactive():
			return default
		while True:
			try:
				if ispass:
					return getpass.getpass(prompt=prompt)
				else:
					resp = raw_input(prompt).strip()
					if resp == '':
						return default
					else:
						return resp
			except KeyboardInterrupt:
				continue
			except:
				msg = 'Problems getting raw input, assuming no controlling terminal.'
		if ispass:
			return getpass.getpass(prompt=prompt)
		else:
			resp = raw_input(prompt).strip()
			if resp == '':
				return default
			else:
				return resp
		shutit_global.shutit_global_object.set_noninteractive(msg=msg)
		return default



	def match_string(self, string_to_match, regexp):
		"""Get regular expression from the first of the lines passed
		in in string that matched. Handles first group of regexp as
		a return value.

		@param string_to_match: String to match on
		@param regexp: Regexp to check (per-line) against string

		@type string_to_match: string
		@type regexp: string

		Returns None if none of the lines matched.

		Returns True if there are no groups selected in the regexp.
		else returns matching group (ie non-None)
		"""
		if not isinstance(string_to_match, str):
			return None
		lines = string_to_match.split('\r\n')
		# sometimes they're separated by just a carriage return...
		new_lines = []
		for line in lines:
			new_lines = new_lines + line.split('\r')
		# and sometimes they're separated by just a newline...
		for line in lines:
			new_lines = new_lines + line.split('\n')
		lines = new_lines
		if not shutit_util.check_regexp(regexp):
			self.fail('Illegal regexp found in match_string call: ' + regexp) # pragma: no cover
		for line in lines:
			match = re.match(regexp, line)
			if match is not None:
				if len(match.groups()) > 0:
					return match.group(1)
				else:
					return True
		return None


	def module_ids(self, rev=False):
		"""Gets a list of module ids guaranteed to be sorted by run_order, ignoring conn modules
		(run order < 0).
		"""
		ids = sorted(list(self.shutit_map.keys()),key=lambda module_id: self.shutit_map[module_id].run_order)
		if rev:
			return list(reversed(ids))
		else:
			return ids


	def is_to_be_built_or_is_installed(self, shutit_module_obj):
		"""Returns true if this module is configured to be built, or if it is already installed.
		"""
		cfg = self.cfg
		if cfg[shutit_module_obj.module_id]['shutit.core.module.build']:
			return True
		return self.is_installed(shutit_module_obj)


	def is_installed(self, shutit_module_obj):
		"""Returns true if this module is installed.
		Uses cache where possible.
		"""
		# Cache first
		if shutit_module_obj.module_id in self.get_current_shutit_pexpect_session_environment().modules_installed:
			return True
		if shutit_module_obj.module_id in self.get_current_shutit_pexpect_session_environment().modules_not_installed:
			return False
		# Is it installed?
		if shutit_module_obj.is_installed(self):
			self.get_current_shutit_pexpect_session_environment().modules_installed.append(shutit_module_obj.module_id)
			return True
		# If not installed, and not in cache, add it.
		else:
			if shutit_module_obj.module_id not in self.get_current_shutit_pexpect_session_environment().modules_not_installed:
				self.get_current_shutit_pexpect_session_environment().modules_not_installed.append(shutit_module_obj.module_id)
			return False



	def determine_compatibility(self, module_id):
		cfg = self.cfg
		# Allowed images
		if (cfg[module_id]['shutit.core.module.allowed_images'] and self.target['docker_image'] not in cfg[module_id]['shutit.core.module.allowed_images']) and not self.allowed_image(module_id):
			return 1
		# Build methods
		if cfg[module_id]['shutit.core.module.build'] and self.build['delivery'] not in self.shutit_map[module_id].ok_delivery_methods:
			return 2
		return 0


	def allowed_image(self, module_id):
		"""Given a module id, determine whether the image is allowed to be built.
		"""
		self.log("In allowed_image: " + module_id,level=logging.DEBUG)
		cfg = self.cfg
		if self.build['ignoreimage']:
			self.log("ignoreimage == true, returning true" + module_id,level=logging.DEBUG)
			return True
		self.log(str(cfg[module_id]['shutit.core.module.allowed_images']),level=logging.DEBUG)
		if cfg[module_id]['shutit.core.module.allowed_images']:
			# Try allowed images as regexps
			for regexp in cfg[module_id]['shutit.core.module.allowed_images']:
				if not shutit_util.check_regexp(regexp):
					self.fail('Illegal regexp found in allowed_images: ' + regexp) # pragma: no cover
				if re.match('^' + regexp + '$', self.target['docker_image']):
					return True
		return False


	def print_modules(self):
		"""Returns a string table representing the modules in the ShutIt module map.
		"""
		cfg = self.cfg
		module_string = ''
		module_string += 'Modules: \n'
		module_string += '    Run order    Build    Remove    Module ID\n'
		for module_id in self.module_ids():
			module_string += '    ' + str(self.shutit_map[module_id].run_order) + '        ' + str(
				cfg[module_id]['shutit.core.module.build']) + '    ' + str(
				cfg[module_id]['shutit.core.module.remove']) + '    ' + module_id + '\n'
		return module_string


	def load_shutit_modules(self):
		"""Responsible for loading the shutit modules based on the configured module
		paths.
		"""
		if shutit_global.shutit_global_object.loglevel <= logging.DEBUG:
			self.log('ShutIt module paths now: ',level=logging.DEBUG)
			self.log(self.host['shutit_module_path'],level=logging.DEBUG)
		for shutit_module_path in self.host['shutit_module_path']:
			self.load_all_from_path(shutit_module_path)


	def get_command(self, command):
		"""Helper function for osx - return gnu utils rather than default for
		   eg head and md5sum where possible.
		"""
		if command in ('head','md5sum'):
			if self.get_current_shutit_pexpect_session_environment().distro == 'osx':
				return '''PATH="/usr/local/opt/coreutils/libexec/gnubin:$PATH" ''' + command + ' '
			else:
				return command + ' '
		return command


	def get_send_command(self, send):
		"""Internal helper function to get command that's really sent
		"""
		if send is None:
			return send
		cmd_arr = send.split()
		if len(cmd_arr) and cmd_arr[0] in ('md5sum','sed','head'):
			newcmd = self.get_command(cmd_arr[0])
			send = send.replace(cmd_arr[0],newcmd)
		return send



	def get_input(self, msg, default='', valid=None, boolean=False, ispass=False, colour='32'):
		"""Gets input from the user, and returns the answer.

		@param msg:       message to send to user
		@param default:   default value if nothing entered
		@param valid:     valid input values (default == empty list == anything allowed)
		@param boolean:   whether return value should be boolean
		@param ispass:    True if this is a password (ie whether to not echo input)
		"""
		if boolean and valid is None:
			valid = ('yes','y','Y','1','true','no','n','N','0','false')
		answer = self.util_raw_input(prompt=shutit_util.colourise(colour,msg),ispass=ispass)
		if boolean and answer in ('', None) and default != '':
			return default
		if valid is not None:
			while answer not in valid:
				self.log('Answer must be one of: ' + str(valid),transient=True)
				answer = self.util_raw_input(prompt=shutit_util.colourise(colour,msg),ispass=ispass)
		if boolean and answer in ('yes','y','Y','1','true','t','YES'):
			return True
		if boolean and answer in ('no','n','N','0','false','f','NO'):
			return False
		if answer in ('',None):
			return default
		else:
			return answer


	def load_configs(self):
		"""Responsible for loading config files into ShutIt.
		Recurses down from configured shutit module paths.
		"""
		# Get root default config.
		configs = [('defaults', StringIO(shutit_util._default_cnf)), os.path.expanduser('~/.shutit/config'), os.path.join(self.host['shutit_path'], 'config'), 'configs/build.cnf']
		# Add the shutit global host- and user-specific config file.
		# Add the local build.cnf
		# Get passed-in config(s)
		for config_file_name in self.build['extra_configs']:
			run_config_file = os.path.expanduser(config_file_name)
			if not os.path.isfile(run_config_file):
				print('Did not recognise ' + run_config_file + ' as a file - do you need to touch ' + run_config_file + '?')
				self.handle_exit(exit_code=0)
			configs.append(run_config_file)
		# Image to use to start off. The script should be idempotent, so running it
		# on an already built image should be ok, and is advised to reduce diff space required.
		if self.action['list_configs'] or shutit_global.shutit_global_object.loglevel <= logging.DEBUG:
			msg = ''
			for c in configs:
				if isinstance(c, tuple):
					c = c[0]
				msg = msg + '    \n' + c
				self.log('    ' + c,level=logging.DEBUG)

		# Interpret any config overrides, write to a file and add them to the
		# list of configs to be interpreted
		if self.build['config_overrides']:
			# We don't need layers, this is a temporary configparser
			override_cp = ConfigParser.RawConfigParser()
			for o_sec, o_key, o_val in self.build['config_overrides']:
				if not override_cp.has_section(o_sec):
					override_cp.add_section(o_sec)
				override_cp.set(o_sec, o_key, o_val)
			override_fd = StringIO()
			override_cp.write(override_fd)
			override_fd.seek(0)
			configs.append(('overrides', override_fd))

		self.config_parser = self.get_configs(configs)
		self.get_base_config()


	# Manage config settings, returning a dict representing the settings
	# that have been sanity-checked.
	def get_base_config(self):
		"""Responsible for getting core configuration from config files.
		"""
		cp = self.config_parser
		# BEGIN Read from config files
		# build - details relating to the build
		self.build['privileged']                 = cp.getboolean('build', 'privileged')
		self.build['base_image']                 = cp.get('build', 'base_image')
		self.build['dotest']                     = cp.get('build', 'dotest')
		self.build['net']                        = cp.get('build', 'net')
		self.build['step_through']               = False
		self.build['ctrlc_stop']                 = False
		self.build['ctrlc_passthrough']          = False
		self.build['have_read_config_file']      = False
		# Width of terminal to set up on login and assume for other cases.
		self.build['vagrant_run_dir']            = None
		self.build['this_vagrant_run_dir']       = None
		# Take a command-line arg if given, else default.
		if self.build['conn_module'] is None:
			self.build['conn_module']            = cp.get('build', 'conn_module')
		# Whether to accept default configs
		self.build['accept_defaults']            = None
		# target - the target of the build, ie the container
		self.target['hostname']                  = cp.get('target', 'hostname')
		self.target['ports']                     = cp.get('target', 'ports')
		self.target['volumes']                   = cp.get('target', 'volumes')
		self.target['volumes_from']              = cp.get('target', 'volumes_from')
		self.target['name']                      = cp.get('target', 'name')
		self.target['rm']                        = cp.getboolean('target', 'rm')
		# host - the host on which the shutit script is run
		self.host['add_shutit_to_path']          = cp.getboolean('host', 'add_shutit_to_path')
		self.host['docker_executable']           = cp.get('host', 'docker_executable')
		self.host['dns']                         = cp.get('host', 'dns')
		self.host['password']                    = cp.get('host', 'password')
		if isinstance(self.host['password'],str):
			shutit_global.shutit_global_object.secret_words_set.add(self.host['password'])
		shutit_global.shutit_global_object.logfile = cp.get('host', 'logfile')
		self.host['shutit_module_path']          = cp.get('host', 'shutit_module_path').split(':')

		# repository - information relating to docker repository/registry
		self.repository['name']                  = cp.get('repository', 'name')
		self.repository['server']                = cp.get('repository', 'server')
		self.repository['push']                  = cp.getboolean('repository', 'push')
		self.repository['tag']                   = cp.getboolean('repository', 'tag')
		self.repository['export']                = cp.getboolean('repository', 'export')
		self.repository['save']                  = cp.getboolean('repository', 'save')
		self.repository['suffix_date']           = cp.getboolean('repository', 'suffix_date')
		self.repository['suffix_format']         = cp.get('repository', 'suffix_format')
		self.repository['user']                  = cp.get('repository', 'user')
		self.repository['password']              = cp.get('repository', 'password')
		if isinstance(self.repository['password'],str):
			shutit_global.shutit_global_object.secret_words_set.add(self.repository['password'])
		self.repository['email']                 = cp.get('repository', 'email')
		self.repository['tag_name']              = cp.get('repository', 'tag_name')
		# END Read from config files

		# BEGIN Standard expects
		# It's important that these have '.*' in them at the start, so that the matched data is reliably 'after' in the
		# child object. Use these where possible to make things more consistent.
		# Attempt to capture any starting prompt (when starting) with this regexp.
		self.expect_prompts['base_prompt']       = '\r\n.*[@#$] '
		# END Standard expects

		if self.target['docker_image'] == '':
			self.target['docker_image'] = self.build['base_image']
		# END tidy configs up

		# BEGIN warnings
		# FAILS begins
		# rm is incompatible with repository actions
		if self.target['rm'] and (self.repository['tag'] or self.repository['push'] or self.repository['save'] or self.repository['export']): # pragma: no cover
			print("Can't have [target]/rm and [repository]/(push/save/export) set to true")
			self.handle_exit(exit_code=1)
		if self.target['hostname'] != '' and self.build['net'] != '' and self.build['net'] != 'bridge': # pragma: no cover
			print('\n\ntarget/hostname or build/net configs must be blank\n\n')
			self.handle_exit(exit_code=1)
		# FAILS ends




	def load_all_from_path(self, path):
		"""Dynamically imports files within the same directory (in the end, the path).
		"""
		#111: handle expanded paths
		path = os.path.abspath(path)
		#http://stackoverflow.com/questions/301134/dynamic-module-import-in-python
		if os.path.abspath(path) == self.shutit_main_dir:
			return
		if not os.path.exists(path):
			return
		if os.path.exists(path + '/STOPBUILD') and not self.build['ignorestop']:
			self.log('Ignoring directory: ' + path + ' as it has a STOPBUILD file in it. Pass --ignorestop to shutit run to override.',level=logging.DEBUG)
			return
		for sub in glob.glob(os.path.join(path, '*')):
			subpath = os.path.join(path, sub)
			if os.path.isfile(subpath):
				self.load_mod_from_file(subpath)
			elif os.path.isdir(subpath):
				self.load_all_from_path(subpath)



	def load_mod_from_file(self, fpath):
		"""Loads modules from a .py file into ShutIt if there are no modules from
		this file already.
		We expect to have a callable 'module/0' which returns one or more module
		objects.
		If this doesn't exist we assume that the .py file works in the old style
		(automatically inserting the module into shutit_global) or it's not a shutit
		module.
		"""
		fpath = os.path.abspath(fpath)
		file_ext = os.path.splitext(os.path.split(fpath)[-1])[-1]
		if file_ext.lower() != '.py':
			return
		with open(fpath) as f:
			content = f.read().splitlines()
		ok = False
		for line in content:
			if line.strip() == 'from shutit_module import ShutItModule':
				ok = True
				break
		if not ok:
			self.log('Rejected file: ' + fpath,level=logging.DEBUG)
			return
		# Note that this attribute will only be set for 'new style' module loading, # this should be ok because 'old style' loading checks for duplicate # existing modules.
		# TODO: this is quadratic complexity
		existingmodules = [
			m for m in self.shutit_modules
			if getattr(m, '__module_file', None) == fpath
		]
		if len(existingmodules) > 0:
			self.log('Module already seen: ' + fpath,level=logging.DEBUG)
			return
		# Looks like it's ok to load this file
		self.log('Loading source for: ' + fpath,level=logging.DEBUG)

		# Add this directory to the python path iff not already there.
		directory = os.path.dirname(fpath)
		if directory not in sys.path:
			sys.path.append(os.path.dirname(fpath))
		mod_name = base64.b32encode(fpath.encode()).decode().replace('=', '')
		pymod = imp.load_source(mod_name, fpath)

		# Got the python module, now time to pull the shutit module(s) out of it.
		targets = [
			('module', self.shutit_modules), ('conn_module', self.conn_modules)
		]
		self.build['source'] = {}
		for attr, target in targets:
			modulefunc = getattr(pymod, attr, None)
			# Old style or not a shutit module, nothing else to do
			if not callable(modulefunc):
				return
			modules = modulefunc()
			if not isinstance(modules, list):
				modules = [modules]
			for module in modules:
				setattr(module, '__module_file', fpath)
				ShutItModule.register(module.__class__)
				target.add(module)
				self.build['source'][fpath] = open(fpath).read()



	def handle_exit(self,exit_code=0,loglevel=logging.DEBUG,msg=None):
		if not msg:
			msg = '\nExiting with error code: ' + str(exit_code)
		if exit_code != 0:
			self.log('Exiting with error code: ' + str(exit_code),level=loglevel)
			self.log('Resetting terminal',level=loglevel)
		shutit_util.sanitize_terminal()
		sys.exit(exit_code)


	def config_collection_for_built(self, throw_error=True,silent=False):
		"""Collect configuration for modules that are being built.
		When this is called we should know what's being built (ie after
		dependency resolution).
		"""
		self.log('In config_collection_for_built',level=logging.DEBUG)
		cfg = self.cfg
		for module_id in self.module_ids():
			# Get the config even if installed or building (may be needed in other hooks, eg test).
			if (self.is_to_be_built_or_is_installed(self.shutit_map[module_id]) and
				not self.shutit_map[module_id].get_config(self)):
				self.fail(module_id + ' failed on get_config') # pragma: no cover
			# Collect the build.cfg if we are building here.
			# If this file exists, process it.
			if cfg[module_id]['shutit.core.module.build'] and not self.build['have_read_config_file']:
				module = self.shutit_map[module_id]
				# TODO: __module_file not accessible when within object - look to get this elsewhere and re-read in, then move this function into shutit object.
				cfg_file = os.path.dirname(self.shutit_file_map[module_id]) + '/configs/build.cnf'
				if os.path.isfile(cfg_file):
					self.build['have_read_config_file'] = True
					# use self.get_config, forcing the passed-in default
					config_parser = ConfigParser.ConfigParser()
					config_parser.read(cfg_file)
					for section in config_parser.sections():
						if section == module_id:
							for option in config_parser.options(section):
								override = False
								for mod, opt, val in self.build['config_overrides']:
									val = val # pylint
									# skip overrides
									if mod == module_id and opt == option:
										override = True
								if override:
									continue
								is_bool = isinstance(cfg[module_id][option], bool)
								if is_bool:
									value = config_parser.getboolean(section,option)
								else:
									value = config_parser.get(section,option)
								if option == 'shutit.core.module.allowed_images':
									value = json.loads(value)
								self.get_config(module_id, option, value, forcedefault=True)
		# Check the allowed_images against the base_image
		passed = True
		for module_id in self.module_ids():
			if (cfg[module_id]['shutit.core.module.build'] and
			   (cfg[module_id]['shutit.core.module.allowed_images'] and
			    self.target['docker_image'] not in cfg[module_id]['shutit.core.module.allowed_images'])):
				if not self.allowed_image(module_id):
					passed = False
					if not silent:
						print('\n\nWARNING!\n\nAllowed images for ' + module_id + ' are: ' + str(cfg[module_id]['shutit.core.module.allowed_images']) + ' but the configured image is: ' + self.target['docker_image'] + '\n\nIs your shutit_module_path set correctly?\n\nIf you want to ignore this, pass in the --ignoreimage flag to shutit.\n\n')
		if not passed:
			if not throw_error:
				return False
			if self.build['imageerrorok']:
				# useful for test scripts
				print('Exiting on allowed images error, with return status 0')
				self.handle_exit(exit_code=1)
			else:
				raise ShutItFailException('Allowed images checking failed') # pragma: no cover
		return True


	def config_collection(self):
		"""Collect core config from config files for all seen modules.
		"""
		self.log('In config_collection',level=logging.DEBUG)
		cfg = self.cfg
		for module_id in self.module_ids():
			# Default to None so we can interpret as ifneeded
			self.get_config(module_id, 'shutit.core.module.build', None, boolean=True, forcenone=True)
			self.get_config(module_id, 'shutit.core.module.remove', False, boolean=True)
			self.get_config(module_id, 'shutit.core.module.tag', False, boolean=True)
			# Default to allow any image
			self.get_config(module_id, 'shutit.core.module.allowed_images', [".*"])
			module = self.shutit_map[module_id]
			cfg_file = os.path.dirname(self.shutit_file_map[module_id]) + '/configs/build.cnf'
			if os.path.isfile(cfg_file):
				# use self.get_config, forcing the passed-in default
				config_parser = ConfigParser.ConfigParser()
				config_parser.read(cfg_file)
				for section in config_parser.sections():
					if section == module_id:
						for option in config_parser.options(section):
							if option == 'shutit.core.module.allowed_images':
								override = False
								for mod, opt, val in self.build['config_overrides']:
									val = val # pylint
									# skip overrides
									if mod == module_id and opt == option:
										override = True
								if override:
									continue
								value = config_parser.get(section,option)
								if option == 'shutit.core.module.allowed_images':
									value = json.loads(value)
								self.get_config(module_id, option, value, forcedefault=True)
			# ifneeded will (by default) only take effect if 'build' is not
			# specified. It can, however, be forced to a value, but this
			# should be unusual.
			if cfg[module_id]['shutit.core.module.build'] is None:
				self.get_config(module_id, 'shutit.core.module.build_ifneeded', True, boolean=True)
				cfg[module_id]['shutit.core.module.build'] = False
			else:
				self.get_config(module_id, 'shutit.core.module.build_ifneeded', False, boolean=True)



	def do_list_modules(self, long_output=None,sort_order=None):
		"""Display a list of loaded modules.

		Config items:
			- shutit.list_modules['long']
			  If set, also print each module's run order value

			- shutit.list_modules['sort']
			  Select the column by which the list is ordered:
				- id: sort the list by module id
				- run_order: sort the list by module run order

		The output is also saved to ['build']['log_config_path']/module_order.txt

		Dependencies: operator
		"""
		cfg = self.cfg
		# list of module ids and other details
		# will also contain column headers
		table_list = []
		if long_output is None:
			long_output = self.list_modules['long']
		if sort_order is None:
			sort_order = self.list_modules['sort']
		if long_output:
			# --long table: sort modules by run order
			table_list.append(["Order","Module ID","Description","Run Order","Built","Compatible"])
			#table_list.append(["Order","Module ID","Description","Run Order","Built"])
		else:
			# "short" table ==> sort module by module_id
			#table_list.append(["Module ID","Description","Built"])
			table_list.append(["Module ID","Description","Built","Compatible"])

		if sort_order == 'run_order':
			d = {}
			for m in self.shutit_modules:
				d.update({m.module_id:m.run_order})
			# sort dict by run_order; see http://stackoverflow.com/questions/613183/sort-a-python-dictionary-by-value
			b = sorted(d.items(), key=operator.itemgetter(1))
			count = 0
			# now b is a list of tuples (module_id, run_order)
			for pair in b:
				# module_id is the first item of the tuple
				k = pair[0]
				for m in self.shutit_modules:
					if m.module_id == k:
						count += 1
						compatible = True
						if not cfg[m.module_id]['shutit.core.module.build']:
							cfg[m.module_id]['shutit.core.module.build'] = True
							compatible = self.determine_compatibility(m.module_id) == 0
							cfg[m.module_id]['shutit.core.module.build'] = False
						if long_output:
							table_list.append([str(count),m.module_id,m.description,str(m.run_order),str(cfg[m.module_id]['shutit.core.module.build']),str(compatible)])
							#table_list.append([str(count),m.module_id,m.description,str(m.run_order),str(cfg[m.module_id]['shutit.core.module.build'])])
						else:
							table_list.append([m.module_id,m.description,str(cfg[m.module_id]['shutit.core.module.build']),str(compatible)])
		elif sort_order == 'id':
			l = []
			for m in self.shutit_modules:
				l.append(m.module_id)
			l.sort()
			for k in l:
				for m in self.shutit_modules:
					if m.module_id == k:
						count = 1
						compatible = True
						if not cfg[m.module_id]['shutit.core.module.build']:
							cfg[m.module_id]['shutit.core.module.build'] = True
							compatible = self.determine_compatibility(m.module_id) == 0
						if long_output:
							table_list.append([str(count),m.module_id,m.description,str(m.run_order),str(cfg[m.module_id]['shutit.core.module.build']),str(compatible)])
							#table_list.append([str(count),m.module_id,m.description,str(m.run_order),str(cfg[m.module_id]['shutit.core.module.build'])])
						else:
							#table_list.append([m.module_id,m.description,str(cfg[m.module_id]['shutit.core.module.build'])])
							table_list.append([m.module_id,m.description,str(cfg[m.module_id]['shutit.core.module.build']),str(compatible)])

		# format table for display
		table = texttable.Texttable()
		table.add_rows(table_list)
		# Base length of table on length of strings
		colwidths = []
		for item in table_list:
			for n in range(0,len(item)):
				# default to 10 chars
				colwidths.append(10)
			break
		for item in table_list:
			for n in range(0,len(item)-1):
				if len(str(item[n])) > colwidths[n]:
					colwidths[n] = len(str(item[n]))
		table.set_cols_width(colwidths)
		msg = table.draw()
		print('\n' + msg)


	def print_config(self, cfg, hide_password=True, history=False, module_id=None):
		"""Returns a string representing the config of this ShutIt run.
		"""
		cp = self.config_parser
		s = ''
		keys1 = list(cfg.keys())
		if keys1:
			keys1.sort()
		for k in keys1:
			if module_id is not None and k != module_id:
				continue
			if isinstance(k, str) and isinstance(cfg[k], dict):
				s += '\n[' + k + ']\n'
				keys2 = list(cfg[k].keys())
				if keys2:
					keys2.sort()
				for k1 in keys2:
					line = ''
					line += k1 + ':'
					# If we want to hide passwords, we do so using a sha512
					# done an aritrary number of times (27).
					if hide_password and (k1 == 'password' or k1 == 'passphrase'):
						p = hashlib.sha512(cfg[k][k1]).hexdigest()
						i = 27
						while i > 0:
							i -= 1
							p = hashlib.sha512(s).hexdigest()
						line += p
					else:
						if type(cfg[k][k1] == bool):
							line += str(cfg[k][k1])
						elif type(cfg[k][k1] == str):
							line += cfg[k][k1]
					if history:
						try:
							line += (30-len(line)) * ' ' + ' # ' + cp.whereset(k, k1)
						except Exception:
							# Assume this is because it was never set by a config parser.
							line += (30-len(line)) * ' ' + ' # ' + "defaults in code"
					s += line + '\n'
		return s


	def process_args(self, args):
		"""Process the args we have.
		"""
		assert isinstance(args,ShutItInit)

		if args.action == 'version':
			print('ShutIt version: ' + shutit.shutit_version)
			self.handle_exit(exit_code=0)

		# What are we asking shutit to do?
		self.action['list_configs'] = args.action == 'list_configs'   # TODO: abstract away to shutitconfig object
		self.action['list_modules'] = args.action == 'list_modules'   # TODO: abstract away to shutitconfig object
		self.action['list_deps']    = args.action == 'list_deps'   # TODO: abstract away to shutitconfig object
		self.action['skeleton']     = args.action == 'skeleton'   # TODO: abstract away to shutitconfig object
		self.action['build']        = args.action == 'build'   # TODO: abstract away to shutitconfig object
		self.action['run']          = args.action == 'run'   # TODO: abstract away to shutitconfig object
		self.build['exam']     = False # TODO: place in global
		# Logging
		shutit_global.shutit_global_object.logfile   = args.logfile # TODO: place in global

		shutit_global.shutit_global_object.loglevel = args.log # TODO: place in global
		if shutit_global.shutit_global_object.loglevel in ('', None): # TODO: place in global
			shutit_global.shutit_global_object.loglevel = 'INFO' # TODO: place in global
		shutit_global.shutit_global_object.setup_logging() # TODO: place in global

		# This mode is a bit special - it's the only one with different arguments
		# TODO: abstract away to separate function in global
		if self.action['skeleton']:
			delivery_method = args.delivery # TODO: abstract away to shutitconfig object
			accept_defaults = args.accept # TODO: abstract away to shutitconfig object
			# Looks through the arguments given for valid shutitfiles, and adds their names to _new_shutitfiles.
			_new_shutitfiles = None
			if args.shutitfiles: # TODO: abstract away to shutitconfig object
				cwd = os.getcwd()
				_new_shutitfiles       = []
				_delivery_methods_seen = set()
				for shutitfile in args.shutitfiles: # TODO: abstract away to shutitconfig object
					if shutitfile[0] != '/':
						shutitfile = cwd + '/' + shutitfile
					if os.path.isfile(shutitfile):
						candidate_shutitfile_fh = open(shutitfile,'r')
						candidate_shutitfile_contents = candidate_shutitfile_fh.read()
						candidate_shutitfile_fh.close()
						try:
							shutitfile_representation, ok = shutit_skeleton.process_shutitfile(self, candidate_shutitfile_contents)
							if not ok or candidate_shutitfile_contents.strip() == '':
								print('Ignoring file (failed to parse candidate shutitfile): ' + shutitfile)
							else:
								_new_shutitfiles.append(shutitfile)
								if len(shutitfile_representation['shutitfile']['delivery']) > 0:
									_delivery_methods_seen.add(shutitfile_representation['shutitfile']['delivery'][0][1])
						except Exception as e:
							print('')
							print(e)
							print('Ignoring file (failed to parse candidate shutitfile): ' + shutitfile)
					elif os.path.isdir(shutitfile):
						for root, subfolders, files in os.walk(shutitfile):
							subfolders.sort()
							files.sort()
							for fname in files:
								candidate_shutitfile = os.path.join(root, fname)
								try:
									if os.path.isfile(candidate_shutitfile):
										candidate_shutitfile_fh = open(candidate_shutitfile,'r')
										candidate_shutitfile_contents = candidate_shutitfile_fh.read()
										candidate_shutitfile_fh.close()
										shutitfile_representation, ok = shutit_skeleton.process_shutitfile(shutit, candidate_shutitfile_contents)
										if not ok or candidate_shutitfile_contents.strip() == '':
											print('Ignoring file (failed to parse candidate shutitfile): ' + candidate_shutitfile)
										else:
											_new_shutitfiles.append(candidate_shutitfile)
											if len(shutitfile_representation['shutitfile']['delivery']) > 0:
												_delivery_methods_seen.add(shutitfile_representation['shutitfile']['delivery'][0][1])
									else:
										print('Ignoring filename (not a normal file): ' + fname)
								except:
									print('Ignoring file (failed to parse candidate shutitfile): ' + candidate_shutitfile)
				if _new_shutitfiles:
					if len(_delivery_methods_seen) == 0 and delivery_method is None:
						delivery_method = 'bash'
					elif len(_delivery_methods_seen) == 0:
						pass
					elif len(_delivery_methods_seen) == 1 and delivery_method is None:
						delivery_method = _delivery_methods_seen.pop()
					elif len(_delivery_methods_seen) == 1:
						shutitfile_delivery_method = _delivery_methods_seen.pop()
						if delivery_method != shutitfile_delivery_method:
							print('Conflicting delivery methods passed in vs. from shutitfile.\nPassed-in: ' + delivery_method + '\nShutitfile: ' + shutitfile_delivery_method)
							self.handle_exit(exit_code=1)
					else:
						print('Too many delivery methods seen in shutitfiles: ' + str(_new_shutitfiles))
						print('Delivery methods: ' + str(_delivery_methods_seen))
						print('Delivery method passed in: ' + delivery_method)
						self.handle_exit(exit_code=1)
				else:
					print('ShutItFiles: ' + str(_new_shutitfiles) + ' appear to not exist.')
					self.handle_exit(exit_code=1)
			module_directory = args.name # TODO: abstract away to shutitconfig object
			if module_directory == '':
				default_dir = self.host['calling_path'] + '/shutit_' + shutit_util.random_word()
				if accept_defaults:
					module_directory = default_dir
				else:
					module_directory = self.util_raw_input(prompt='# Input a name for this module.\n# Default: ' + default_dir + '\n', default=default_dir)
			if module_directory[0] != '/':
				module_directory = self.host['calling_path'] + '/' + module_directory
			module_name = module_directory.split('/')[-1].replace('-','_')
			if args.domain == '': # TODO: abstract away to shutitconfig object
				default_domain_name = os.getcwd().split('/')[-1] + '.' + module_name
				#if accept_defaults:
				domain = default_domain_name
				#else:
				#	domain = self.util_raw_input(prompt='# Input a unique domain, eg (com.yourcorp).\n# Default: ' + default_domain_name + '\n', default=default_domain_name)
			else:
				domain = args.domain # TODO: abstract away to shutitconfig object
			# Figure out defaults.
			# If no pattern supplied, then assume it's the same as delivery.
			default_pattern = 'bash'
			if args.pattern == '': # TODO: abstract away to shutitconfig object
				if accept_defaults or _new_shutitfiles:
					if _new_shutitfiles:
						default_pattern = delivery_method
					pattern = default_pattern
				else:
					pattern = self.util_raw_input(prompt='''# Input a ShutIt pattern.
	Default: ''' + default_pattern + '''

	bash:              a shell script
	docker:            a docker image build
	vagrant:           a vagrant setup
	docker_tutorial:   a docker-based tutorial
	shutitfile:        a shutitfile-based project (can be docker, bash, vagrant)

	''',default=default_pattern)
			else:
				pattern = args.pattern # TODO: abstract away to shutitconfig object

			# Sort out delivery method.
			if delivery_method is None:
				take_this_default = False
				default_delivery = 'bash'
				if pattern in ('docker','docker_tutorial', 'shutitfile'):
					if pattern in ('docker','docker_tutorial'):
						take_this_default = True
					default_delivery = 'docker'
				elif pattern in ('vagrant','bash'):
					take_this_default = True
					default_delivery = 'bash'
				else:
					default_delivery = 'bash'
				if accept_defaults or take_this_default:
					delivery = default_delivery
				else:
					delivery = ''
					while delivery not in shutit_util.allowed_delivery_methods:
						delivery = self.util_raw_input(prompt=textwrap.dedent('''
							# Input a delivery method from: bash, docker, vagrant.
							# Default: ''' + default_delivery + '''

							docker:      build within a docker image
							bash:        run commands directly within bash
							vagrant:     build an n-node vagrant cluster

							'''), default=default_delivery)
			else:
				delivery = delivery_method

			self.cfg['skeleton'] = {
				'path':                   module_directory,
				'module_name':            module_name,
				'base_image':             args.base_image, # TODO: abstract away to shutitconfig object
				'domain':                 domain,
				'domain_hash':            str(shutit_util.get_hash(domain)),
				'depends':                args.depends, # TODO: abstract away to shutitconfig object
				'script':                 args.script, # TODO: abstract away to shutitconfig object
				'shutitfiles':            _new_shutitfiles,
				'output_dir':             args.output_dir, # TODO: abstract away to shutitconfig object
				'delivery':               delivery,
				'pattern':                pattern,
				'vagrant_num_machines':   args.vagrant_num_machines, # TODO: abstract away to shutitconfig object
				'vagrant_ssh_access':     args.vagrant_ssh_access, # TODO: abstract away to shutitconfig object
				'vagrant_machine_prefix': args.vagrant_machine_prefix, # TODO: abstract away to shutitconfig object
				'vagrant_docker':         args.vagrant_docker # TODO: abstract away to shutitconfig object
			}
			# set defaults to allow config to work
			self.build['extra_configs']    = []
			self.build['config_overrides'] = []
			self.build['conn_module']      = None
			self.build['delivery']         = 'bash'
			self.target['docker_image']    = ''
		# TODO: abstract away to separate function in global
		elif self.action['run']:
			module_name      = shutit_util.random_id(chars=string.ascii_letters)
			module_dir       = "/tmp/shutit_built/" + module_name
			module_domain    = module_name + '.' + module_name
			argv_new = [sys.argv[0],'skeleton','--shutitfile'] + args.shutitfiles + ['--name', module_dir,'--domain',module_domain,'--pattern','bash'] # TODO: abstract away to shutitconfig object
			retdir = os.getcwd()
			subprocess.call(argv_new)
			os.chdir(module_dir)
			subprocess.call('./run.sh')
			os.chdir(retdir)
			sys.exit(0)
		# TODO: process
		else:
			shutit_home = self.host['shutit_path'] = os.path.expanduser('~/.shutit')
			# We're not creating a skeleton, so make sure we have the infrastructure
			# in place for a user-level storage area
			if not os.path.isdir(shutit_home):
				mkpath(shutit_home, 0o700)
			if not os.path.isfile(os.path.join(shutit_home, 'config')):
				f = os.open(os.path.join(shutit_home, 'config'), os.O_WRONLY | os.O_CREAT, 0o600)
				if PY3:
					os.write(f,bytes(shutit_util._default_cnf,'utf-8'))
				else:
					os.write(f,shutit_util._default_cnf)
				os.close(f)

			# Default this to False as it's not always set (mostly for debug logging).
			self.list_configs['cfghistory']  = False
			self.list_modules['long']        = False
			self.list_modules['sort']        = None
			self.build['video']              = False
			self.build['training']           = False
			self.build['exam_object']        = None
			self.build['choose_config']      = False
			# Persistence- and build-related arguments.
			if self.action['build']:
				self.repository['push']       = args.push  # TODO: abstract away to shutitconfig object
				self.repository['export']     = args.export # TODO: abstract away to shutitconfig object
				self.repository['save']       = args.save # TODO: abstract away to shutitconfig object
				self.build['distro_override'] = args.distro # TODO: abstract away to shutitconfig object
				self.build['mount_docker']    = args.mount_docker# TODO: abstract away to shutitconfig object
				self.build['walkthrough']     = args.walkthrough# TODO: abstract away to shutitconfig object
				self.build['training']        = args.training# TODO: abstract away to shutitconfig object
				self.build['exam']            = args.exam# TODO: abstract away to shutitconfig object
				self.build['choose_config']   = args.choose_config# TODO: abstract away to shutitconfig object
				if self.build['exam'] and not self.build['training']:
					# We want it to be quiet
					#print('--exam implies --training, setting --training on!')
					print('Exam starting up')
					self.build['training'] = True
				if (self.build['exam'] or self.build['training']) and not self.build['walkthrough']:
					if not self.build['exam']:
						print('--training or --exam implies --walkthrough, setting --walkthrough on!')
					self.build['walkthrough'] = True
				if isinstance(args.video, list) and args.video[0] >= 0:# TODO: abstract away to shutitconfig object
					self.build['walkthrough']      = True
					self.build['walkthrough_wait'] = float(args.video[0])# TODO: abstract away to shutitconfig object
					self.build['video']            = True
					if self.build['training']:
						print('--video and --training mode incompatible')
						self.handle_exit(exit_code=1)
					if self.build['exam']:
						print('--video and --exam mode incompatible')
						self.handle_exit(exit_code=1)
				# Create a test session object if needed.
				if self.build['exam']:
					self.build['exam_object'] = shutit_exam.ShutItExamSession(self)
			elif self.action['list_configs']:
				self.list_configs['cfghistory'] = args.history# TODO: abstract away to shutitconfig object
			elif self.action['list_modules']:
				self.list_modules['long'] = args.long# TODO: abstract away to shutitconfig object
				self.list_modules['sort'] = args.sort# TODO: abstract away to shutitconfig object

			# What are we building on? Convert arg to conn_module we use.
			if args.delivery == 'docker' or args.delivery is None:# TODO: abstract away to shutitconfig object
				self.build['conn_module'] = 'shutit.tk.conn_docker'
				self.build['delivery']    = 'docker'
			elif args.delivery == 'ssh':# TODO: abstract away to shutitconfig object
				self.build['conn_module'] = 'shutit.tk.conn_ssh'
				self.build['delivery']    = 'ssh'
			elif args.delivery == 'bash' or args.delivery == 'dockerfile':# TODO: abstract away to shutitconfig object
				self.build['conn_module'] = 'shutit.tk.conn_bash'
				self.build['delivery']    = args.delivery# TODO: abstract away to shutitconfig object
			# If the image_tag has been set then ride roughshod over the ignoreimage value if not supplied
			if args.image_tag != '' and args.ignoreimage is None:# TODO: abstract away to shutitconfig object
				args.ignoreimage = True# TODO: abstract away to shutitconfig object
			# If ignoreimage is still not set, then default it to False
			if args.ignoreimage is None:# TODO: abstract away to shutitconfig object
				args.ignoreimage = False# TODO: abstract away to shutitconfig object

			# Get these early for this part of the build.
			# These should never be config arguments, since they are needed before config is passed in.
			if args.shutit_module_path is not None:# TODO: abstract away to shutitconfig object
				module_paths = args.shutit_module_path.split(':')# TODO: abstract away to shutitconfig object
				if '.' not in module_paths:
					module_paths.append('.')
				args.set.append(('host', 'shutit_module_path', ':'.join(module_paths)))# TODO: abstract away to shutitconfig object
			shutit_global.shutit_global_object.interactive      = int(args.interactive)# TODO: abstract away to shutitconfig object
			self.build['extra_configs']    = args.config# TODO: abstract away to shutitconfig object
			self.build['config_overrides'] = args.set# TODO: abstract away to shutitconfig object
			self.build['ignorestop']       = args.ignorestop# TODO: abstract away to shutitconfig object
			self.build['ignoreimage']      = args.ignoreimage# TODO: abstract away to shutitconfig object
			self.build['imageerrorok']     = args.imageerrorok# TODO: abstract away to shutitconfig object
			self.build['tag_modules']      = args.tag_modules# TODO: abstract away to shutitconfig object
			self.build['deps_only']        = args.deps_only# TODO: abstract away to shutitconfig object
			self.build['always_echo']      = args.echo# TODO: abstract away to shutitconfig object
			self.target['docker_image']    = args.image_tag# TODO: abstract away to shutitconfig object

			if self.build['delivery'] in ('bash','ssh'):
				if self.target['docker_image'] != '': # pragma: no cover
					print('delivery method specified (' + self.build['delivery'] + ') and image_tag argument make no sense')
					self.handle_exit(exit_code=1)
			# Finished parsing args.
			# Sort out config path
			if self.action['list_configs'] or self.action['list_modules'] or self.action['list_deps'] or shutit_global.shutit_global_object.loglevel == logging.DEBUG:
				self.build['log_config_path'] = shutit_global.shutit_global_object.shutit_state_dir + '/config'
				if not os.path.exists(self.build['log_config_path']):
					os.makedirs(self.build['log_config_path'])
					os.chmod(self.build['log_config_path'],0o777)
			else:
				self.build['log_config_path'] = None
			# Tutorial stuff. TODO: ditch tutorial mode
			#The config is read in the following order:
			#~/.shutit/config
			#	- Host- and username-specific config for this host.
			#/path/to/this/shutit/module/configs/build.cnf
			#	- Config specifying what should be built when this module is invoked.
			#/your/path/to/<configname>.cnf
			#	- Passed-in config (via --config, see --help)
			#command-line overrides, eg -s com.mycorp.mymodule.module name value
			# Set up trace as fast as possible.
			if args.trace:# TODO: abstract away to shutitconfig object into global
				def tracefunc(frame, event, arg, indent=[0]):
					indent = indent # pylint
					arg = arg # pylint
					if event == 'call':
						self.log('-> call function: ' + frame.f_code.co_name + ' ' + str(frame.f_code.co_varnames),level=logging.DEBUG)
					elif event == 'return':
						self.log('<- exit function: ' + frame.f_code.co_name,level=logging.DEBUG)
					return tracefunc
				sys.settrace(tracefunc)


	def get_configs(self, configs):
		"""Reads config files in, checking their security first
		(in case passwords/sensitive info is in them).
		"""
		cp  = LayerConfigParser()
		fail_str = ''
		files    = []
		for config_file in configs:
			if isinstance(config_file, tuple):
				continue
			if not shutit_util.is_file_secure(config_file):
				fail_str = fail_str + '\nchmod 0600 ' + config_file
				files.append(config_file)
		if fail_str != '':
			if shutit_global.shutit_global_object.interactive > 1:
				fail_str = 'Files are not secure, mode should be 0600. Running the following commands to correct:\n' + fail_str + '\n'
				# Actually show this to the user before failing...
				self.log(fail_str)
				self.log('Do you want me to run this for you? (input y/n)')
				if shutit_global.shutit_global_object.interactive == 0 or self.util_raw_input(default='y') == 'y':
					for f in files:
						self.log('Correcting insecure file permissions on: ' + f)
						os.chmod(f,0o600)
					# recurse
					return self.get_configs(configs)
			else:
				for f in files:
					self.log('Correcting insecure file permissions on: ' + f)
					os.chmod(f,0o600)
				# recurse
				return self.get_configs(configs)
			self.fail(fail_str) # pragma: no cover
		for config in configs:
			if isinstance(config, tuple):
				cp.readfp(config[1], filename=config[0])
			else:
				cp.read(config)
		# Treat allowed_images as a special, additive case
		self.build['shutit.core.module.allowed_images'] = cp.get_config_set('build', 'shutit.core.module.allowed_images')
		return cp


	# Returns the config dict
	def parse_args(self):
		r"""Responsible for parsing arguments.

		Environment variables:
		SHUTIT_OPTIONS:
		Loads command line options from the environment (if set).
		Behaves like GREP_OPTIONS:
			- space separated list of arguments
			- backslash before a space escapes the space separation
			- backslash before a backslash is interpreted as a single backslash
			- all other backslashes are treated literally
		eg ' a\ b c\\ \\d \\\e\' becomes '', 'a b', 'c\', '\d', '\\e\'
		SHUTIT_OPTIONS is ignored if we are creating a skeleton
		"""
		shutit_global.shutit_global_object.real_user_id = pexpect.run('id -u ' + shutit_global.shutit_global_object.real_user)

		# These are in order of their creation
		actions = ['build', 'run', 'list_configs', 'list_modules', 'list_deps', 'skeleton', 'version']

		# COMPAT 2014-05-15 - build is the default if there is no action specified
		# and we've not asked for help and we've called via 'shutit.py'
		if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] not in actions
				and '-h' not in sys.argv and '--help' not in sys.argv):
			sys.argv.insert(1, 'build')

		parser = argparse.ArgumentParser(description='ShutIt - a tool for managing complex Docker deployments.\n\nTo view help for a specific subcommand, type ./shutit <subcommand> -h',prog="ShutIt")
		subparsers = parser.add_subparsers(dest='action', help='''Action to perform - build=deploy to target, skeleton=construct a skeleton module, list_configs=show configuration as read in, list_modules=show modules available, list_deps=show dep graph ready for graphviz. Defaults to 'build'.''')


		sub_parsers = dict()
		for action in actions:
			sub_parsers[action] = subparsers.add_parser(action)

		sub_parsers['run'].add_argument('shutitfiles', nargs='*', default=['ShutItFile','Shutitfile','ShutItfile','ShutitFile','shutitfile'])

		sub_parsers['skeleton'].add_argument('--name', help='Absolute path to new directory for module. Last part of path is taken as the module name.',default='')
		sub_parsers['skeleton'].add_argument('--domain', help='Arbitrary but unique domain for namespacing your module, eg com.mycorp',default='')
		sub_parsers['skeleton'].add_argument('--depends', help='Module id to depend on, default shutit.tk.setup (optional)', default='shutit.tk.setup')
		sub_parsers['skeleton'].add_argument('--base_image', help='FROM image, default ubuntu:16.04 (optional)', default='ubuntu:16.04')
		sub_parsers['skeleton'].add_argument('--script', help='Pre-existing shell script to integrate into module (optional)', nargs='?', default=None)
		sub_parsers['skeleton'].add_argument('--output_dir', help='Just output the created directory', default=False, const=True, action='store_const')
		sub_parsers['skeleton'].add_argument('--shutitfiles', nargs='+', default=None)
		sub_parsers['skeleton'].add_argument('--vagrant_num_machines', default=None)
		sub_parsers['skeleton'].add_argument('--vagrant_ssh_access', default=False, const=True, action='store_const')
		sub_parsers['skeleton'].add_argument('--vagrant_machine_prefix', default=None)
		sub_parsers['skeleton'].add_argument('--vagrant_docker', default=None, const=True, action='store_const')
		sub_parsers['skeleton'].add_argument('--pattern', help='Pattern to use', default='')
		sub_parsers['skeleton'].add_argument('--delivery', help='Delivery method, aka target. "docker" container (default), configured "ssh" connection, "bash" session', default=None, choices=('docker','dockerfile','ssh','bash'))
		sub_parsers['skeleton'].add_argument('-a','--accept', help='Accept defaults', const=True, default=False, action='store_const')
		sub_parsers['skeleton'].add_argument('--log','-l', help='Log level (DEBUG, INFO (default), WARNING, ERROR, CRITICAL)', default='')
		sub_parsers['skeleton'].add_argument('-o','--logfile', help='Log output to this file', default='')

		sub_parsers['build'].add_argument('--export', help='Perform docker export to a tar file', const=True, default=False, action='store_const')
		sub_parsers['build'].add_argument('--save', help='Perform docker save to a tar file', const=True, default=False, action='store_const')
		sub_parsers['build'].add_argument('--push', help='Push to a repo', const=True, default=False, action='store_const')
		sub_parsers['build'].add_argument('--distro', help='Specify the distro type', default='', choices=('ubuntu','debian','alpine','steamos','red hat','centos','fedora','shutit'))
		sub_parsers['build'].add_argument('--mount_docker', help='Mount the docker socket', default=False, action='store_const', const=True)
		sub_parsers['build'].add_argument('-w','--walkthrough', help='Run in walkthrough mode', default=False, action='store_const', const=True)
		sub_parsers['build'].add_argument('-c','--choose_config', help='Choose configuration interactively', default=False, action='store_const', const=True)
		sub_parsers['build'].add_argument('--video', help='Run in video mode. Same as walkthrough, but waits n seconds rather than for input', nargs=1, default=-1)
		sub_parsers['build'].add_argument('--training', help='Run in "training" mode, where correct input is required at key points', default=False, action='store_const', const=True)
		sub_parsers['build'].add_argument('--exam', help='Run in "exam" mode, where correct input is required at key points and progress is tracked', default=False, action='store_const', const=True)

		sub_parsers['list_configs'].add_argument('--history', help='Show config with history', const=True, default=False, action='store_const')
		sub_parsers['list_modules'].add_argument('--long', help='Show extended module info, including ordering', const=True, default=False, action='store_const')
		sub_parsers['list_modules'].add_argument('--sort', help='Order the modules seen, default to module id', default='id', choices=('id','run_order'))

		for action in ['build', 'list_configs', 'list_modules', 'list_deps','run']:
			sub_parsers[action].add_argument('-o','--logfile',default='', help='Log output to this file')
			sub_parsers[action].add_argument('-l','--log',default='', help='Log level (DEBUG, INFO (default), WARNING, ERROR, CRITICAL)',choices=('DEBUG','INFO','WARNING','ERROR','CRITICAL','debug','info','warning','error','critical'))
			if action != 'run':
				sub_parsers[action].add_argument('-d','--delivery', help='Delivery method, aka target. "docker" container (default), configured "ssh" connection, "bash" session', default=None, choices=('docker','dockerfile','ssh','bash'))
				sub_parsers[action].add_argument('--config', help='Config file for setup config. Must be with perms 0600. Multiple arguments allowed; config files considered in order.', default=[], action='append')
				sub_parsers[action].add_argument('-s', '--set', help='Override a config item, e.g. "-s target rm no". Can be specified multiple times.', default=[], action='append', nargs=3, metavar=('SEC', 'KEY', 'VAL'))
				sub_parsers[action].add_argument('--image_tag', help='Build container from specified image - if there is a symbolic reference, please use that, eg localhost.localdomain:5000/myref', default='')
				sub_parsers[action].add_argument('--tag_modules', help='''Tag each module after it's successfully built regardless of the module config and based on the repository config.''', default=False, const=True, action='store_const')
				sub_parsers[action].add_argument('-m', '--shutit_module_path', default=None, help='List of shutit module paths, separated by colons. ShutIt registers modules by running all .py files in these directories.')
				sub_parsers[action].add_argument('--trace', help='Trace function calls', const=True, default=False, action='store_const')
				sub_parsers[action].add_argument('--interactive', help='Level of interactive. 0 = none, 1 = honour pause points and config prompting, 2 = query user on each module, 3 = tutorial mode', default='1')
				sub_parsers[action].add_argument('--ignorestop', help='Ignore STOP files', const=True, default=False, action='store_const')
				sub_parsers[action].add_argument('--ignoreimage', help='Ignore disallowed images', const=True, default=None, action='store_const')
				sub_parsers[action].add_argument('--imageerrorok', help='Exit without error if allowed images fails (used for test scripts)', const=True, default=False, action='store_const')
				sub_parsers[action].add_argument('--deps_only', help='build deps only, tag with suffix "_deps"', const=True, default=False, action='store_const')
				sub_parsers[action].add_argument('--echo', help='Always echo output', const=True, default=False, action='store_const')

		args_list = sys.argv[1:]
		if os.environ.get('SHUTIT_OPTIONS', None) and args_list[0] != 'skeleton':
			env_args = os.environ['SHUTIT_OPTIONS'].strip()
			# Split escaped backslashes
			env_args_split = re.split(r'(\\\\)', env_args)
			# Split non-escaped spaces
			env_args_split = [re.split(r'(?<!\\)( )', item) for item in env_args_split]
			# Flatten
			env_args_split = [item for sublist in env_args_split for item in sublist]
			# Split escaped spaces
			env_args_split = [re.split(r'(\\ )', item) for item in env_args_split]
			# Flatten
			env_args_split = [item for sublist in env_args_split for item in sublist]
			# Trim empty strings
			env_args_split = [item for item in env_args_split if item != '']
			# We know we don't have to deal with an empty env argument string
			env_args_list = ['']
			# Interpret all of the escape sequences
			for item in env_args_split:
				if item == ' ':
					env_args_list.append('')
				elif item == '\\ ':
					env_args_list[-1] += ' '
				elif item == '\\\\':
					env_args_list[-1] += '\\'
				else:
					env_args_list[-1] += item
			args_list[1:1] = env_args_list
		args = parser.parse_args(args_list)
		if args.action == 'version':
			self.process_args(ShutItInit(args.action,
			                             logfile=args.logfile,
			                             log=args.log))
		elif args.action == 'skeleton':
			self.process_args(ShutItInit(args.action,
			                             logfile=args.logfile,
			                             log=args.log,
			                             delivery=args.delivery,
			                             shutitfiles=args.shutitfiles,
			                             script=args.script,
			                             base_image=args.base_image,
			                             depends=args.depends,
			                             name=args.name,
			                             domain=args.domain,
			                             pattern=args.pattern,
			                             output_dir=args.output_dir,
			                             vagrant_ssh_access=args.vagrant_ssh_access,
			                             vagrant_num_machines=args.vagrant_num_machines,
			                             vagrant_machine_prefix=args.vagrant_machine_prefix,
			                             vagrant_docker=args.vagrant_docker))
		elif args.action == 'run':
			self.process_args(ShutItInit(args.action,
			                             logfile=args.logfile,
			                             log=args.log,
			                             shutitfiles=args.shutitfiles,
			                             delivery = args.delivery))
		elif args.action == 'build':
			self.process_args(ShutItInit(args.action,
			                             logfile=args.logfile,
			                             log=args.log,
			                             push=args.push,
			                             export=args.export,
			                             save=args.save,
			                             distro=args.distro,
			                             mount_docker=args.mount_docker,
			                             walkthrough=args.walkthrough,
			                             training=args.training,
			                             choose_config=args.choose_config,
		                                 config = args.config,
		                                 set = args.set,
		                                 ignorestop = args.ignorestop,
		                                 ignoreimage = args.ignoreimage,
		                                 imageerrorok = args.imageerrorok,
		                                 tag_modules = args.tag_modules,
		                                 image_tag = args.image_tag,
		                                 video = args.video,
		                                 deps_only = args.deps_only,
		                                 echo = args.echo,
		                                 delivery = args.delivery,
		                                 interactive = args.interactive,
		                                 trace = args.trace,
		                                 shutit_module_path = args.shutit_module_path,
			                             exam=args.exam))
		elif args.action == 'list_configs':
			self.process_args(ShutItInit(args.action,
			                             logfile=args.logfile,
			                             log=args.log,
			                             history=args.history))
		elif args.action == 'list_modules':
			self.process_args(ShutItInit(args.action,
			                             logfile=args.logfile,
			                             log=args.log,
			                             sort=args.sort,
			                             long=args.long))
