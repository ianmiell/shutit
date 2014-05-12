import os
import json
import copy
import threading

from bottle import route, run, request, static_file

import shutit_main
import shutit_global
import util

orig_mod_cfg = {}
shutit = None
build_done = False
build_started = False

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
	global build_done
	shutit_main.do_remove(shutit)
	shutit_main.do_build(shutit)
	shutit_main.do_test(shutit)
	shutit_main.do_finalize(shutit)
	build_done = True

start_shutit()

index_html = '''
<html>
<head>
<script src="/static/react-0.10.0.min.js"></script>
<script src="/static/JSXTransformer-0.10.0.js"></script>
<style>
#commandLog {
	width: 500px; height: 500px; right: 0; top: 0; position: fixed;
	overflow-y: scroll; border-width: 1px; border-style: solid;
}
#statusBar { padding: 10px; margin-bottom: 10px; height: 50px; width: 200px; }
pre { margin: 0; padding: 0; }
</style>
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
		var color = 'transparent', text = '';
		if (this.props.done) { color = "green"; text = "done"; }
		else if (this.props.building) { color = "purple"; text = "building"; }
		else if (this.props.loading) { color = "yellow"; text = "loading"; }
		var style = {
			visibility: color === 'transparent' ? 'hidden' : '',
			backgroundColor: color
		}
		return <div id="statusBar" style={style}>{text.toUpperCase()}</div>;
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
					disabled={this.props.noInput}
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
				noInput={this.props.noInput}
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
		return {lines: [], loadingLog: false, interval: 0};
	},
	getNewLines: function () {
		if (this.props.done) { clearInterval(this.state.interval); }
		if (!this.props.building || this.state.loadingLog) { return; }
		var loadingstate = copy(this.state);
		loadingstate.loadingLog = true;
		this.setState(loadingstate);
		jsonpost('/log', this.state.lines.length, (function (data) {
			var newstate = {
				lines: this.state.lines.concat(data.lines),
				loadingLog: false
			};
			this.setState(newstate);
		}).bind(this));
	},
	componentWillMount: function () {
		var interval = setInterval(this.getNewLines, 1000);
		var newstate = copy(this.state);
		newstate.interval = interval;
		this.setState(newstate);
	},
	componentWillUpdate: function () {
		var node = this.getDOMNode();
		// This should be === per http://blog.vjeux.com/2013/javascript/scroll-position-with-react.html
		// but it doesn't seem to work...
		this.toBottom = node.scrollTop + node.offsetHeight >= node.scrollHeight;
	},
	componentDidUpdate: function() {
		if (this.toBottom) {
			var node = this.getDOMNode();
			node.scrollTop = node.scrollHeight;
		}
	},
	render: function () {
		var elts = this.state.lines.map(function (line, i) {
			return <pre key={i}>{line}</pre>;
		});
		return <div id="commandLog">{elts}</div>;
	}
});
var ShutItUI = React.createClass({
	getInfo: function (newstate) {
		var loadingstate = copy(this.state);
		loadingstate.loadingInfo = true;
		this.setState(loadingstate);
		var mid_list = [];
		newstate.modules.map(function (module) {
			if (module.selected) {
				mid_list.push(module.module_id);
			}
		})
		jsonpost('/info', {to_build: mid_list}, (function (verifiedstate) {
			verifiedstate.loadingInfo = false;
			this.setState(verifiedstate);
		}).bind(this));
	},
	beginBuild: function () {
		var newstate = copy(this.state);
		newstate.loadingInfo = true;
		newstate.building = true;
		this.setState(newstate);
		var checking = false;
		var checkbuild = (function () {
			if (checking) { return; }
			checking = true;
			jsonpost('/build', '', (function (done) {
				if (!done) {
					checking = false;
				} else {
					clearInterval(interval);
					var newstate = copy(this.state);
					newstate.building = false;
					newstate.done = true;
					this.setState(newstate);
				}
			}).bind(this));
		}).bind(this);
		var interval = setInterval(checkbuild, 1000);
	},
	getInitialState: function () {
		return {
			modules: [], errs: [],
			loadingInfo: false, building: false, done: false
		};
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
		var noInput = (this.state.loadingInfo || this.state.building ||
						this.state.done);
		return (
			<div>
				<StatusIndicator
					loading={this.state.loadingInfo}
					building={this.state.building}
					done={this.state.done} />
				<ModuleList
					onChange={this.handleChange}
					noInput={noInput}
					modules={this.state.modules} />
				<ErrList errs={this.state.errs} />
				<button disabled={noInput} onClick={this.beginBuild}>
					Begin build</button>
				<BuildProgress
					building={this.state.building}
					done={this.state.done}/>
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
	global build_started
	if build_done:
		return 'true'
	if not build_started:
		build_started = True
		t = threading.Thread(target=build_shutit)
		t.daemon = True
		t.start()
	return 'false'

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
