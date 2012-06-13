import requests
from urllib import urlencode
from pprint import pprint

try:
    import simplejson as json   # try the faster simplejson on old versions
except:
    import json
import logging
log = logging.getLogger(__name__)

__author__ = 'Erik-Jan van Baaren'
__all__ = ['ESClient']
__version__ = (0, 3, 0)


def get_version():
        return "%s.%s.%s" % __version__


class ESClientException(Exception):
    pass


class ESClient:
    """ESClient is a Python library that warps around the ElasticSearch
    REST API.

    ESClient methods will always return a hierachy of Python objects and not
    the pure JSON as returned by ElasticSearch.

    Take a look at the unit tests to see usage examples for all available API
    methods that this library implements.
    Any API calls that are not (yet) implemented by ESClient can still be used
    by using the send_request() method to directly do an HTTP request to the
    ElasticSearch API.

    """

    def __init__(self, es_url='http://localhost:9200', request_timeout=10):
        self.es_url = es_url
        self.request_timeout = request_timeout

        if self.es_url.endswith('/'):
            self.es_url = self.es_url[:-1]

    #
    # Internal helper methods
    # 

    def _make_path(self, path_components):
        """Create path from components. Empty components will be
        ignored.

        """
        path_components = map(str, filter(None, path_components))
        path = '/'.join(path_components)
        if not path.startswith('/'):
            path = '/' + path
        return path

    def _parse_json_response(self, response):
        """Convert JSON response from ElasticSearch to a hierarchy of Python
        objects and return that hierarchy.
        
        Throws an exception when parsing fails.
        
        """
        try:
            return json.loads(response)
        except:
            raise ESClientException("Unable to parse JSON response from "
                                    "ElasticSearch")

    def check_result(self, results, key, value):
        """Check if key is an element of list, and check if that element
        is equal (==) to value.
        
        Returns True if the key exists and is equal to given value, false
        otherwise.
        """
        if key in results:
            return results[key] == value
        
    def send_request(self, method, path, body=None, query_string_args={},encode_json=True):
        """Make a raw HTTP request to ElasticSearch.

        You may use this method to manually do whatever is not (yet) supported
        by ESClient. This method does not return anything, but sets the class
        variable called last_response, which is the response object returned
        by the requests library.

        Arguments:
        method -- HTTP method, e.g. 'GET', 'PUT', 'DELETE', etc.
        path -- URL path
        body -- the body, as a hierachy of Python objects that is parseable
                to JSON with json.dumps()
        query_string_args -- the query string arguments, which are the
        key=value pairs after the question mark in any URL.

        """
        if query_string_args:
            path = "?".join([path, urlencode(query_string_args)])

        kwargs = { 'timeout': self.request_timeout }
        url = self.es_url + path

        if body:
            if encode_json:
                kwargs['data'] = json.dumps(body)
            else:
                kwargs['data'] = body

        if not hasattr(requests, method.lower()):
            raise ESClientException("No such HTTP Method '%s'!" %
                                    method.upper())
        
        self.last_response = requests.request(method.lower(), url, **kwargs)

    def _search_operation(self, request_type, query_body=None,
                    operation_type="_search", query_string_args=None,
                    indexes=["_all"], doctypes=[]):
        """Perform a search operation. This method can be use for search,
        delete by search and count.

        Searching in ElasticSearch can be done in two ways:
        1) with a query string, by providing query_args
        2) using a full query body (JSON) by providing
        the query_body.
        You can choose one, but not both at the same time.

        """
        if query_body and query_string_args:
            raise ESClientException("Found both a query body and query" +
                                    "arguments")

        indexes = ','.join(indexes)
        doctypes = ','.join(doctypes)
        path = self._make_path([indexes, doctypes, operation_type])

        if query_body:
            self.send_request(request_type, path, body=query_body)
        elif query_string_args:
            self.send_request(request_type, path,
                              query_string_args=query_string_args)
        elif operation_type == "_count":
            # If both options were not used, there one more option left: no
            # query at all. A query is optional when counting, so we fire a
            # request to the URL without a query only in this specific case.
            self.send_request('GET', path)
        else:
            raise ESClientException("Mandatory query was not supplied")

        try:
            return self._parse_json_response(self.last_response.text)
        except:
            raise ESClientException("Was unable to parse the ElasticSearch "
            "response as JSON: \n%s", self.last_response.text)

    #
    # The API methods
    #

    def index(self, index, doctype, body, docid=None, op_type=None):
        """Index the supplied document.

        Options:
        index -- the index name (e.g. twitter)
        doctype -- the document types (e.g. tweet)
        op_type -- "create" or None:
            "create": create document only if it does not exists already
            None: create document or update an existing document

        Returns True on success (document added/updated or already exists
        while using op_type="create") or False in all other instances.

        """
        args = dict()
        if op_type:
            args["op_type"] = op_type
        path = self._make_path([index, doctype, docid])
        self.send_request('POST', path, body=body, query_string_args=args)
        rescode = self.last_response.status_code
        if 200 <= rescode < 300:
            return True
        elif rescode == 409 and op_type == "create":
            # If document already exists, ES returns 409
            return True
        else:
            return False

    def search(self, query_body=None, query_string_args=None,
                indexes=["_all"], doctypes=[]):
        """Perform a search operation.

        Searching in ElasticSearch can be done in two ways:
        1) with a query string, by providing query_args
        2) using a full query body (JSON) by providing
        the query_body.
        You can choose one, but not both at the same time.

        """
        return self._search_operation('GET', query_body=query_body,
                query_string_args=query_string_args, indexes=indexes,
                doctypes=doctypes)


    def delete_by_query(self, query_body=None, query_string_args=None,
                indexes=["_all"], doctypes=[]):
        """Delete based on a search operation.

        Searching in ElasticSearch can be done in two ways:
        1) with a query string, by providing query_args
        2) using a full query body (JSON) by providing
        the query_body.
        You can choose one, but not both at the same time.

        """
        return self._search_operation('DELETE', query_body=query_body,
                query_string_args=query_string_args, indexes=indexes,
                doctypes=doctypes, operation_type='_query')

    def count(self, query_body=None, query_string_args=None,
                indexes=["_all"], doctypes=[]):
        """Count based on a search operation. The query is optional, and when
        not provided, it will use match_all to count all the docs.

        Searching in ElasticSearch can be done in two ways:
        1) with a query string, by providing query_args
        2) using a full query body (JSON) by providing
        the query_body.
        You can choose one, but not both at the same time.

        """
        return self._search_operation('GET', query_body=query_body,
                query_string_args=query_string_args, indexes=indexes,
                doctypes=doctypes, operation_type='_count')

    def get(self, index, doctype, docid, fields=None):
        """Get document from the index.

        You need to supply an index, doctype and id. Optionally, you can
        list the fields that you want to retrieve, e.g.:
        fields=['name','address']

        """
        args = dict()
        if fields:
            fields = ",".join(fields)
            args['fields'] = fields

        path = self._make_path([index, doctype, docid])
        self.send_request('GET', path, query_string_args=args)
        return self._parse_json_response(self.last_response.text)

    def mget(self, index, doctype, ids, fields=None):
        """Perform a multi get.
        
        Although ElasticSearch supports it, this method does not allow you to
        specify the index and/or fields per id. So you can only specify the
        index and fields once and this will be applied to all document id's
        you want to fetch.
        
        Arguments:
            index -- the index name
            doctype -- the document type
            ids -- a list of ids to fetch
            fields -- option list of fields to return

        """
        path = self._make_path([index, doctype, '_mget'])
        docs = []
        for id in ids:
            doc = {'_id': id}
            if fields:
                doc['fields'] = fields
            docs.append(doc)
        body = {'docs': docs}
        self.send_request('GET', path, body=body)
        return self._parse_json_response(self.last_response.text)

    def delete(self, index, doctype, id):
        """Delete document from index.

        Returns true if the document was found and false otherwise.

        """
        path = self._make_path([index, doctype, id])
        self.send_request('DELETE', path)
        resp = json.loads(self.last_response.text)
        return self.check_result(resp, 'found', True)

    """
    Indices API
    """
    def create_index(self, index, body=None):
        """Create an index.

        You have to supply the optional settings and mapping yourself.

        """
        path = self._make_path([index])
        self.send_request('PUT', path, body=body)
        resp = json.loads(self.last_response.text)
        return self.check_result(resp, 'acknowledged', True)

    def delete_index(self, index):
        """Delete an entire index.

        Returns true if the index was deleted and false otherwise.

        """
        path = self._make_path([index])
        self.send_request('DELETE', path)
        resp = json.loads(self.last_response.text)
        return self.check_result(resp, 'acknowledged', True)

    def refresh(self, index):
        """Refresh index.

        Returns True on success, false otherwise.

        """
        path = self._make_path([index, '_refresh'])
        self.send_request('POST', path)
        resp = json.loads(self.last_response.text)
        return self.check_result(resp, 'ok', True)

    def create_alias(self, alias, indexes):
        """Create an alias for one or more indexes.
        
        Arguments:
        alias -- the alias name
        indexes -- a list of indexes that this alias spans over
        
        """
        query = {}
        query['actions'] = []
        for index in indexes:
            query['actions'].append({"add": {"index": index, "alias": alias}})
        
        path = self._make_path(['_aliases'])
        self.send_request('POST', path, body=query)
        resp = json.loads(self.last_response.text)
        return self.check_result(resp, 'ok', True)

    def delete_alias(self, alias, indexes):
        """delete an alias.

        Arguments:
        alias -- the alias name to delete
        indexes -- a list of indexes from which to delete the alias

        """
        query = {}
        query['actions'] = []
        for index in indexes:
            query['actions'].append({"delete": {"index": index, "alias": alias}})

        path = self._make_path(['_aliases'])
        self.send_request('POST', path, body=query)
        resp = json.loads(self.last_response.text)
        return self.check_result(resp, 'ok', True)


    def open_index(self, index):
        """Open a closed index.
        
        Opening a closed index will make that index go through the normal
        recover process.
        
        Returns True on success, False of failure.
        
        """
        path = self._make_path([index, '_open'])
        self.send_request('POST', path)
        resp = json.loads(self.last_response.text)
        return self.check_result(resp, 'ok', True)
        
    def close_index(self, index):
        """Close an index. A closed index has almost no overhead on the
        cluster except for maintaining its metadata. A closed index is
        blocked for reading and writing.
        
        Returns True on success, False of failure.
        """
        path = self._make_path([index, '_close'])
        self.send_request('POST', path)
        resp = json.loads(self.last_response.text)
        return self.check_result(resp, 'ok', True)

    def status(self, indexes=['_all']):
        """Retrieve the status of one or more indices.
        
        Returns the JSON response converted to a hierachy of Python objects.
        
        """
        path = self._make_path([','.join(indexes), '_status'])
        self.send_request('GET', path)
        return self._parse_json_response(self.last_response.text)

    def flush(self, indexes=['_all'], refresh=False):
        """Flush one or more indexes.
        
        Flush frees memory from the index by flushing data to the index
        storage and clearing the internal transaction log. There is
        usually no need to use this function manually though.
        
        """
        path = self._make_path([','.join(indexes), '_flush'])
        args = {}
        if refresh:
            args['refresh'] = "true"
        self.send_request('POST', path, query_string_args=args)
        resp = json.loads(self.last_response.text)
        return self.check_result(resp, 'ok', True)

    def get_mapping(self, indexes=['_all'], doctypes=[]):
        """Get mapping(s).
        
        You can get mappings for multiple indexes and/or multiple
        types.
        
        Arguments:
        indexes -- optional list of indexes
        types -- optional list of types

        """

        # TODO: find out if you can get a mapping for multiple indexes
        # and multiple types at the same time
        path = self._make_path([','.join(indexes), ','.join(doctypes),
                                '_mapping'])
        self.send_request('GET', path)
        return self._parse_json_response(self.last_response.text)

    def put_mapping(self, mapping, doctype, indexes=['_all']):
        """Register a mapping definition for a specific type. You can
        register a mapping for one index, multiple indexes or even
        all indexes (the default).
        
        Arguments:
        indexes -- optional list of indexes (defaults to _all)
        type -- the type you want this mapping to apply to
        mapping -- a hierachy of Python object that can be converted to
        a JSON document

        """
        path = self._make_path([','.join(indexes), doctype, '_mapping'])
        self.send_request('PUT', path=path, body=mapping)
        return self._parse_json_response(self.last_response.text)
        
if __name__ == '__main__':
    print "This is a library, it is not intended to be started by itself."
