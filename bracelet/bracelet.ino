#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_ADS1015.h>
#include <NTPClient.h>
#include <WiFiUdp.h>
#include "FS.h"

//MQTT Bracelet ID-------------------------------------------------------------------------------------------------------
#define DEVICE_ID  "pgcc008-problem02-bracelet"

//Database broker configuration data-------------------------------------------------------------------------------------
#define DATABASE_BROKER_MQTT "192.168.0.104"
#define DATABASE_BROKER_PORT 1883
#define SUBSCRIBE_TOPIC "/interval"
#define PUBLISH_TOPIC   "/data"

//Sensors read definitios------------------------------------------------------------------------------------------------
#define MAX_ADC_READ 27000.0
#define MAX_HEART_FREQ 140
#define MAX_BODY_TEMP 42

//Digital pins configurations--------------------------------------------------------------------------------------------
#define DATABASE_LED D5
#define AWS_LED D6
#define PUBLISH_LED D7
#define DISCONNECT_BUTTON D3

//NTP time configuratios-------------------------------------------------------------------------------------------------
#define NTP_OFFSET  0     
#define NTP_INTERVAL 60 * 1000    
#define NTP_ADDRESS  "0.br.pool.ntp.org"

//NTP time instances-----------------------------------------------------------------------------------------------------
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, NTP_ADDRESS, NTP_OFFSET, NTP_INTERVAL);

//WiFi connection data---------------------------------------------------------------------------------------------------
const char* SSID = "Virus";
const char* PASSWORD = "91b6e1ce4e";

//Database broker instances----------------------------------------------------------------------------------------------
WiFiClient databaseBrokerClient;
PubSubClient databaseMQTT(databaseBrokerClient);

//AWS broker instances---------------------------------------------------------------------------------------------------
const char* AWS_endpoint = "a18jmvtsiq4e9v-ats.iot.us-east-1.amazonaws.com";
WiFiClientSecure awsBrokerClient;
void aws_broker_callback(char* topic, byte* payload, unsigned int length);
PubSubClient awsMQTT(AWS_endpoint, 8883, aws_broker_callback, awsBrokerClient);

//Sensors instances------------------------------------------------------------------------------------------------------
Adafruit_ADS1115 ads(0x48);
int bodyTemperature = 31;
int heartFrequency = 85;

//Comunication type variables--------------------------------------------------------------------------------------------
boolean databaseConnected = true;
boolean collectingData = false;
boolean disconnectState = false;

//Data collected to send to AWS------------------------------------------------------------------------------------------
unsigned long collectedTs[5];
int collectedBodyTemp[5];
int collectedHeartFreq[5];
int nSamples = 0;

//AWS publish time variables---------------------------------------------------------------------------------------------
int publishInterval = 2;
unsigned long currentTimestamp = 0;

void setup(){
  //Init serial--------------------------------------------------------------
  Serial.begin(115200);
  delay(10);
  Serial.println("[INFO] Serial started");

  //Init ADC-----------------------------------------------------------------
  ads.begin();
  delay(10);
  Serial.println("[INFO] ADS started");

  //Connects to network------------------------------------------------------
  if(WiFi.status() == WL_CONNECTED)
    return;
         
  WiFi.begin(SSID, PASSWORD);
  while (WiFi.status() != WL_CONNECTED){
    delay(100);
  }
  Serial.println("[INFO] WiFi connected");
  
  //Configures database broker communication---------------------------------
  databaseMQTT.setServer(DATABASE_BROKER_MQTT, DATABASE_BROKER_PORT);
  databaseMQTT.setCallback(database_mqtt_callback);

  //Configures NTC-----------------------------------------------------------
  timeClient.begin();
  while(!timeClient.update()){
    timeClient.forceUpdate();
  }
  awsBrokerClient.setX509Time(timeClient.getEpochTime());

  //Configures SPIFFS--------------------------------------------------------
  SPIFFS.begin();
  ESP.getFreeHeap();

  //Reads AWS certificate file and load this---------------------------------
  File cert = SPIFFS.open("/cert.der", "r"); 
  if(!cert)
    Serial.println("[INFO] Failed to open cert file");
  else{
    Serial.println("[INFO] Success to open cert file");
    if (awsBrokerClient.loadCertificate(cert))
      Serial.println("  Cert file loaded");
    else
     Serial.println("  Cert file not loaded");
  }

  //Reads AWS private key file and load this---------------------------------
  File private_key = SPIFFS.open("/private.der", "r");
  if(!private_key)
    Serial.println("[INFO] Failed to open private cert file");
  else{
    Serial.println("[INFO] Success to open private cert file");
    if (awsBrokerClient.loadPrivateKey(private_key))
      Serial.println("  Private key file loaded");
    else
      Serial.println("  Private key file not loaded");
  }

  //Reads AWS CA file and load this------------------------------------------
  File ca = SPIFFS.open("/ca.der", "r");
  if(!ca)
    Serial.println("[INFO] Failed to open ca ");
  else{
    Serial.println("[INFO] Success to open ca");
    if(awsBrokerClient.loadCACert(ca))
      Serial.println("  CA file loaded");
    else
      Serial.println("  CA file not loaded");
  }

  //Configures digital pins--------------------------------------------------
  pinMode(DATABASE_LED, OUTPUT);
  pinMode(AWS_LED, OUTPUT);
  pinMode(PUBLISH_LED, OUTPUT);
  digitalWrite(DATABASE_LED, LOW);
  digitalWrite(AWS_LED, LOW);
  digitalWrite(PUBLISH_LED, LOW);
  attachInterrupt(digitalPinToInterrupt(DISCONNECT_BUTTON), disconnectButtonDetectISR, RISING);  
}

void loop(){
  //Updates current NTC time----------------------------------------------------------
  timeClient.update();

  //Reads sensors---------------------------------------------------------------------
  heartFrequency = int(float(ads.readADC_SingleEnded(0)/MAX_ADC_READ)*MAX_HEART_FREQ);
  bodyTemperature = int(float(ads.readADC_SingleEnded(1)/MAX_ADC_READ)*MAX_BODY_TEMP);

  //Connected with local database-----------------------------------------------------
  if(collectingData == false && disconnectState == false){
    database_mqtt_check();
    delay(5000);
  }
  //Not connected with local database-------------------------------------------------
  if(databaseConnected == false || disconnectState == true){
    aws_mqtt_check();
    if(collectingData == true)
      delay(((publishInterval*60)/5)*1000);
  }
}

void database_mqtt_callback(char* topic, byte* payload, unsigned int length){
    //Gets topic message------------------------------
    String msg;
    for(int i = 0; i < length; i++){
       char c = (char)payload[i];
       msg += c;
    }
    //Converts to publish interval--------------------
    publishInterval = msg.toInt();
    Serial.print("[INFO] New publish interval: ");
    Serial.print(publishInterval);
    Serial.println(" minute(s)");
}

void database_mqtt_check(){
  //Try to connect with database broker----------------------------------------------
  if(!databaseMQTT.connected()){
    //Sucess-------------------------------------------------------------------------
    if(databaseMQTT.connect(DEVICE_ID, "pi", "91b6e1ce4e")){
      databaseMQTT.subscribe(SUBSCRIBE_TOPIC); 
      Serial.println("[INFO] Database broker connected");
      databaseConnected = true;
      digitalWrite(DATABASE_LED, HIGH);
      digitalWrite(AWS_LED, LOW);
      currentTimestamp = 0.0;
    }
    //Fail---------------------------------------------------------------------------
    else{
      if(databaseConnected == true)
       Serial.println("[INFO] Database not connected. Bracelet will publish on AWS");
      
      databaseConnected = false;
      digitalWrite(DATABASE_LED, LOW);
    }
  }
  //Publish on database broker already connected--------------------------------------
  else{
    StaticJsonBuffer<300> jsonBuffer;
    JsonObject& JSONencoder = jsonBuffer.createObject();
    JSONencoder["temp"] = bodyTemperature;
    JSONencoder["freq"] = heartFrequency;
    
    char JSONmessageBuffer[100];
    JSONencoder.printTo(JSONmessageBuffer, sizeof(JSONmessageBuffer));
    
    databaseMQTT.publish(PUBLISH_TOPIC, JSONmessageBuffer);
    
    Serial.print("[INFO] Values sent to database broker: ");
    Serial.println(JSONmessageBuffer);
    
    digitalWrite(PUBLISH_LED, HIGH);
    delay(100);
    digitalWrite(PUBLISH_LED, LOW); 
  }
  databaseMQTT.loop();
}


void aws_broker_callback(char* topic, byte* payload, unsigned int length) {
  ;
}

void aws_mqtt_check(){
  //Checks first data collection to send to AWS----------------------------
  if(collectingData == false){
    collectingData = true;
    digitalWrite(AWS_LED, HIGH);
  }

  //Gets current data and store this---------------------------------------------
  currentTimestamp = timeClient.getEpochTime();

  Serial.println("[INFO] Saving data to send to AWS");

  collectedTs[nSamples] = currentTimestamp;
  collectedBodyTemp[nSamples] = bodyTemperature;
  collectedHeartFreq[nSamples] = heartFrequency;
  
  if(nSamples < 5)
    nSamples++;
  else
    nSamples = 0;
  
  //Time to publish on AWS broker------------------------------------------------
  if(nSamples == 5){
    //Creates json---------------------------------------------------------------
    StaticJsonBuffer<300> JSONbuffer;
    JsonObject& JSONencoder = JSONbuffer.createObject();

    //Fill json------------------------------------------------------------------
    JSONencoder["origem_dado"] = "pulseira";
    JsonArray& ts = JSONencoder.createNestedArray("timestamp");
    JsonArray& bodyTemp = JSONencoder.createNestedArray("temperatura");
    JsonArray& heatFreq = JSONencoder.createNestedArray("frequencia_cardiaca");
    
    int i = 0;
    for(i = 0; i < nSamples; i++){
      ts.add(collectedTs[i]);
      bodyTemp.add(collectedBodyTemp[i]);
      heatFreq.add(collectedHeartFreq[i]);
    }

    //Prepare buffer to publish--------------------------------------------------
    char JSONmessageBuffer[300];
    JSONencoder.printTo(JSONmessageBuffer, sizeof(JSONmessageBuffer));

    //Try to connect-------------------------------------------------------------
    if(!awsMQTT.connected()){
      while(!awsMQTT.connect(DEVICE_ID)){
        Serial.print(".");
        delay(100);
      }
    }

    //Publish--------------------------------------------------------------------
    Serial.println("[INFO] AWS Broker connected");
    awsMQTT.publish("pgcc008/problem02/data", JSONmessageBuffer);

    Serial.print("[INFO] Values sent to database broker: ");
    Serial.println(JSONmessageBuffer);

    digitalWrite(PUBLISH_LED, HIGH);
    delay(100);
    digitalWrite(PUBLISH_LED, LOW);
  
    nSamples = 0;
    collectingData = false;
  }
}

ICACHE_RAM_ATTR void disconnectButtonDetectISR() {
  if (disconnectState == false){
    disconnectState = true;
    Serial.println("[INFO] Database not connected. Bracelet will publish on AWS"); 
    databaseConnected = false;
    digitalWrite(DATABASE_LED, LOW);
  }
  else
    disconnectState = false;
}
