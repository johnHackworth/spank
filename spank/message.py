import logging
import time
import tornado.ioloop
import pika

from pika.adapters.tornado_connection import TornadoConnection

class MessagingTornadoConnection(TornadoConnection):
    def _handle_disconnect(self):
        self._on_connection_closed(None, True)

class MessagingService(object):
    def __init__(self,
            host="localhost",
            port=5672,
            virtual_host="/",
            channel=None,
            username="guest",
            password="guest",
            ):
        self.host = host
        self.port = port
        self.virtual_host = virtual_host
        self.username = username
        self.password = password
        self.logger = logging.getLogger("spank.messaging")
        self.connected = False
        self.connecting = False
        self.connection = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.channel = None
        self.handlers={}


        self.ioloop = tornado.ioloop.IOLoop.instance()
        self.ioloop.add_timeout(time.time()+0.1, self.connect)


    def connect(self):
        if self.connecting:
            self.logger.info('Already connecting to RabbitMQ')
            return
        self.logger.info('Connecting to RabbitMQ on %s:%s' % (self.host,self.port))
        self.connecting = True
        credentials = pika.PlainCredentials(self.username,self.password)
        param = pika.ConnectionParameters(host=self.host,
                                          port=self.port,
                                          virtual_host=self.virtual_host,
                                          credentials=credentials)

        try: 
            self.connection = MessagingTornadoConnection(param,on_open_callback=self.on_connected)
            self.connection.add_on_close_callback(self.on_closed)
        except Exception,e:
            self.connecting = False
            self.ioloop.add_timeout(time.time()+3, self.connect)
        

    def on_connected(self, connection):
        self.connected = True
        self.connecting = False
        self.connection = connection
        self.logger.info("Connected to messaging server, openning channel")
        self.connection.channel(self.on_channel_open)
           
    def on_basic_cancel(self, frame):
        self.logger.info('Basic Cancel Ok')
        self.connection.close()

    def on_closed(self, connection):
        self.logger.info("Connection to messaging service closed")
        self.connected = False
        self.connect()


    def on_channel_open(self, channel):
        self.logger.info("Channel is open")
        self.channel = channel
        self.channel.add_on_close_callback(self.on_channel_close)

    def on_channel_close(self,frame,msg):
        self.logger.info("Channel closed, closing all handlers")
        self.channel = None
        for handler in self.handlers.values():
            handler.close()
   
    def get_channel(self):
        return self.channel

    def subscribe(self,callback,exclusive=False,durable=False,auto_delete=True,routing_key='',exchange_name="spank",exchange_type="direct",exchange_auto_delete=True,exchange_durable=False,close_callback=None):
        self.logger.info("Subscribing to queue: %s" % routing_key)
        # Ensure exchange exists
        subscribe_handler = SubscriberHandler(
          exchange_name = exchange_name,
          channel_callback=self.get_channel,
          callback=callback,
          durable=durable,
          auto_delete=auto_delete,
          routing_key=routing_key,
          close_callback = close_callback
          )

        self.channel.exchange_declare(exchange=exchange_name,
                                      type=exchange_type,
                                      auto_delete=exchange_auto_delete,
                                      durable=exchange_durable,
                                      callback= subscribe_handler.handle)
        self.handlers[callback] = subscribe_handler

    def unsubscribe(self,callback):
        self.handlers[callback].close()
        self.handlers.pop(callback)

    def publish(self,message,exchange_name="spank",exchange_type="direct",exchange_auto_delete=True,exchange_durable=False):
            publish_handler = PublishHandler(exchange_name=exchange_name,
                                             message=message,
                                             channel_callback=self.get_channel,
                                             )

            self.channel.exchange_declare(exchange=exchange_name,
                                      type=exchange_type,
                                      auto_delete=exchange_auto_delete,
                                      durable=exchange_durable,
                                      callback=publish_handler.handle)


class PublishHandler(object):
    def __init__(self,exchange_name,message,channel_callback):
        self.exchange_name = exchange_name
        self.message = message
        self.channel_callback = channel_callback
        
    def handle(self,exchange):
        properties = pika.BasicProperties(content_type=self.message.content_type,
                                          delivery_mode=self.message.delivery_mode)

        self.channel_callback().basic_publish(exchange=self.exchange_name,
                                   routing_key=self.message.routing_key,
                                   body=self.message.body,
                                   properties=properties)


class SubscriberHandler(object):
    def __init__(self,channel_callback,callback,exchange_name='',exclusive=False,durable=False,auto_delete=True,routing_key='',close_callback=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.callback = callback
        self.queue_name = ""
        self.channel_callback = channel_callback
        self.exclusive = exclusive
        self.durable = durable
        self.auto_delete = auto_delete
        self.exchange_name = exchange_name
        self.routing_key = routing_key
        self.consumer_tag = None
        self.close_callback = close_callback

    def on_channel_close(self,frame,msg):
        self.consumer_tag = None

    def handle(self,exchange):
        channel = self.channel_callback()
        channel.queue_declare(
            exclusive=self.exclusive,
            durable=self.durable,
            auto_delete=self.auto_delete,
            callback = self.on_queue_declared,
            )
        #channel.add_on_close_callback(self.on_channel_close)
    
    def callback_wrapper(self,ch,method,properties,body):
        self.logger.info("Message delivered from queue %s" % self.queue_name)
        message = Message(body=body)
        return self.callback(message)

    def on_queue_bound(self,frame):
        self.logger.info("Queue %s bound" % self.queue_name)
        self.consumer_tag = self.channel_callback().basic_consume(consumer_callback=self.callback_wrapper,queue=self.queue_name,no_ack=True)

    def on_queue_declared(self,frame):
        self.queue_name = frame.method.queue
        self.logger.info("Queue %s declared" % self.queue_name)
        self.channel_callback().queue_bind(exchange=self.exchange_name,queue=self.queue_name,routing_key=self.routing_key,callback=self.on_queue_bound)
 
    def close(self):
        channel = self.channel_callback()
        if self.consumer_tag and channel:
            self.logger.info("Closing queue %s" % self.queue_name)
            channel.basic_cancel(self.consumer_tag,callback=self.on_closed)
        if self.close_callback:
            #User provided callback may fail
            try:
                self.close_callback()
            except Exception,e:
                self.logger.info("User close() callback failed: %s" % str(e))

    def on_closed(self,frame):
        self.logger.info("Queue %s deleted" % self.queue_name)




class Message(object):
    def __init__(self,body="",routing_key="",content_type="text/plain",delivery_mode=1,exchange_name="spank"):
        self.body = body
        self.content_type = content_type
        self.delivery_mode = delivery_mode
        self.routing_key = routing_key
        self.exchange_name = exchange_name
