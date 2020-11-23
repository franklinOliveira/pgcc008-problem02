import paho.mqtt.client as mqtt
import json
import datetime

class PahoMqtt():
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
        print("Connected")

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
        print(datetime.datetime.fromtimestamp(timestamp), self.dataSubscribed)

    def publish(self, topic, msg):
        self.client.publish(topic, msg)

pahoMqtt = PahoMqtt()
pahoMqtt.connect()

data = 1
while data != 0:
    data = input("Determine a frequencia de envio: ")
    pahoMqtt.publish("/interval", data)
pahoMqtt.disconnect()
