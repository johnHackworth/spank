import unittest
from spank import index

class TestDateHistogramFacet(unittest.TestCase):
    def setUp(self):
        pass    

    def test_constructor(self):
        facet = index.DateHistogramFacet(name="test_facet",field="time",interval="minute",filter_=None)
        result = str(facet)
        self.assertEqual(result,'{"test_facet": {"date_histogram": {"field": "time", "interval": "minute"}}}')

    def test_chaining(self):
        facet = index.DateHistogramFacet(name="test_facet").field("time").interval("minute").filter(None)
        result = str(facet)
        self.assertEqual(result,'{"test_facet": {"date_histogram": {"field": "time", "interval": "minute"}}}')
