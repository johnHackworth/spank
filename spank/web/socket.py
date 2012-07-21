import logging
import tornado.web
import md5
import sockjs.tornado

class LiveSocketHandler(sockjs.tornado.SockJSConnection):
    def __init__(self,*args,**kwargs):
        super(LiveSocketHandler,self).__init__(*args,**kwargs)
        self.logger = logging.getLogger("spank.api")
        self.server_close = False

    def on_open(self,info):
        self.logger.info("Opening WS")
        key = md5.md5("*:*").hexdigest()
        self.application.live_messaging.subscribe(exclusive=True,routing_key=key,callback=self.on_message,close_callback=self.on_server_close)
        self.send(key)

    def on_message(self,message):
        self.send(message.body)

    def on_close(self):
        self.logger.info("Closing WS")
        if not self.server_close:
            self.application.live_messaging.unsubscribe(callback=self.on_message)

    def on_server_close(self):
        self.server_close = True
        self.close()

