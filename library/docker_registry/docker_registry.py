"""ShutIt module. See http://shutit.tk
"""
#Copyright (C) 2014 OpenBet Limited
#
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is furnished
#to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
#FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
#COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
#IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from shutit_module import ShutItModule
import os

class docker_registry(ShutItModule):

	def is_installed(self,shutit):
		return False

	def build(self,shutit):
		shutit.install('gunicorn')
		shutit.install('git')
		shutit.send_and_expect('pushd /')
		shutit.send_and_expect('git clone https://github.com/dotcloud/docker-registry.git')
		shutit.send_and_expect('popd')
		shutit.send_file('/docker-registry/run.sh',"""
			#!/bin/bash
			if [[ -z "$GUNICORN_WORKERS" ]] ; then
			    GUNICORN_WORKERS=""" + shutit.cfg['shutit.tk.docker_registry.docker_registry']['gunicorn_workers'] + """
			fi
			
			if [[ -z "$REGISTRY_PORT" ]] ; then
			    REGISTRY_PORT=""" + shutit.cfg['shutit.tk.docker_registry.docker_registry']['registry_port'] + """
			fi
			
			cd "$(dirname $0)"
			# Increase timeout as it's low by default
			gunicorn --access-logfile - --debug --max-requests """ + shutit.cfg['shutit.tk.docker_registry.docker_registry']['gunicorn_max_requests'] + """ --graceful-timeout """ + shutit.cfg['shutit.tk.docker_registry.docker_registry']['gunicorn_timeout'] + """ -t """ + shutit.cfg['shutit.tk.docker_registry.docker_registry']['gunicorn_timeout'] + """ -k gevent -b 0.0.0.0:$REGISTRY_PORT -w $GUNICORN_WORKERS wsgi:application
			""")

		return True

	def get_config(self,shutit):
		shutit.get_config('shutit.tk.docker_registry.docker_registry','registry_port','5000')
		shutit.get_config('shutit.tk.docker_registry.docker_registry','gunicorn_timeout','10000000')
		shutit.get_config('shutit.tk.docker_registry.docker_registry','gunicorn_max_requests','100')
		shutit.get_config('shutit.tk.docker_registry.docker_registry','gunicorn_workers','4')
		return True

def module():
	return docker_registry(
		'shutit.tk.docker_registry.docker_registry', 0.802,
		depends=['shutit.tk.setup']
	)

