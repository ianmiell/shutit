import os
import json

from bottle import route, run, request

import shutit_main
import shutit_global

config_dict = None
orig_mod_config_dict = {}
shutit_map = None

def start_shutit():
	global config_dict
	global orig_mod_config_dict
	global shutit_map
	config_dict = shutit_global.config_dict
	shutit_map = shutit_main.shutit_init(config_dict)
	shutit_main.config_collection(config_dict, shutit_map)
	shutit_main.build_core_module(config_dict, shutit_map)
	for mid in shutit_map:
		orig_mod_config_dict[mid] = config_dict[mid]

start_shutit()

index_html = '''
<html>
<body>
Modules:
<ul id="mods"></ul>
Errors:
<ul id="errs"></ul>
<script>
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
		elt.children[0].textContent =
			m.module_id + ' - ' + m.build + ' - ' + m.run_order;
	});
}
function setupmodule(m) {
	var elt = document.createElement('li');
	var desc = document.createElement('span');
	elt.id = m.module_id;
	elt.appendChild(desc);
	return elt;
}
getmodules([]);
</script>
</body>
</html>
'''

@route('/info', method='POST')
def info():
	config_dict.update(orig_mod_config_dict)

	for mid in request.json['to_build']:
		config_dict[mid]['build'] = True

	errs = []
	if not errs: errs = shutit_main.check_deps(config_dict, shutit_map)
	if not errs: errs = shutit_main.check_conflicts(config_dict, shutit_map)
	if not errs: errs = shutit_main.check_ready(config_dict, shutit_map)

	return json.dumps({
		'errs': errs,
		'modules': [
			{
				"module_id": mid,
				"run_order": float(shutit_map[mid].run_order),
				"build": config_dict[mid]['build']
			} for mid in shutit_main.module_ids(shutit_map)
		]
	})

@route('/')
def index():
	return index_html

if __name__ == '__main__':
	host = os.environ.get('SHUTIT_HOST', 'localhost')
	port = int(os.environ.get('SHUTIT_PORT', 8080))
	run(host=host, port=port, debug=True)
