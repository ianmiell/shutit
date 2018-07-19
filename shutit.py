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
import shutit_global
import shutit_util


def create_session(session_type='bash',
                   docker_image=None,
                   vagrant_image='ubuntu/xenial64',
                   vagrant_provider='virtualbox',
                   gui=False,
                   memory='1024',
                   swapsize='2G',
                   rm=None,
                   echo=False,
                   walkthrough=False,
                   nocolor=False,
                   video=-1,
                   vagrant_version='1.8.6',
                   virt_method='virtualbox',
                   session_name=None,
                   num_machines='1',
                   root_folder=None,
                   loglevel='WARNING'):
	assert session_type in ('bash','docker','vagrant'), shutit_util.print_debug()
	shutit_global_object = shutit_global.shutit_global_object
	if video != -1 and video > 0:
		walkthrough = True
	if session_type in ('bash','docker'):
		return shutit_global_object.create_session(session_type,
		                                           docker_image=docker_image,
		                                           rm=rm,
		                                           echo=echo,
		                                           walkthrough=walkthrough,
		                                           walkthrough_wait=video,
		                                           nocolor=nocolor,
		                                           loglevel=loglevel)
	elif session_type == 'vagrant':
		assert session_name is not None
		if isinstance(num_machines, int):
			num_machines = str(num_machines)
		assert isinstance(num_machines, str)
		assert isinstance(int(num_machines), int)
		if root_folder is None:
			root_folder = shutit_global.shutit_global_object.owd
		return create_session_vagrant(session_name,
		                              num_machines,
		                              vagrant_image,
		                              vagrant_provider,
		                              gui,
		                              memory,
		                              swapsize,
		                              echo,
		                              walkthrough,
		                              nocolor,
		                              video,
		                              vagrant_version,
		                              virt_method,
		                              root_folder,
		                              loglevel)


def create_session_vagrant(session_name,
                           num_machines,
                           vagrant_image,
                           vagrant_provider,
                           gui,
                           memory,
                           swapsize,
                           echo,
                           walkthrough,
                           nocolor,
                           video,
                           vagrant_version,
                           virt_method,
                           root_folder,
                           loglevel):
	if video != -1 and video > 0:
		walkthrough = True
	assert isinstance(memory, str)
	assert isinstance(swapsize, str)
	return shutit_global.shutit_global_object.create_session_vagrant(session_name,
	                                                                 num_machines,
	                                                                 vagrant_image,
	                                                                 vagrant_provider,
	                                                                 gui,
	                                                                 memory,
	                                                                 swapsize,
	                                                                 echo,
	                                                                 walkthrough,
	                                                                 video,
	                                                                 nocolor,
	                                                                 vagrant_version,
	                                                                 virt_method,
	                                                                 root_folder,
	                                                                 loglevel)

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
		shutit_global.shutit_global_object.shutit_print('Keyboard interrupt caught, exiting with status 1')
		sys.exit(1)


shutit_version='1.0.135'

if __name__ == '__main__':
	shutit_global.setup_signals()
	main()
