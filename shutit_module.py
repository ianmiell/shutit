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
"""Abstract class that defines how a ShutIt module should be written.
"""


from six import with_metaclass, iteritems
from abc import ABCMeta, abstractmethod
import decimal
import inspect


# TODO: these don't belong here, but this module is 'top level' and doesn't depend on any other shutit files.
class ShutItException(Exception):
	"""Placeholder exception. Implementation TODO.
	"""
	pass


class ShutItModuleError(ShutItException):
	"""Placeholder exception. Implementation TODO.
	"""
	pass


class ShutItFailException(ShutItException):
	"""Placeholder exception. Implementation TODO.
	"""
	pass



def shutit_method_scope(func):
	"""Notifies the ShutIt object whenever we call a shutit module method.
	This allows setting values for the 'scope' of a function.
	"""
	def wrapper(self, shutit):
		"""Wrapper to call a shutit module method, notifying the ShutIt object.
		"""
		ret = func(self, shutit)
		return ret
	return wrapper


class ShutItMeta(ABCMeta):
	"""Abstract class that defines what a ShutIt module must implement
	to be registered.
	"""
	ShutItModule = None
	def __new__(mcs, name, bases, local):
		"""Checks this is a ShutItModule, and wraps any ShutItModule methods
		that have been overridden in the subclass.
		"""

		# Don't wrap methods of the ShutItModule class, only subclasses
		if name != 'ShutItModule':

			sim = mcs.ShutItModule
			assert sim is not None

			# Wrap any of the ShutItModule (self, shutit) methods that have been
			# overridden in a subclass
			for name, method in iteritems(local):
				if not hasattr(sim, name):
					continue
				if not callable(method):
					continue
				sim_method = getattr(sim, name)
				if sim_method is method:
					continue
				args = inspect.getargspec(sim_method)[0]
				if args != ['self', 'shutit']:
					continue
				local[name] = shutit_method_scope(method)

		cls = super(ShutItMeta, mcs).__new__(mcs, name, bases, local)
		if name == 'ShutItModule':
			mcs.ShutItModule = cls
		return cls


class ShutItModule(with_metaclass(ShutItMeta)):
	"""Class that takes a ShutIt object and defines what a ShutIt module must
	implement to be registered.

	Build order:

		- Gather core config (build, remove, tag)
		- Gather module-specific config
		- FOR MODULE 0
			- Build module 0
		- FOR ALL MODULES:
		- Determine dependency requirements are met
		- Determine conflict requirements are met.
			- Remove any modules that are configured for removal.
			- Build if not installed
			- Do repo work if not installed (commit, tag, push)
			- Test all modules (in reverse)
			- Finalize all modules
		- FOR MODULE 0
			- Do repo work on build
	"""

	def __init__(self, module_id, run_order, description='', maintainer='', depends=None, conflicts=None, delivery_methods=[]):
		"""Constructor.
		Sets up module_id, run_order, deps and conflicts.
		Also checks types for safety.
		"""
		# Module id for the module (a string).
		# Following the Java standard is recommended, eg 'com.bigcorp.project.alpha.mymodule'
		# Duplicate module ids are rejected if within the configured
		# shutit_module_path.
		self.module_id = module_id
		if not isinstance(module_id, str):
			err = str(module_id) + '\'s module_id is not a string'
			print(err)
			raise ShutItModuleError(err)
		# run_order for the module (a float).
		# It should be a float and not duplicated within the shutit_module path.
		# Module 0 is special. It is expected to:
		#   - Set up a target (see shutit_setup.py)
		#   - Set up pexpect children with relevant keys and populate
		#     shutit_global.shutit_pexpect_children.
		if (isinstance(run_order, float) or
			isinstance(run_order, str) or
			isinstance(run_order, int)):
			run_order = decimal.Decimal(run_order)
		# Check that run_order is a float - this will throw an error as a 
		# side effect if float doesn't work.
		if not isinstance(run_order, decimal.Decimal):
			err = module_id + '\'s run order is not a decimal'
			print(err)
			raise ShutItModuleError(err)
		self.run_order = run_order
		# module ids depended on
		self.depends_on     = []
		if depends is not None:
			self.depends_on = [dep for dep in depends]
		# module ids this is known to conflict with.
		self.conflicts_with = []
		if conflicts is not None:
			self.conflicts_with = [conflict for conflict in conflicts]
		self.description = description
		self.maintainer  = maintainer
		if delivery_methods == [] or delivery_methods == '':
			# default to all
			delivery_methods = ['ssh','dockerfile','bash','docker']
		if type(delivery_methods) == str:
			delivery_methods = [delivery_methods]
		self.ok_delivery_methods = delivery_methods


	########################################################################
	# Abstract methods
	########################################################################
	def get_config(self, shutit):
		"""Gets all config items necessary for this module to be built
		"""
		return True

	def check_ready(self, shutit):
		"""Checks whether we are ready to build this module.

		This is called before the build, to ensure modules have
		their requirements in place before we commence the build.
		Checking whether the build will happen at all (and
		therefore whether the check should take place) will be
		determined by the framework.
		
		Should return True if it's ready to run, else False.
		"""
		return True

	def remove(self, shutit):
		"""Remove the module, which should ensure the module has been deleted
		from the system.
		
		Returns True if all removed without any errors, else False.
		"""
		return False

	def start(self, shutit):
		"""Run when module should be installed (is_installed() or configured
		to build is true)
		Run after repository work.
		Returns True if all started ok.
		"""
		return True

	def stop(self, shutit):
		"""Runs when module should be stopped.
		Runs before repo work, and before finalize is called.
		Returns True if all stopped ok.
		"""
		return True

	def is_installed(self, shutit):
		"""Determines whether the module has been built in this target host
		already.
		
		Returns True if it is certain it's there, else False.
		
		Required.
		"""
		return shutit.is_shutit_installed(self.module_id)

	@abstractmethod
	def build(self, shutit):
		"""Runs the build part of the module, which should ensure the module has been set up.  If is_installed determines that the module is already there, this is not run.
		
		Returns True if it has succeeded in building, else False.
		
		Required.
		"""
		pass

	def test(self, shutit):
		"""Tests the module is OK.
		Returns True if all is OK, else False.
		This is run regardless of whether the module is installed or not.
		"""
		return True

	def finalize(self, shutit):
		"""Finalize the module, ie do things that need doing after final module
		has been run and before we exit, eg updatedb.
		"""
		return True

