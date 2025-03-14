# -*- coding: utf-8 -*-
'''
gui_topology.py
================

.. module:: gui_topology
  :platform: Linux
  :synopsis: This module serves static files for the Ryu SDN controller's web-based topology 
             viewer. It provides a web interface to visualize and manage network topologies.

.. moduleauthor:: Ryu Project Contributors <ryu-devel@lists.sourceforge.net>

Introduction
------------

This module is designed to serve static files that are used by the Ryu SDN controller’s 
web-based topology viewer. It allows users to visualize and manage their network topologies 
through a web browser. Key features include:

- Serving static HTML, CSS, and JavaScript files necessary for the web interface.
- Integration with other Ryu applications such as `rest_topology`, `ws_topology`, and `ofctl_rest` 
  to provide comprehensive network management capabilities.

Usage example
-------------

1. Join switches (use your favorite method):
$ sudo mn --controller remote --topo tree,depth=3

2. Run this application:
$ PYTHONPATH=. ./bin/ryu run \
    --observe-links ryu/app/gui_topology/gui_topology.py

3. Access http://<ip address of ryu host>:8080 with your web browser.

The original license and copyright notice for the Ryu controller are retained below:

Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.
See the License for the specific language governing permissions and
limitations under the License.

Version
-------

- Version 1.0 (2025/03/14): Initial release implementing basic functionalities for serving static files for the web-based topology viewer.

'''

import os

from webob.static import DirectoryApp

from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.base import app_manager


PATH = os.path.dirname(__file__)


# Serving static files
class GUIServerApp(app_manager.RyuApp):
    _CONTEXTS = {
        'wsgi': WSGIApplication,
    }

    def __init__(self, *args, **kwargs):
        super(GUIServerApp, self).__init__(*args, **kwargs)

        wsgi = kwargs['wsgi']
        wsgi.register(GUIServerController)


class GUIServerController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(GUIServerController, self).__init__(req, link, data, **config)
        path = "%s/html/" % PATH
        self.static_app = DirectoryApp(path)

    @route('topology', '/{filename:[^/]*}')
    def static_handler(self, req, **kwargs):
        if kwargs['filename']:
            req.path_info = kwargs['filename']
        return self.static_app(req)


app_manager.require_app('ryu.app.rest_topology')
app_manager.require_app('ryu.app.ws_topology')
app_manager.require_app('ryu.app.ofctl_rest')
