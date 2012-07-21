from urlparse import urljoin
from tornado.httpclient import AsyncHTTPClient,HTTPClient
from tornado.escape import json_encode,json_decode

class CallbackWrapper(object):
    def __init__(self,callback):
        self.callback = callback
    def __call__(self,response):
        index_response = json_decode(response.body)
        return self.callback(index_response)

class ES(object):
    #TODO: Make use of all provided servers instead of just the first one
    def __init__(self,servers):
        if type(servers) != list:
            self._servers = [servers]
        else:
            self._servers = servers
    
    def _send_request(self,callback,method,body=None,server=None,path=None,docid=None):
        url = self._servers[0]
        if server:
            url = server
            
        if path:
            url = urljoin(url,path)
        if docid:
            url = urljoin(url,docid)
        if callback:
            async_http_client = AsyncHTTPClient()
            async_http_client.fetch(url,CallbackWrapper(callback),method=method,body=body)
        else:
            http_client = HTTPClient()
            response = http_client.fetch(url,method=method,body=body)
            return json_decode(response.body)
            

    def index(self,index,doctype,body,docid,percolate=False,callback=None):
        path =  "%s/%s/%s?" % (index,doctype,docid)
        if percolate:
            path +="percolate=*"
        return self._send_request(path=path,body=json_encode(body),callback=callback,method="POST")

    def get(self,index,doctype,docid,callback=None):
        path = "%s/%s/%s" % (index,doctype,docid)
        return self._send_request(path=path,callback=callback,method="GET")
        
    def search(self,query,indexes=[],doctypes=[],callback=None):
        path = "/"
        if indexes:
            path = urljoin(path,",".join(indexes))
        if doctypes:
            path = urljoin(path,",".join(doctypes))
        path = urljoin(path,"_search")

        return self._send_request(path=path,callback=callback,method="POST",body=json_encode(query))

    def delete(self,index,callback=None):
        path =  "/%s" % index
        return self._send_request(path=path,callback=callback,method="DELETE")
