import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT

class AwsMQTT():
    MQTTClient = None
    data = None
    status = None

    def __init__(self):
        #Path to AWS IoT Core certificates and keys
        ROOT_PATH = "/home/franklin/Desktop/Projetos/pgcc008-problem02/daemon/"
        ROOT_CA_PATH = ROOT_PATH+"certificates/AmazonRootCA1.pem.txt"
        KEY_PATH = ROOT_PATH+"certificates/b4078a262d-private.pem.key"
        CERT_PATH = ROOT_PATH+"certificates/b4078a262d-certificate.pem.crt"

        #Configures MQTTClient (device) with AWS MQTT Broker endpoint
        self.MQTTClient = AWSIoTPyMQTT.AWSIoTMQTTClient("pgcc008-problem02-daemon")
        self.MQTTClient.configureEndpoint("a18jmvtsiq4e9v-ats.iot.us-east-1.amazonaws.com", 8883)
        self.MQTTClient.configureCredentials(ROOT_CA_PATH, KEY_PATH, CERT_PATH)

        #Starts the process of subscribe topics
        self.MQTTClient.subscribe("pgcc008/problem02/status", 0, self.dataChangeCallback)
        self.MQTTClient.subscribe("pgcc008/problem02/data", 0, self.dataChangeCallback)

    #Subscribe data from topics
    def dataChangeCallback(self, client, userdata, message):
        if message.topic == "pgcc008/problem02/data":
            self.data = message.payload.decode("utf-8")
        elif message.topic == "pgcc008/problem02/status":
            self.status = message.payload.decode("utf-8")

    #Connects MQTTClient (device) with AWS MQTT Broker
    def connect(self):
        self.MQTTClient.connect()

    #Disconnects MQTTClient (device) of AWS MQTT Broker
    def disconnect(self):
        self.MQTTClient.disconnect()

    #Publish a data on topic
    def publish(self, topic, data):
        self.MQTTClient.publish(topic, data, 1)
