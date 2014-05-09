import os
import json
import copy

from bottle import route, run, request

import shutit_main
import shutit_global
import util

orig_mod_cfg = {}
shutit = None

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

	for mid in shutit.shutit_map:
		orig_mod_cfg[mid] = shutit.cfg[mid]

start_shutit()

index_html = '''
<html>
<body>
<div id="loading" style="visibility: hidden; padding: 10px; background-color: yellow;">LOADING</div>
Modules:
<ul id="mods"></ul>
Errors:
<ul id="errs"></ul>
<script>
'use strict';
function getmodules(mid_list) {
	var r = new XMLHttpRequest();
	r.open('POST', '/info', true);
	r.setRequestHeader("Content-type", "application/json");
	r.onreadystatechange = function () {
		if (r.readyState != 4 || r.status != 200) return;
		updatedoc(r.responseText);
	};
	r.send(JSON.stringify({'to_build': mid_list}));
}
function updatedoc(info) {
	var info = JSON.parse(info);
	var errsElt = document.getElementById('errs');

	errsElt.innerHTML = '';
	info.errs.map(function (e) {
		var elt = document.createElement('li');
		elt.textContent = e;
		errsElt.appendChild(elt);
	});

	var modsElt = document.getElementById('mods');
	if (document.querySelectorAll('#mods > li').length == 0) {
		info.modules.map(function (m) {
			modsElt.appendChild(setupmodule(m));
		});
	}
	info.modules.map(function (m) {
		var elt = document.getElementById(m.module_id);
		if (m.build) {
			elt.style.fontWeight = 'bold';
		} else {
			elt.style.fontWeight = '';
		}
	});
	toggleloading(false);
}
function setupmodule(m) {
	var elt = document.createElement('li');
	elt.id = m.module_id;
	var checkbox = document.createElement('input');
	checkbox.type = 'checkbox';
	checkbox.addEventListener('change', changelistener);
	var desc = document.createElement('span');
	desc.textContent = m.module_id + ' - ' + m.run_order;
	elt.appendChild(checkbox);
	elt.appendChild(desc);
	return elt;
}
function changelistener() {
	toggleloading(true);
	var midlist = [];
	// qsa doesn't return an array
	[].slice.call(document.querySelectorAll('#mods > li')).map(function (e) {
		if (e.children[0].checked) {
			midlist.push(e.id);
		}
	});
	getmodules(midlist);
}
function toggleloading(loading) {
	var elts = [].slice.call(document.querySelectorAll('#mods > li'))
	if (loading) {
		document.getElementById('loading').style.visibility = '';
	} else {
		document.getElementById('loading').style.visibility = 'hidden';
	}
	elts.map(function (e) {
		e.children[0].disabled = loading;
	});
}
getmodules([]);
</script>
</body>
</html>
'''

@route('/info', method='POST')
def info():
	shutit.cfg.update(copy.deepcopy(orig_mod_cfg))

	for mid in request.json['to_build']:
		shutit.cfg[mid]['build'] = True

	errs = []
	errs.extend(shutit_main.check_deps(shutit))
	errs.extend(shutit_main.check_conflicts(shutit))
	errs.extend(shutit_main.check_ready(shutit))

	return json.dumps({
		'errs': [err[0] for err in errs],
		'modules': [
			{
				"module_id": mid,
				"run_order": float(shutit.shutit_map[mid].run_order),
				"build": shutit.cfg[mid]['build']
			} for mid in shutit_main.module_ids(shutit)
		]
	})

@route('/')
def index():
	return index_html

if __name__ == '__main__':
	host = os.environ.get('SHUTIT_HOST', 'localhost')
	port = int(os.environ.get('SHUTIT_PORT', 8080))
	run(host=host, port=port, debug=True)
