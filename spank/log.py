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
import logging
from logging.handlers import SysLogHandler

def initialize_logging(args,description=sys.argv[0]):
    # Setup logging
    logger = logging.getLogger()
    if args.debug:
        logger.setLevel(level=logging.DEBUG)
    else:
        logger.setLevel(level=logging.INFO)
    if args.logging.startswith("/"):
        syslog_handler = SysLogHandler(args.logging)
    else:
        try:
            host,port = args.logging.split(":")
            syslog_handler = SysLogHandler((host,int(port)))
        except Exception,e:
            print "Invalid logging arguments."
            sys.exit(1)
    syslog_handler.setFormatter(logging.Formatter(args.log_format))
    logger.addHandler(syslog_handler)
    logging.info("Initializing logging for %s..." % description)
