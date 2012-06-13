#!/usr/bin/env python
# Copyright 2012 Matias Surdi
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import tornado.web
import os
from spank.web.api import LogsAPIHandler, ChartsAPIHandler
from spank.index import Index

HANDLERS=[
    (r"/api/logs/?", LogsAPIHandler),
    (r"/api/charts/?", ChartsAPIHandler),
    (r"/app/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(os.path.dirname(__file__), "client/app")}),
    (r"/", tornado.web.RedirectHandler,{"url":"/app/index.html"}),
]


class Application(tornado.web.Application):
    def __init__(self,**kwargs):
        super(Application,self).__init__(HANDLERS,**kwargs)
        self.index = Index(servers=self.settings["index_servers"])

