import unittest
from spank import index

class TestQueryTranslator(unittest.TestCase):
    def setUp(self):
        pass

    def test_basic(self):
        query = "*:*"
        query_translator = index.QueryTranslator(query)
        result = query_translator.translate()
        self.assertEqual(query,result)
        
    def test_dates_utc(self):
        query = "time:[20/10/2005 17:20:20 TO 20/10/2005 17:21:20]"        
        query_translator = index.QueryTranslator(query)
        result = query_translator.translate()
        self.assertEqual("time:[2005-10-20T17:20:20Z TO 2005-10-20T17:21:20Z]",result)
 
    def test_dates_gmt_2(self):
        query = "time:[20/10/2005 17:20:20 TO 20/10/2005 17:21:20]"        
        query_translator = index.QueryTranslator(query,tzoffset="+02:00")
        result = query_translator.translate()
        self.assertEqual("time:[2005-10-20T17:20:20+02:00 TO 2005-10-20T17:21:20+02:00]",result)
        
