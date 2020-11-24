import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT

class AwsMQTT():
    MQTTClient = None
    #Saves min and max temp limits
    uploadInterval = 1
    braceletData = None

    def __init__(self):
        #Path to AWS IoT Core certificates and keys
        ROOT_PATH = "/home/pi/database/"
        ROOT_CA_PATH = ROOT_PATH+"certificates/AmazonRootCA1.pem.txt"
        KEY_PATH = ROOT_PATH+"certificates/4d327b67ce-private.pem.key"
        CERT_PATH = ROOT_PATH+"certificates/4d327b67ce-certificate.pem.crt"

        #Configures MQTTClient (device) with AWS MQTT Broker endpoint
        self.MQTTClient = AWSIoTPyMQTT.AWSIoTMQTTClient("pgcc008-problem01-device")
        self.MQTTClient.configureEndpoint("a18jmvtsiq4e9v-ats.iot.us-east-1.amazonaws.com", 8883)
        self.MQTTClient.configureCredentials(ROOT_CA_PATH, KEY_PATH, CERT_PATH)

        #Starts the process of subscribe topics
        self.MQTTClient.subscribe("pgcc008/problem02/interval", 0, self.dataChangeCallback)
        self.MQTTClient.subscribe("pgcc008/problem02/data", 0, self.dataChangeCallback)

    #Subscribe data from topics
    def dataChangeCallback(self, client, userdata, message):
        if message.topic == "pgcc008/problem02/interval":
            self.uploadInterval = int(message.payload.decode("utf-8"))
        else:
            self.braceletData = message.payload.decode("utf-8")


    #Connects MQTTClient (device) with AWS MQTT Broker
    def connect(self):
        self.MQTTClient.connect()

    #Disconnects MQTTClient (device) of AWS MQTT Broker
    def disconnect(self):
        self.MQTTClient.disconnect()

    #Publish a data on topic
    def publish(self, topic, data):
        self.MQTTClient.publish(topic, data, 1)
