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

import os
import time
import logging
import tornado.web
import tornado.ioloop
from spank.web.api import LogsAPIHandler, ChartsAPIHandler, LiveAPIHandler
from spank.index import Index
from spank.message import MessagingService
from spank.web.socket import LiveSocketHandler
import sockjs.tornado

LiveRouter = sockjs.tornado.SockJSRouter(LiveSocketHandler, '/live')
HANDLERS=[
#    (r"/live",LiveSocketHandler),
    (r"/api/live/?", LiveAPIHandler),
    (r"/api/live/(.*)", LogsAPIHandler),
    (r"/api/logs/?", LogsAPIHandler),
    (r"/api/logs/(.*)", LogsAPIHandler),
    (r"/api/charts/?", ChartsAPIHandler),
    (r"/api/charts/(.*)", ChartsAPIHandler),
    (r"/app/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(os.path.dirname(__file__), "client/app")}),
    (r"/(favicon.ico)",tornado.web.StaticFileHandler,{"path":os.path.join(os.path.dirname(__file__), "client/app/img") }),
    (r"/", tornado.web.RedirectHandler,{"url":"/app/index.html"}),
] + LiveRouter.urls



class Application(tornado.web.Application):
    def __init__(self,**kwargs):
        super(Application,self).__init__(HANDLERS,**kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)        

        # Setup index service
        self.index = Index(server_url=kwargs["index_server_url"])
        LiveSocketHandler.application = self
        # Setup messaging service
        self.live_messaging = MessagingService(
            host=kwargs["messaging_server_host"],
            port=kwargs["messaging_server_port"],
            password=kwargs["messaging_server_password"],
            username=kwargs["messaging_server_username"],
            virtual_host=kwargs["messaging_server_vhost"],
        )
        self.tzoffset = kwargs["tzoffset"]
