import os
from bottle import route, run, template

import shutit_main
import shutit_global

config_dict = None
shutit_map = None

def start_shutit():
	global config_dict
	global shutit_map
	config_dict = shutit_global.config_dict
	shutit_map = shutit_main.shutit_init(config_dict)
	shutit_main.config_collection(config_dict, shutit_map)
	shutit_main.build_core_module(config_dict, shutit_map)

start_shutit()

index_html = '''
<html>
<body>
Modules:
<ul>
	% for mid in module_ids:
		<li>
			{{ mid }} -
				{{ config_dict[mid]['build'] }} -
				{{ shutit_map[mid].run_order }}
		</li>
	% end
</ul>
Errors:
<ul>
	% for err in errs:
		<li>{{ err }}</li>
	% end
</ul>
</body>
</html>
'''

@route('/')
def index():
	errs = []
	if not errs: errs = shutit_main.check_deps(config_dict, shutit_map)
	if not errs: errs = shutit_main.check_conflicts(config_dict, shutit_map)
	if not errs: errs = shutit_main.check_ready(config_dict, shutit_map)
	return template(
		index_html,
		errs=errs,
		module_ids=shutit_main.module_ids(shutit_map),
		shutit_map=shutit_map,
		config_dict=config_dict
	)

if __name__ == '__main__':
	host = os.environ.get('SHUTIT_HOST', 'localhost')
	port = int(os.environ.get('SHUTIT_PORT', 8080))
	run(host=host, port=port, debug=True)
