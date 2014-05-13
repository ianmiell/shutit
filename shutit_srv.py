import os
import json
import copy
import threading
import StringIO

import bottle
from bottle import route, request, static_file

import shutit_main
import shutit_global
import util

orig_mod_cfg = {}
shutit = None
STATUS = {
	'build_done': False,
	'build_started': False,
	'modules': [],
	'errs': []
}

def start_shutit():
	global shutit
	global orig_mod_cfg
	shutit = shutit_global.shutit

	util.parse_args(shutit.cfg)
	util.load_configs(shutit)
	util.load_shutit_modules(shutit)
	shutit_main.init_shutit_map(shutit)
	shutit_main.config_collection(shutit)
	shutit_main.build_core_module(shutit)

	shutit.cfg['build']['build_log'] = StringIO.StringIO()

	for mid in shutit.shutit_map:
		orig_mod_cfg[mid] = shutit.cfg[mid]

def build_shutit():
	global STATUS
	shutit_main.do_remove(shutit)
	shutit_main.do_build(shutit)
	shutit_main.do_test(shutit)
	shutit_main.do_finalize(shutit)
	STATUS["build_done"] = True

start_shutit()

@route('/info', method='POST')
def info():
	global STATUS
	shutit.cfg.update(copy.deepcopy(orig_mod_cfg))

	selected = set(request.json['to_build'])
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

	return json.dumps(STATUS)

@route('/log', method='POST')
def log():
	cmd_offset, log_offset = request.json
	return json.dumps({
		"cmds": shutit.shutit_command_history[cmd_offset:],
		"logs": shutit.cfg['build']['build_log'].getvalue()[log_offset:]
	})

@route('/build', method='POST')
def build():
	global STATUS
	if not STATUS["build_started"]:
		STATUS["build_started"] = True
		t = threading.Thread(target=build_shutit)
		t.daemon = True
		t.start()
	return json.dumps(STATUS)

@route('/')
def index():
	return static_file('index.html', root='./web')

@route('/static/<path:path>.js')
def static_srv(path):
	return static_file(path + '.js', root='./web')

if __name__ == '__main__':
	host = os.environ.get('SHUTIT_HOST', 'localhost')
	port = int(os.environ.get('SHUTIT_PORT', 8080))
	bottle.debug(True)
	bottle.run(host=host, port=port)
