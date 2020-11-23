#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_ADS1015.h>

#define DATABASE_BROKER_MQTT "192.168.0.104"
#define DATABASE_BROKER_PORT 1883
#define DEVICE_ID  "pgcc008-problem02-device"
#define SUBSCRIBE_TOPIC "/interval"
#define PUBLISH_TOPIC   "/data"

#define MAX_ADC_READ 27000.0
#define MAX_HEART_FREQ 140
#define MAX_BODY_TEMP 42

#define DATABASE_LED D5
#define AWS_LED D6

const char* SSID = "Virus";
const char* PASSWORD = "91b6e1ce4e";

WiFiClient databaseBrokerClient;
PubSubClient databaseMQTT(databaseBrokerClient);

Adafruit_ADS1115 ads(0x48);

boolean databaseConnected = false;
int publishInterval = 0;
int bodyTemperature = 31;
int heartFrequency = 85;

void setup(){
  Serial.begin(115200);
  delay(10);
  Serial.println("[INFO] Serial started");

  ads.begin();
  delay(10);
  Serial.println("[INFO] ADS started");

  if(WiFi.status() == WL_CONNECTED)
    return;
         
  WiFi.begin(SSID, PASSWORD);
  while (WiFi.status() != WL_CONNECTED){
    delay(100);
  }
  Serial.println("[INFO] WiFi connected");

  databaseMQTT.setServer(DATABASE_BROKER_MQTT, DATABASE_BROKER_PORT);
  databaseMQTT.setCallback(database_mqtt_callback);

  pinMode(DATABASE_LED, OUTPUT);
  pinMode(AWS_LED, OUTPUT);
  digitalWrite(DATABASE_LED, LOW);
  digitalWrite(AWS_LED, LOW);
}

void loop(){
  heartFrequency = int(float(ads.readADC_SingleEnded(0)/MAX_ADC_READ)*MAX_HEART_FREQ);
  bodyTemperature = int(float(ads.readADC_SingleEnded(1)/MAX_ADC_READ)*MAX_BODY_TEMP);
  database_mqtt_check();
  
  delay(1000);
}

void database_mqtt_callback(char* topic, byte* payload, unsigned int length){
    String msg;
    for(int i = 0; i < length; i++){
       char c = (char)payload[i];
       msg += c;
    }
    publishInterval = msg.toInt();
    Serial.print("[INFO] New publish interval: ");
    Serial.print(publishInterval);
    Serial.println(" minute(s)");
}

void database_mqtt_check(){
  if(!databaseMQTT.connected()){
    if(databaseMQTT.connect(DEVICE_ID, "pi", "91b6e1ce4e")){
      databaseMQTT.subscribe(SUBSCRIBE_TOPIC); 
      Serial.println("[INFO] Database broker connected");
      databaseConnected = true;
      digitalWrite(DATABASE_LED, HIGH);
    }
    else{
      Serial.println("[INFO] Database broker not connected");
      databaseConnected = false;
      digitalWrite(DATABASE_LED, LOW);
    }
  }
  else{
    StaticJsonBuffer<500> jsonBuffer;
    JsonObject& JSONencoder = jsonBuffer.createObject();
    JSONencoder["temp"] = bodyTemperature;
    JSONencoder["freq"] = heartFrequency;
    
    char JSONmessageBuffer[100];
    JSONencoder.printTo(JSONmessageBuffer, sizeof(JSONmessageBuffer));
    if(databaseMQTT.publish(PUBLISH_TOPIC, JSONmessageBuffer)){
      Serial.print("[INFO] Values sent to database broker: ");
      Serial.println(JSONmessageBuffer);
    }
    else
      Serial.print("[INFO] Values not sent to database broker");
    
  }
  databaseMQTT.loop();
}
