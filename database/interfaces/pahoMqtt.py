import paho.mqtt.client as mqtt
import json
import datetime

class PahoMQTT():
    client = None
    BROKER_NAME = "database.local"
    BROKER_PORT = 1883
    CLIENT_NAME = "pgcc008-problem02-database-local"

    dataSubscribed = [None,None,None]

    def __init__(self):
        self.client = mqtt.Client("pgcc008-problem02-database-local")

    def connect(self):
        self.client.connect(self.BROKER_NAME,self.BROKER_PORT,60)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.loop_start()

    def disconnect(self):
        self.client.disconnect()
        self.client.loop_stop()

    def on_connect(self, client, userdata, flags, rc):
        self.client.subscribe("/data")

    def on_message(self, client, userdata, msg):
        timestamp = datetime.datetime.now().timestamp()
        data = json.loads(msg.payload.decode())

        self.dataSubscribed[0] = timestamp
        self.dataSubscribed[1] = data['temp']
        self.dataSubscribed[2] = data['freq']

    def publish(self, topic, msg):
        self.client.publish(topic, msg)
