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
import logging
import sys
import shutit_threads
import shutit_global
import shutit_util


def create_session(session_type='bash',
                   docker_image=None,
                   rm=None,
                   echo=False,
                   walkthrough=False,
                   nocolor=False,
                   video=-1,
                   loglevel='WARNING'):
	assert session_type in ('bash','docker'), shutit_util.print_debug()
	shutit_global_object = shutit_global.shutit_global_object
	if video != -1 and video > 0:
		walkthrough = True
	return shutit_global_object.create_session(session_type,
	                                           docker_image=docker_image,
	                                           rm=rm,
	                                           echo=echo,
	                                           walkthrough=walkthrough,
	                                           walkthrough_wait=video,
	                                           nocolor=nocolor,
	                                           loglevel=loglevel)


def main():
	"""Main ShutIt function.

	Handles the configured actions:

		- skeleton     - create skeleton module
		- list_configs - output computed configuration
		- depgraph     - output digraph of module dependencies
	"""
	# Create base shutit object.
	shutit = shutit_global.shutit_global_object.shutit_objects[0]
	if sys.version_info[0] == 2:
		if sys.version_info[1] < 7:
			shutit.fail('Python version must be 2.7+') # pragma: no cover
	try:
		shutit.setup_shutit_obj()
	except KeyboardInterrupt:
		shutit_util.print_debug(sys.exc_info())
		shutit_global.shutit_global_object.log('Keyboard interrupt caught, exiting with status 1', level=logging.CRITICAL)
		sys.exit(1)


shutit_version='1.0.124'

if __name__ == '__main__':
	shutit_global.setup_signals()
	main()
