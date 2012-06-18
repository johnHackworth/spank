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

import sys
import uuid
import time
import datetime
import logging
import urllib2
import isodate
from tornado.escape import json_encode

class LogForwardingException(Exception):
    pass

class ForwarderRequest(object):
    def __init__(self,url,payload):
        self.logger = logging.getLogger("spank.forwarder.forward_request")
        self.payload = json_encode(payload)
        self.request = urllib2.Request(url,self.payload,headers={'Content-Type':'application/json'})
        self.logger.debug("Created new request with payload: %s" % self.payload)

    def get_payload(self):
        return self.payload

    def submit(self):
        try:
            response = urllib2.urlopen(self.request).read()
            self.logger.debug("Response from upstream: %s" % response)
        except Exception,e:
            self.logger.critical("Error submitting request: %s" % str(e))
            raise LogForwardingException

class Forwarder(object):
    def __init__(self,servers,input_stream=sys.stdin,request_type=ForwarderRequest):
        self.logger = logging.getLogger("spank.forwarder")
        self.servers = servers
        self.input_stream = input_stream
        self.request_type = request_type

    def send(self,log_entry):
        #TODO: Implement roundrobin/failover on provided servers instead of using just the first one
        request = self.request_type(self.servers[0],log_entry)
        try:
            request.submit()
        except Exception,e:
            #TODO: Decide and implement what to do when no backend available.
            # For now, just send it to syslog so that other tool could recover it
            # later
            self.logger.info("NOTINDEXED: %s" % json_encode(log_entry))

    def forward(self):
        log_entry = self._read_input()
        while log_entry:
            log_entry["received"] = int(time.time()*1000)
            self.send(log_entry)
            log_entry = self._read_input()

    def _read_input(self):
        log_entry = {}
        while True:
            try:
                line = self.input_stream.readline()
            except KeyboardInterrupt:
                return
            
            if not line:
                time.sleep(0.2)
            else:
                line = line.strip()
                if line == "end":
                    return log_entry   
                elif line == "quit":
                    return
                else:
                    try:
                        field,value = line.split("=",1)
                        if field.find(":") > -1:
                            field,validator = field.split(":",1)
                            if validator == "timestamp":
                                value =  int(float(value) *1000)
                            else:
                                value = str(value)
                        log_entry[field] = value
                    except Exception,e:
                        self.logger.critical(str(e))
                        pass
                self.logger.debug(line)
    
