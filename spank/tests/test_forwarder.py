import unittest
import json
import urllib2
import time
from mock import Mock,patch,call
from StringIO import StringIO
from spank.forwarder import Forwarder,ForwarderRequest

SAMPLE_INPUT="level=notice\nfacility=syslog\nhost=hadron\ntime:isodate=2012-05-23T11:06:20\nprogram=syslog-ng\n message=syslog-ng shutting down; version='3.1.3'\nend\nquit"
SAMPLE_OUTPUT='{"received": 1339062800527, "level": "notice", "facility": "syslog", "host": "hadron", "program": "syslog-ng", "time": "2012-05-23T11:06:20", "message": "syslog-ng shutting down; version=\'3.1.3\'"}'

class TestForwarder(unittest.TestCase):
    def setUp(self):
        self.input_stream = StringIO()
        self.input_stream.write(SAMPLE_INPUT)
        self.input_stream.seek(0)
    
    @patch("urllib2.urlopen",autospec=True)
    @patch("time.time",autospec=True)
    def test_forward(self,time_time_mock,urllib2_urlopen_mock):
        time_time_mock.return_value=1339062800.527
        forwarder = Forwarder("http://localhost/",input_stream=self.input_stream)
        forwarder.forward() 
        self.assertEqual(True,urllib2_urlopen_mock.called)
        self.assertIn(call.read,urllib2_urlopen_mock.mock_calls)
        self.assertEqual(urllib2_urlopen_mock.call_args[0][0].headers,{'Content-type': 'application/json'})
        self.assertEqual(urllib2_urlopen_mock.call_args[0][0].data,SAMPLE_OUTPUT)
                   
