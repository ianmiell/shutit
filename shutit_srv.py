import os
import json
import copy

from bottle import route, run, request, static_file

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

def build_shutit():
	shutit_main.do_remove(shutit)
	shutit_main.do_build(shutit)
	shutit_main.do_test(shutit)
	shutit_main.do_finalize(shutit)

start_shutit()

index_html = '''
<html>
<head>
<script src="/static/react-0.10.0.min.js"></script>
<script src="/static/JSXTransformer-0.10.0.js"></script>
</head>
<body>
<div id="ShutItUI"></div>
<script type="text/jsx">
/** @jsx React.DOM */
'use strict';
function copy(obj) {
	var newObj = {};
	for (var key in obj) {
		if (obj.hasOwnProperty(key)) {
			newObj[key] = obj[key];
		}
	}
	return newObj;
}
function jsonpost(url, data, cb) {
	var r = new XMLHttpRequest();
	r.open('POST', url, true);
	r.setRequestHeader('Content-type', 'application/json');
	r.onreadystatechange = (function () {
		if (r.readyState != 4 || r.status != 200) return;
		cb(JSON.parse(r.responseText));
	});
	r.send(JSON.stringify(data));
}

var StatusIndicator = React.createClass({
	render: function () {
		var style = {
			visibility: this.props.loading ? '' : 'hidden',
			padding: '10px',
			backgroundColor: 'yellow'
		}
		return <div style={style}>LOADING</div>;
	}
});
var ModuleListItem = React.createClass({
	handleChange: function (property, event) {
		var value, elt = event.target;
		if (elt.type && elt.type === 'checkbox') {
			value = elt.checked;
		} else {
			throw Error('unknown value');
		}
		this.props.onChange(this.props.module.module_id, property, value);
	},
	render: function () {
		return (
			<li id="{this.props.module.module_id}">
				<input type="checkbox" checked={this.props.module.selected}
					disabled={this.props.loading}
					onChange={this.handleChange.bind(this, 'selected')}></input>
				<span style={{fontWeight: this.props.module.build ? 'bold' : ''}}>
					{this.props.module.module_id}
					- {this.props.module.run_order}
					{this.props.module.build}</span>
			</li>
		)
	}
});
var ModuleList = React.createClass({
	handleChange: function (module_id, property, value) {
		this.props.onChange(module_id, property, value);
	},
	render: function () {
		var moduleItems = this.props.modules.map((function (module) {
			return <ModuleListItem
				module={module}
				loading={this.props.loading}
				key={module.module_id}
				onChange={this.handleChange} />;
		}).bind(this));
		return <div>Modules: <ul>{moduleItems}</ul></div>;
	}
});
var ErrList = React.createClass({
	render: function () {
		var errs = this.props.errs.map(function (err, i) {
			return <li key={i}>{err}</li>;
		});
		return <div>Errors: <ul>{errs}</ul></div>;
	}
});
var BuildProgress = React.createClass({
	getInitialState: function () {
		return {lines: [], loading: false};
	},
	getNewLines: function () {
		if (!this.props.building || this.state.loading) { return; }
		var loadingstate = copy(this.state);
		loadingstate.loading = true;
		this.setState(loadingstate);
		jsonpost('/log', this.state.lines.length, (function (data) {
			var newstate = {
				lines: this.state.lines.concat(data.lines),
				loading: false
			};
			this.setState(newstate);
		}).bind(this));
	},
	componentWillMount: function () {
		setInterval(this.getNewLines, 1000);
	},
	render: function () {
		var elts = this.state.lines.map(function (line, i) {
			return <div key={i}>{line}</div>;
		});
		return (
			<div style={{width: '500px', height: '500px', overflow: 'scroll'}}>
				{elts}
			</div>
		);
	}
});
var ShutItUI = React.createClass({
	getInfo: function (newstate) {
		var loadingstate = copy(this.state);
		loadingstate.loading = true;
		this.setState(loadingstate);
		var mid_list = [];
		newstate.modules.map(function (module) {
			if (module.selected) {
				mid_list.push(module.module_id);
			}
		})
		jsonpost('/info', {to_build: mid_list}, (function (verifiedstate) {
			verifiedstate.loading = false;
			this.setState(verifiedstate);
		}).bind(this));
	},
	beginBuild: function () {
		var newstate = copy(this.state);
		newstate.loading = true;
		newstate.building = true;
		this.setState(newstate);
		jsonpost('/build', '', (function (success) {
			var newstate = copy(this.state);
			newstate.loading = false;
			newstate.building = false;
			this.setState(newstate);
		}).bind(this));
	},
	getInitialState: function () {
		return {modules: [], errs: [], loading: false, building: false};
	},
	componentWillMount: function () {
		this.getInfo(this.state);
	},
	handleChange: function (module_id, property, value) {
		var newstate = copy(this.state);
		for (var i = 0; i < newstate.modules.length; i++) {
			if (newstate.modules[i].module_id === module_id) {
				newstate.modules[i][property] = value;
				break;
			}
		}
		this.getInfo(newstate);
	},
	render: function () {
		return (
			<div>
				<StatusIndicator loading={this.state.loading} />
				<ModuleList onChange={this.handleChange}
					loading={this.state.loading} modules={this.state.modules} />
				<ErrList errs={this.state.errs} />
				<button onClick={this.beginBuild}>Begin build</button>
				<BuildProgress building={this.state.building} />
			</div>
		);
	}
});
React.renderComponent(
	<ShutItUI />,
	document.getElementById('ShutItUI')
);
</script>
</body>
</html>
'''

@route('/info', method='POST')
def info():
	shutit.cfg.update(copy.deepcopy(orig_mod_cfg))

	selected = set(request.json['to_build'])
	for mid in selected:
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
				"build": shutit.cfg[mid]['build'],
				"selected": mid in selected
			} for mid in shutit_main.module_ids(shutit)
		]
	})

@route('/log', method='POST')
def log():
	offset = request.json
	return json.dumps({"lines": shutit.shutit_command_history[offset:]})

@route('/build', method='POST')
def build():
	build_shutit()
	return 'true'

@route('/')
def index():
	return index_html

@route('/static/<path:path>')
def static_srv(path):
	return static_file(path, root='./web')

if __name__ == '__main__':
	host = os.environ.get('SHUTIT_HOST', 'localhost')
	port = int(os.environ.get('SHUTIT_PORT', 8080))
	run(host=host, port=port, debug=True)
