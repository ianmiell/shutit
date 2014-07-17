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
import subprocess

import bottle
from bottle import route, request, response, static_file

import shutit_main
import shutit_global
from shutit_module import ShutItException
import util

orig_mod_cfg = None
shutit = None
STATUS = None

def build_shutit():
    """Performs ShutIt remove/build/test/finalize cycle.
    """
    global STATUS
    try:
        shutit_main.do_remove(shutit)
        shutit_main.do_build(shutit)
        shutit_main.do_test(shutit)
        shutit_main.do_finalize(shutit)
        shutit_main.finalize_container(shutit)
    except ShutItException as e:
        STATUS['errs'] = [str(e)]
    STATUS['build_done'] = True

def update_modules(to_build, cfg):
    """
    Updates modules to be built with the passed-in config.
    Updating each individual module section will propogate the changes to
    STATUS as well (as the references are the same).
    Note that we have to apply overrides in a specific order -
    1) reset the modules being built to the defaults
    2) set any modules selected for build as build = True
    3) reset configs using config_collection_for_built
    4) apply config overrides
    """
    global STATUS

    selected = set(to_build)
    for mid in shutit.cfg:
        if mid in orig_mod_cfg and 'build' in orig_mod_cfg[mid]:
            shutit.cfg[mid]['build'] = orig_mod_cfg[mid]['build']
        if mid in selected:
            shutit.cfg[mid]['build'] = True
    # There is a complexity here in that module configs may depend on
    # configs from other modules (!). We assume this won't happen as we
    # would have to override each module at the correct time.
    shutit_main.config_collection_for_built(shutit)

    if cfg is not None:
        sec, key, val = cfg
        orig_mod_cfg[sec][key] = val
    for mid in orig_mod_cfg:
        for cfgkey in orig_mod_cfg[mid]:
            if cfgkey == 'build': continue
            shutit.cfg[mid][cfgkey] = orig_mod_cfg[mid][cfgkey]

    errs = []
    errs.extend(shutit_main.check_deps(shutit))
    errs.extend(shutit_main.check_conflicts(shutit))
    errs.extend(shutit_main.check_ready(shutit))

    # TODO: display an error if (selected and not build)
    STATUS['errs'] = [err[0] for err in errs]
    STATUS['modules'] = [
        {
            "module_id":   mid,
            "description": shutit.shutit_map[mid].description,
            "run_order":   float(shutit.shutit_map[mid].run_order),
            "build":       shutit.cfg[mid]['build'],
            "selected":    mid in selected
        } for mid in shutit_main.module_ids(shutit)
    ]

@route('/info', method='POST')
def info():
    """Handles requests to build, reset, defaulting to returning current STATUS if none of these are requested.
    """
    global STATUS
    can_check = not (STATUS['build_started'] or STATUS['resetting'])
    can_cfg   = not (STATUS['build_started'] or STATUS['resetting'])
    can_build = not (STATUS['build_started'] or STATUS['resetting'])
    can_reset = not ((STATUS['build_started'] and not STATUS['build_done']) or STATUS['resetting'])

    if can_check and 'to_build' in request.json and 'cfg' in request.json:
        update_modules(request.json['to_build'], request.json['cfg'])
    if can_build and 'build' in request.json and len(STATUS['errs']) == 0:
        STATUS["build_started"] = True
        t = threading.Thread(target=build_shutit)
        t.daemon = True
        t.start()
    if can_reset and 'reset' in request.json:
        shutit_reset()

    return json.dumps(STATUS)

@route('/log', method='POST')
def log():
    """Returns log information to the client.
    """
    cmd_offset, log_offset = request.json
    if STATUS['resetting']:
        command_list = []
        log = ''
    else:
        command_list = shutit.shutit_command_history[cmd_offset:]
        log = shutit.cfg['build']['build_log'].getvalue()[log_offset:]
    # Working around issues with encoding in a cowardly way.
    return json.dumps({
        "cmds": command_list,
        "logs": log
    }, encoding='iso8859-1')

@route('/')
def index():
    """Serves the main file.
    """
    return static_file('index.html', root='./web')

@route('/static/<path:path>.js')
def static_srv(path):
    """Serves a static file.
    """
    return static_file(path + '.js', root='./web')

@route('/export/<cid>.tar.gz')
def export_srv(cid):
    # TODO: this blocks all other requests
    global shutit
    docker = shutit.cfg['host']['docker_executable'].split(' ')
    export_cmd = docker + ['export', cid]
    # TODO: check for error on stderr for both the below commands
    tar_export = subprocess.Popen(export_cmd,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    gzip_export = subprocess.Popen(['gzip', '--stdout'],
        stdin=tar_export.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    response.content_type = 'application/x-gzip'
    response.set_header('Content-disposition', 'attachment')
    if 'wsgi.file_wrapper' in request.environ:
        return request.environ['wsgi.file_wrapper'](gzip_export.stdout)
    else:
        return iter(lambda: gzip_export.stdout.read(1024*1024), '')

def shutit_reset():
    """Handles a ShutIt reset, clearing the STATUS global.
    """
    global orig_mod_cfg
    global shutit
    global STATUS

    orig_mod_cfg = {}
    if shutit is not None:
        for c in shutit.pexpect_children.values():
            # Try to clean up the old children...
            c.send('\n')
            c.sendeof()
            c.readlines()
        print shutit.cfg
        image_tag = shutit.cfg['container']['docker_image']
    else:
        image_tag = ''
    shutit = None
    STATUS = {
        'build_done':    False,
        'build_started': False,
        'resetting':     True,
        'modules':       [],
        'errs':          [],
        'cid':           '',
        'cfg':           {},
        'image_tag':     image_tag
    }

    def reset_thread():
        global orig_mod_cfg
        global shutit
        global STATUS
        # Start with a fresh shutit object
        shutit = shutit_global.shutit = shutit_global.init()

        # This has already happened but we have to do it again on top of our new
        # shutit object
        util.parse_args(shutit.cfg)

        # The rest of the loading from shutit_main
        util.load_configs(shutit)
        shutit_main.shutit_module_init(shutit)
        # Here we can set the starting image.
        if STATUS['image_tag'] != '':
            shutit.cfg['container']['docker_image'] = STATUS['image_tag']
        else:
            STATUS['image_tag'] = shutit.cfg['container']['docker_image']
        shutit_main.conn_container(shutit)

        # Some hacks for server mode
        shutit.cfg['build']['build_log'] = StringIO.StringIO()
        shutit.cfg['build']['interactive'] = 0
        STATUS['cid'] = shutit.cfg['container']['container_id']
        for mid in shutit.shutit_map:
            orig_mod_cfg[mid] = STATUS['cfg'][mid] = shutit.cfg[mid]
        # Add in core sections
        for mid in ['repository', 'container']:
            orig_mod_cfg[mid] = STATUS['cfg'][mid] = shutit.cfg[mid]
            
        # Make sure that orig_mod_cfg can be updated seperately to
        # STATUS and shutit.cfg (which remain linked), as it will hold
        # our overrides
        orig_mod_cfg = copy.deepcopy(orig_mod_cfg)
        update_modules([], None)

        STATUS['resetting'] = False

    t = threading.Thread(target=reset_thread)
    t.daemon = True
    t.start()

def start():
    """Start the ShutIt server.

    Environment variables:
        SHUTIT_HOST - hostname for the server (default: localhost)
        SHUTIT_PORT - port for the server (default: 8080)
    """
    shutit_reset()

    # Start the server
    host = os.environ.get('SHUTIT_HOST', '0.0.0.0')
    port = int(os.environ.get('SHUTIT_PORT', 8080))
    bottle.debug(True)
    try:
        import cherrypy
        bottle.run(host=host, port=port, server='cherrypy')
    except:
        print "WARNING: falling back to single threaded mode"
        bottle.run(host=host, port=port)

if __name__ == '__main__':
    print "PLEASE START VIA SHUTIT_MAIN INSTEAD"
