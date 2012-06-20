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

import uuid
import logging
import time
import datetime
import tornado.web
from tornado.escape import json_encode,json_decode
from spank.index import InvalidQueryException, Query, IndexRequest, DateHistogramFacet, RangeFilter

class BaseAPIHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.logger = logging.getLogger("spank.api")
        self.doctype = None
        self.sort_field = None
        self.sort_direction = "desc"

    def _get_tzoffset(self):
        return self.get_argument("tzoffset",self.application.settings["tzoffset"])

    def get(self, entry_id):
        response = []
        if entry_id is None:
            # Setup parameters
            q = self.get_argument("q","*:*")
            count = self.get_argument("count",30)
            before = self.get_argument("before",time.time())
            after = self.get_argument("after",0)

            try:
                time_filter = RangeFilter("time", int(after)*1000,int(before)*1000,False,False)
                index_request = IndexRequest().query(Query(q,tzoffset=self._get_tzoffset())).size(int(count)).sort(self.sort_field,
                    self.sort_direction).filter(time_filter)
                index_response = self.application.index.search(index_request, doctypes=[self.doctype])
                self.logger.debug("Index Response: %s" % str(index_response)[20])
            except InvalidQueryException, e:
                self.send_error(500,message="Invalid query\n")

            try:
                if index_response.has_key("hits"):
                    response = [entry["_source"] for entry in index_response["hits"]["hits"]]
            except InvalidQueryException, e:
                response = []
        else:
            index_response = self.application.index.get(self.doctype, entry_id)
            if not index_response["exists"]:
                self.send_error(404,message="Document not found")
            else:
                response = index_response["_source"]
        self.set_header("Content-Type", "application/json")
        self.write(json_encode(response))

    def post(self):
        data = None
        try:
            data = json_decode(self.request.body)
        except ValueError,e:
            self.send_error(501,message="Invalid json input")
        self.logger.debug(data)
        entry_id = str(uuid.uuid1())
        data["id"] = entry_id
        self.application.index.add(data, doctype=self.doctype, docid=entry_id)
        self.write({"id": str(entry_id)})

    def delete(self, id_):
        self.send_error(501,message="Not implemented")

    def put(self, id_):
        self.send_error(501,message="Not implemented")

class ChartsAPIHandler(BaseAPIHandler):
    def initialize(self):
        super(ChartsAPIHandler, self).initialize()
        self.doctype = "charts"
        # Setup global default parameters
        current_time = time.time()
        self.args = {
            "to": int(current_time),
            "from": 0,
            "interval": "hour",
            "query_string": "*:*"
        }

    def _build_chart(self):
        # Verify arguments
        assert self.args["interval"] in ["minute", "hour","day", "month", "year"]
        interval = self.args["interval"]
        from_ = int(self.args["from"])
        to = int(self.args["to"])
        query_string = self.args["query"]

        # Backend requires timestamps in milliseconds
        from_millis = from_ * 1000
        to_millis = to * 1000

        query = Query(query_string,tzoffset=self._get_tzoffset())
        facet = DateHistogramFacet("dataset_facet").interval(interval).field("time").filter(
            RangeFilter("time", from_millis, to_millis))
        index_request = IndexRequest().size(0).facet(facet).query(query)
        self.logger.debug(str(index_request))
        index_response = self.application.index.search(index_request)
        self.logger.debug(str(index_response)[:100])
        data = [(point["time"], point["count"]) for point in index_response["facets"]["dataset_facet"]["entries"]]
        return data

    def get(self, chart_id=None):
        if chart_id:
            index_response = self.application.index.get("charts", chart_id)
            if not index_response["exists"]:
                self.send_error(404,message="Document not found")
            else:
                chart = index_response["_source"]

                # Setup defaults from chart object
                if chart.has_key("interval"):
                    self.args["interval"] = chart["interval"]

                if chart.has_key("query"):
                    self.args["query"] = chart["query"]

                if chart.has_key("since") and chart.has_key("since_unit"):
                    since_minutes = int(chart["since"])
                    if chart["since_unit"] == "hours":
                        since_minutes *= 60
                    elif chart["since_unit"] == "days":
                        since_minutes *= 60 * 24
                    elif chart["since_unit"] == "months":
                        since_minutes *= 60 * 24 * 30
                    elif chart["since_unit"] == "years":
                        since_minutes *= 60 * 24 * 30 * 12
                    self.args["from"] = int(self.args["to"]) - datetime.timedelta(minutes=since_minutes).total_seconds()

                # Request parameters override all previous defaults
                self.args.update(self.request.arguments)
                try:
                    chart["data"] = self._build_chart()
                except Exception, e:
                    self.send_error(501,message="Invalid arguments detected: " + str(e))
                swlf.write(chart)

        elif self.request.arguments.has_key("query"):
            self.args["query"] = self.get_argument("query","*:*")
            try:
                data = self._build_chart()
            except Exception, e:
                self.send_error(501,message="Invalid arguments detected: " + str(e))
            chart = {
                "title": "Generated by: %s" % self.args["query"],
                "query": self.args["query"],
                "data": data
            }
            self.write(chart)

        else:
            return self.send_error(501,message="Chart ID or query string required")

    def post(self):
        return super(ChartsAPIHandler, self).post()


class LogsAPIHandler(BaseAPIHandler):
    def initialize(self):
        super(LogsAPIHandler, self).initialize()
        self.sort_field = "time"
        self.doctype = "logs"

    def get(self, log_id=None):
        return super(LogsAPIHandler, self).get(log_id)

    def post(self):
        return super(LogsAPIHandler, self).post()


