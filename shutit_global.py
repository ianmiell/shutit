#The MIT License (MIT)
#
#Copyright (C) 2014 OpenBet Limited
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of
#this software and associated documentation files (the "Software"), to deal in
#the Software without restriction, including without limitation the rights to
#use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#of the Software, and to permit persons to whom the Software is furnished to do
#so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#ITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.


import os
import socket
import time
import util
import sets

def init(): 
	global pexpect_children
	global shutit_modules
	global shutit_main_dir
	global config_dict
	global cwd
	global shutit_command_history

	pexpect_children = {}
	shutit_modules   = sets.Set([])
	shutit_command_history = []
	# Store the root directory of this application.
	# http://stackoverflow.com/questions/5137497/find-current-directory-and-files-directory
	shutit_main_dir = os.path.abspath(os.path.dirname(__file__))
	cwd = os.getcwd()
	
	config_dict = {}
	config_dict['build']                = {}
	config_dict['build']['interactive'] = True # Default to true until we know otherwise
	config_dict['build']['build_log']   = {}
	config_dict['build']['report']      = ''
	config_dict['container']            = {}
	#config_dict['container']['docker_image_default'] = 'stackbrew/ubuntu' # Statically set up here as needed before general config setup made.
	config_dict['container']['docker_image_default'] = 'ubuntu:12.04' # Statically set up here as needed before general config setup made.
	config_dict['host']                 = {}
	config_dict['repository']           = {}
	config_dict['expect_prompts']       = {}
	config_dict['users']                = {}
	
	username = os.environ['LOGNAME']
	if username == 'root':
		util.fail('You cannot be root to run this script')
	try:
		# Get the real username
		config_dict['host']['real_user'] = os.environ['SUDO_USER']
	except:
	        config_dict['host']['real_user'] = username
	config_dict['build']['build_id']    = socket.gethostname() + '_' + config_dict['host']['real_user'] + '_' + str(time.time())

init()
