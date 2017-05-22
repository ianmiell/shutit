#!/usr/bin/env python
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



"""ShutIt is a means of building stateless target hosts in a flexible and predictable way.
"""
from __future__ import print_function
from distutils import spawn
import logging
import os
import re
import signal
import sys
import urllib
import shutit_global
import shutit_skeleton
import shutit_util
from shutit_module import ShutItModule


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
				shutit.login(prompt_prefix=module_id,command='bash --noprofile --norc',echo=False)
				if not shutit.shutit_map[module_id].finalize(shutit):
						shutit.fail(module_id + ' failed on finalize', shutit_pexpect_child=shutit.get_shutit_pexpect_session_from_id('target_child').pexpect_child) # pragma: no cover
				shutit.logout(echo=False)
		for shutit in shutit_global.shutit_global_object.shutit_objects:
			_finalize(shutit)


def main():
	"""Main ShutIt function.

	Handles the configured actions:

		- skeleton     - create skeleton module
		- list_configs - output computed configuration
		- depgraph     - output digraph of module dependencies
	"""
	shutit = shutit_global.shutit_global_object.shutit_objects[0]
	if sys.version_info.major == 2:
		if sys.version_info.minor < 7:
			shutit.fail('Python version must be 2.7+') # pragma: no cover
	shutit.setup_shutit_obj()


def setup_signals():
	signal.signal(signal.SIGINT, shutit_util.ctrl_c_signal_handler)
	signal.signal(signal.SIGQUIT, shutit_util.ctrl_quit_signal_handler)

def create_session(session_type='bash'):
	assert session_type in ('bash','docker')
	shutit_global_object = shutit_global.shutit_global_object
	return shutit_global_object.create_session(session_type)

shutit_version='0.9.365'

if __name__ == '__main__':
	setup_signals()
	main()
