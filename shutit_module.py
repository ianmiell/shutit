#Copyright (C) 2014 OpenBet Limited
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from abc import ABCMeta, abstractmethod
import sys
import decimal

# Abstract class that defines what a ShutIt module must implement to be registered.

class ShutItModule:
	__metaclass__ = ABCMeta

	########################################################################
	# Build order:
	########################################################################
	# - Gather core config (build, remove, tag)
	# - Gather module-specific config
	# - FOR MODULE 0
	#     - Build module 0
	# - FOR ALL MODULES:
	# - Determine dependency requirements are met
	# - Determine conflict requirements are met.
	#     - Remove any modules that are configured for removal.
	#     - Build if not installed
	#     - Cleanup if not installed
	#     - Do repo work if not installed (commit, tag, push)
	#     - Test all modules (in reverse)
	#     - Finalize all modules
	# - FOR MODULE 0
	#     - Do repo work on build

	########################################################################
	# Constructor
	########################################################################
	def __init__(self,module_id,run_order):
		# Module id for the module (a string).
		# Following the Java standard is recommended, eg 'com.bigcorp.project.alpha.mymodule'
		# Duplicate module ids are rejected if within the configured shutit_module_path.
		self.module_id = module_id
		if not isinstance(module_id,str):
			print(str(module_id) + '\'s module_id is not a string')
			sys.exit(1)
		# run_order for the module (a float).
		# It should be a float and not duplicated within the shutit_module path.
		# Module 0 is special. It is expected to:
		#   - Set up a container (see setup.py)
		#   - Set up pexpect children with relevant keys and populate shutit_global.pexpect_children.
		if isinstance(run_order,float) or isinstance(run_order,str) or isinstance(run_order,int):
			run_order = decimal.Decimal(run_order)
		if not isinstance(run_order,decimal.Decimal):
			print(str(run_order) + '\'s module_id is not a decimal')
			sys.exit(1)
		self.run_order = run_order
		# Check that run_order is a float - this will throw an error as a side effect if float doesn't work.
		if not isinstance(run_order,decimal.Decimal):
			print(module_id + '\'s run order is not a decimal')
			sys.exit(1)
		# module ids depended on
		self.depends_on     = []
		# module ids this is known to conflict with.
		self.conflicts_with = []


	########################################################################
	# config_dict
	########################################################################
	# a dictionary which stores all the configuration for the build.
	# module configuration is stored within config_dict[module.module_id][config_item]

	########################################################################
	# Helper methods.
	########################################################################
	# each object can handle config
	def get_config(self,config_dict):
		return config_dict

	# set the run order (see __init__)
	def set_run_order(self,order):
		self.run_order = order

	# add a dependency (see __init__)
	def add_dependency(self,dependency):
		self.depends_on.append(dependency)

	# add a conflict (see __init__)
	def add_conflict(self,conflict):
		self.conflicts_with.append(conflict)

	########################################################################
	# Abstract methods
	########################################################################

	# check_ready
	# 
	# Check whether we are ready to build this module.
	# 
	# This is called before the build, to ensure modules have 
	# their requirements in place (eg files required to be mounted 
	# in /resources). Checking whether the build will happen (and
	# therefore whether the check should take place) will be 
	# determined by the framework.
	# 
	# Should return True if it ready, else False.
	#
	# Required.
	def check_ready(self,config_dict):
		return True

	# remove
	# 
	# Remove the module, which should ensure the module has been deleted 
	# from the system.
	#
	# Should return True if it has succeeded in removing, else False.
	def remove(self,config_dict):
		return False

	# start
	#
	# Run when module should be installed (is_installed() or configured to build is true)
	# Run after repo work.
	@abstractmethod
	def start(self,config_dict):
		return False

	# stop
	#
	# Run when module should be stopped.
	# Run before repo work, and before finalize is called.
	@abstractmethod
	def stop(self,config_dict):
		return False

	# is_installed
	#
	# Determines whether the module has been built in this container
	# already.
	#
	# Should return True if it is certain it's there, else False.
	#
	# Required.
	@abstractmethod
	def is_installed(self,config_dict):
		return False

	# build
	#
	# Run the build part of the module, which should ensure the module
	# has been set up.
	# If is_installed determines that the module is already there,
	# this is not run.
	#
	# Should return True if it has succeeded in building, else False.
	#
	# Required.
	@abstractmethod
	def build(self,config_dict):
		return False


	# cleanup
	#
	# Cleanup the module, ie clear up stuff not needed for the rest of the build, eg tar files removed, apt-get cleans.
	# Should return True if all is OK, else False.
	# Note that this is only run if the build phase was actually run.
	#
	# Required.
	@abstractmethod
	def cleanup(self,config_dict):
		return False

	# test
	#
	# Test the module is OK.
	# Should return True if all is OK, else False.
	# This is run regardless of whether the module is installed or not.
	#
	# Required.
	@abstractmethod
	def test(self,config_dict):
		return False

	# finalize
	#
	# Finalize the module, ie do things that need doing before we exit.
	#
	# Required.
	@abstractmethod
	def finalize(self,config_dict):
		return False

