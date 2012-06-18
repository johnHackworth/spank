import unittest
from spank import index

class TestRangeFilter(unittest.TestCase):
    def setUp(self):
        pass    

    def test_range(self):
        range_filter = index.RangeFilter(field="field1",from_="A",to="B")
        result = str(range_filter)
        self.assertEqual('{"range": {"field1": {"to": "B", "include_lower": true, "include_upper": true, "from": "A"}}}',result)
