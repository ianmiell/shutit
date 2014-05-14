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
import json
import copy
import threading
import StringIO

import bottle
from bottle import route, request, static_file

import shutit_main
import shutit_global
from shutit_module import ShutItException
import util

orig_mod_cfg = {}
shutit = None
STATUS = {
	'build_done': False,
	'build_started': False,
	'modules': [],
	'errs': []
}

def build_shutit():
	global STATUS
	try:
		shutit_main.do_remove(shutit)
		shutit_main.do_build(shutit)
		shutit_main.do_test(shutit)
		shutit_main.do_finalize(shutit)
	except ShutItException as e:
		STATUS['errs'] = [e.message]
	STATUS["build_done"] = True

def update_modules(to_build):
	global STATUS
	shutit.cfg.update(copy.deepcopy(orig_mod_cfg))

	selected = set(to_build)
	for mid in selected:
		shutit.cfg[mid]['build'] = True

	errs = []
	errs.extend(shutit_main.check_deps(shutit))
	errs.extend(shutit_main.check_conflicts(shutit))
	errs.extend(shutit_main.check_ready(shutit))

	STATUS['errs'] = [err[0] for err in errs]
	STATUS['modules'] = [
		{
			"module_id": mid,
			"run_order": float(shutit.shutit_map[mid].run_order),
			"build": shutit.cfg[mid]['build'],
			"selected": mid in selected
		} for mid in shutit_main.module_ids(shutit)
	]

@route('/info', method='POST')
def info():
	global STATUS
	if 'to_build' in request.json:
		update_modules(request.json['to_build'])
	if 'build' in request.json:
		if not STATUS["build_started"]:
			STATUS["build_started"] = True
			t = threading.Thread(target=build_shutit)
			t.daemon = True
			t.start()
	return json.dumps(STATUS)

@route('/log', method='POST')
def log():
	cmd_offset, log_offset = request.json
	return json.dumps({
		"cmds": shutit.shutit_command_history[cmd_offset:],
		"logs": shutit.cfg['build']['build_log'].getvalue()[log_offset:]
	})

@route('/')
def index():
	return static_file('index.html', root='./web')

@route('/static/<path:path>.js')
def static_srv(path):
	return static_file(path + '.js', root='./web')

def start():
	global shutit
	global orig_mod_cfg

	# Some hacks for server mode
	shutit = shutit_global.shutit
	shutit.cfg['build']['build_log'] = StringIO.StringIO()
	for mid in shutit.shutit_map:
		orig_mod_cfg[mid] = shutit.cfg[mid]
	update_modules([])

	# Start the server
	host = os.environ.get('SHUTIT_HOST', 'localhost')
	port = int(os.environ.get('SHUTIT_PORT', 8080))
	bottle.debug(True)
	bottle.run(host=host, port=port)

if __name__ == '__main__':
	print "PLEASE START VIA SHUTIT_MAIN INSTEAD"
