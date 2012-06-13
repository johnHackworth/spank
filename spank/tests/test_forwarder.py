import unittest
from StringIO import StringIO
from spank.forwarder import Forwarder,ForwarderRequest

SAMPLE_INPUT="level=notice\nfacility=syslog\nhost=hadron\ntime:isodate=2012-05-23T11:06:20\nprogram=syslog-ng\n message=syslog-ng shutting down; version='3.1.3'\nend\nquit"
SAMPLE_OUTPUT='{"received": 1339062800527, "level": "notice", "facility": "syslog", "host": "hadron", "program": "syslog-ng", "time": "2012-05-23T11:06:20", "message": "syslog-ng shutting down; version=\'3.1.3\'"}1'

class IncorrectOutputException(Exception):
    pass

class FakeForwarderRequest(ForwarderRequest):
    def submit(self):
        import pdb;pdb.set_trace()
        if self.payload != SAMPLE_OUTPUT:
            raise IncorrectOutputException(self.payload)

class TestForwarder(unittest.TestCase):
    def setUp(self):
        self.input_stream = StringIO()
        self.input_stream.write(SAMPLE_INPUT)
        self.input_stream.seek(0)
        
    def test_forward(self):
        forwarder = Forwarder("http://localhost/",request_type=FakeForwarderRequest,input_stream=self.input_stream)
        try:
            forwarder.forward() 
        except Exception,e:
            self.fail(str(e))
                   
