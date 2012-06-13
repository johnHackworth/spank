import unittest
from spank import index

class TestIndexRequest(unittest.TestCase):
    def setUp(self):
        pass    

    def test_constructor(self):
        query = index.Query("*:*",tzoffset="Z")
        facet = index.DateHistogramFacet(name="test_Facet",field="time",interval="hour")
        request = index.IndexRequest(query=query,facets=set([facet]),size=10,sort_field="name",sort_direction="desc")
        result = str(request)
        expected_result = '{"sort": {"name": "desc"}, "query": {"query_string": {"query": "*:*", "default_operator": "AND"}}, "facets": {"test_Facet": {"date_histogram": {"field": "time", "interval": "hour"}}}, "size": 10}'
        self.assertEqual(result,expected_result)

    def test_chaining(self):
        query = index.Query("*:*",tzoffset="Z")
        facet = index.DateHistogramFacet(name="test_Facet",field="time",interval="hour")
        request = index.IndexRequest().query(query).facet(facet).size(10).sort_field("name").sort_direction("desc")
        result = str(request)
        expected_result = '{"sort": {"name": "desc"}, "query": {"query_string": {"query": "*:*", "default_operator": "AND"}}, "facets": {"test_Facet": {"date_histogram": {"field": "time", "interval": "hour"}}}, "size": 10}'
        self.assertEqual(result,expected_result)

