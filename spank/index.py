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

import logging
import re
import datetime
import time
from tornado.escape import json_encode,json_decode
from spank import estornudo

DATETIME_REGEX = [
    '(?P<day>\d{1,2})/(?P<month>\d{1,2})/(?P<year>\d{4}) (?P<hour>\d{1,2}):(?P<minute>\d{1,2}):(?P<second>\d{1,2})(?P<tzoffset>[+-]{1}\d{2}:\d{2})',
    '(?P<day>\d{1,2})/(?P<month>\d{1,2})/(?P<year>\d{4}) (?P<hour>\d{1,2}):(?P<minute>\d{1,2}):(?P<second>\d{1,2})',
    '(?P<day>\d{1,2})/(?P<month>\d{1,2})/(?P<year>\d{4}) (?P<hour>\d{1,2}):(?P<minute>\d{1,2})',
    '(?P<day>\d{1,2})/(?P<month>\d{1,2})/(?P<year>\d{4}) (?P<hour>\d{1,2})',
    '(?P<day>\d{1,2})/(?P<month>\d{1,2})/(?P<year>\d{4})[^T\d]',
    '[^T\d](?P<hour>\d{1,2}):(?P<minute>\d{1,2}):(?P<second>\d{1,2})',
    ]

DATETIME_FORMAT = "%(year)s-%(month)s-%(day)sT%(hour)s:%(minute)s:%(second)s%(tzoffset)s"

class QueryTranslator(object):
    def __init__(self, query,tzoffset="Z"):
        self.query = query
        self.tzoffset = tzoffset

    def _cleanup_datetimes(self):
        now = datetime.datetime.now()
        defaults = {
            "day": now.day,
            "month": now.month,
            "year": now.year,
            "hour": 0,
            "minute": 0,
            "second": 0,
            "tzoffset":self.tzoffset
            }
        keep_looking = True
        while keep_looking:
            keep_looking = False
            for f in DATETIME_REGEX:
                match = re.search(f, self.query)
                if match:
                    time_parts = match.groupdict()
                    defaults.update(time_parts)
                    self.query = re.sub(f, DATETIME_FORMAT % defaults, self.query, 1)
                    keep_looking = True
                    break

    def translate(self):
        self._cleanup_datetimes()
        return self.query


class InvalidQueryException(Exception):
    pass


class RangeFilter(object):
    def __init__(self, field, from_=None, to=None,include_lower=True,include_upper=True):
        self.field = field
        self.from_ = from_ or 0
        self.to = to or time.time()
        self.include_lower = include_lower
        self.include_upper = include_upper

    def from_(self,from_):
        self.from_ = from_
        return self

    def to(self,to):
        self.to = to
        return self

    def include_lower(self,include_lower):
        self.include_lower = include_lower
        return self

    def include_upper(self,include_upper):
        self.include_upper = include_upper
        return self

    def get(self):
        return JSONDict({
            "range": {
                self.field: {
                    "from": self.from_, 
                    "to": self.to,
                    "include_lower": self.include_lower,
                    "include_upper": self.include_upper
                    },
               }
        })

    def __str__(self):
        return str(self.get())


class Facet(object):
    def __init__(self, name):
        self._name = name

    def get(self):
        result = {}

        return JSONDict(result)


    def __str__(self):
        return str(self.get())


class DateHistogramFacet(Facet):
    def __init__(self, name,field=None,interval=None,filter_=None):
        super(DateHistogramFacet, self).__init__(name)
        self._field = field
        self._interval = interval
        self._filter = filter_

    def interval(self, interval):
        self._interval = interval
        return self

    def field(self, field):
        self._field = field
        return self

    def filter(self, filter):
        self._filter = filter
        return self

    def get(self):
        result = super(DateHistogramFacet, self).get()
        result[self._name] = {}
        result[self._name]["date_histogram"] = {
            "field": self._field,
            "interval": self._interval
        }
        if self._filter:
            result[self._name]["facet_filter"] = self._filter.get()

        return JSONDict(result)

    def __str__(self):
        return str(self.get())


class JSONDict(dict):
    def __str__(self):
        return json_encode(self)


class IndexRequest(object):
    def __init__(self,query=None,facets=set(),size=None,sort_field=None,sort_direction=None,from_=None):
        self._query = query
        self._facets = facets
        self._size = size
        self._sort_field = sort_field
        self._sort_direction = sort_direction
        self._from = from_
        self._filter = None

    def query(self, query):
        self._query = query
        return self

    def filter(self, filter):
        self._filter = filter
        return self

    def facet(self, facet):
        self._facets.add(facet)
        return self

    def size(self, size):
        self._size = size
        return self

    def from_(self,from_):
        self._from = from_
        return self

    def sort_field(self,sort_field):
        self._sort_field = sort_field
        return self

    def sort_direction(self,sort_direction):
        self._sort_direction = sort_direction
        return self

    def sort(self, field, direction="asc"):
        self._sort_field = field
        self._sort_direction = direction
        return self

    def get(self):
        request = {}
        if self._facets:
            for facet in self._facets:
                if not request.has_key("facets"):
                    request["facets"] = {}
                request["facets"].update(facet.get())
        if self._size is not None:
            request["size"] = self._size
    
        if self._from is not None:
            request["from"] = self._from

        if self._sort_field and self._sort_direction:
            request["sort"] = {self._sort_field: self._sort_direction}


        if self._filter:
            request["query"] = {}
            request["query"]["filtered"] = {}
            request["query"]["filtered"]["filter"] = self._filter.get()
            if self._query:
                request["query"]["filtered"]["query"] = self._query.get()
        else:
            if self._query:
                request["query"] = self._query.get()
        return JSONDict(request)

    def __str__(self):
        return str(self.get())


class Query(object):
    def __init__(self, query_string="",tzoffset="Z"):
        self.logger = logging.getLogger("spank.query")
        self.query_string = query_string
        self.default_operator = "AND"
        self.tzoffset = tzoffset


    def default_operator(self, default_operator):
        self.default_operator = default_operator
        return self

    def search_type(self, search_type):
        self.search_type = search_type
        return self


    def get(self):
        query = {
            "query_string": {
                "query": QueryTranslator(self.query_string,tzoffset=self.tzoffset).translate(),
                "default_operator": self.default_operator
            }
        }

        self.logger.debug(query)
        return JSONDict(query)

    def __str__(self):
        return str(self.get())


class Index(object):
    def __init__(self, server_url):
        self.logger = logging.getLogger("spank.index")
        self.server_url = server_url
        self.es = estornudo.ES(self.server_url)

    def add(self, doc, index="main", doctype="", docid=None,percolate=False,callback=None):
        response = self.es.index(index=index, doctype=doctype, body=doc, docid=(docid or doc["id"]),percolate=percolate,callback=callback)
        return response

    def search(self, query, indexes=["main"], doctypes=[],callback=None):
        self.logger.debug("Runing query: %s" % str(query))
        response = self.es.search(indexes=indexes,doctypes=doctypes,query=query,callback=callback)
        return response

    def get(self, doctype, docid, index="main", fields=None,callback=None):
        response = self.es.get(index, doctype, docid,callback=callback)
        return response

