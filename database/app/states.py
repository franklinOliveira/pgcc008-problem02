import sys
import json
import pickle
import glob
import os
sys.path.append('/home/pi/database/interfaces')

from pahoMqtt import PahoMQTT
from awsMqtt import AwsMQTT
import datetime

class States:
    braceletMqtt = None
    braceletTimeout = 0
    braceletAvailable = False

    cloudMqtt = None

    uploadInterval = 1
    nextUploadInterval = 1
    nextUpload = None
    timeToUpload = False

    dataFromCloud = None
    nextDownload = None

    dailySamples = list()
    lastSample = [None, None, None, None]
    startDateTime = None

    def __init__(self):
        self.braceletMqtt = PahoMQTT()
        self.braceletMqtt.connect()
        print("[INO] Setup state")
        print("  Connected with local broker")
        self.cloudMqtt = AwsMQTT()
        self.cloudMqtt.connect()
        print("  Connected with cloud broker")

        self.startDateTime = datetime.datetime.now().strftime("%d-%m-%Y-%H-%M-%S")

        if len(glob.glob("/home/pi/database/app/*.samples")) > 0:
            print("  Previous samples available")
            currentSamplesDateTime = glob.glob("/home/pi/database/app/*.samples")[0].replace("/home/pi/database/app/", "")
            currentSamplesDateTime = currentSamplesDateTime.replace(".samples", "")

            currentSampleDT = datetime.datetime.strptime(currentSamplesDateTime, "%d-%m-%Y-%H-%M-%S")
            startDT = datetime.datetime.strptime(self.startDateTime, "%d-%m-%Y-%H-%M-%S")
            if startDT > (currentSampleDT + datetime.timedelta(minutes = 1440)):
                os.system("rm /home/pi/database/app/"+currentSamplesDateTime+'.samples')
                print("  Previous samples removed")
            else:
                self.startDateTime = currentSamplesDateTime
                with open('/home/pi/database/app/'+self.startDateTime+'.samples', 'rb') as file:
                    self.dailySamples = pickle.load(file)
                print("  Previous samples loaded")
        else:
            print("  Previous samples not available")
        print("  Database started at:", self.startDateTime)
        
        self.setStatus("conectada")
        print("  Bracelet available")


    def readingFromBracelet(self, first):
        if first is True:
            print("[INFO] Reading from bracelet state")

        if self.nextUploadInterval != self.cloudMqtt.uploadInterval:
            self.nextUploadInterval = self.cloudMqtt.uploadInterval
            print("  Interval changed for next upload to",self.nextUploadInterval,"minutes")
            braceletInterval = self.nextUploadInterval*2
            self.braceletMqtt.publish("/interval", braceletInterval)
            print("  Bracelet interval changed to",braceletInterval,"minutes")

        newRead = self.checkNewData()

        if newRead is True and self.braceletMqtt.dataSubscribed[0] != None:
            self.braceletAvailable = True
            self.braceletTimeout = 0
            if self.nextUpload == None:
                self.uploadInterval = self.nextUploadInterval
                self.nextUpload = (datetime.datetime.now() + datetime.timedelta(minutes = self.uploadInterval)).strftime("%H:%M:%S")
                print("  Next time to upload:", self.nextUpload)

            print("  New data:", self.braceletMqtt.dataSubscribed)
            timestamp = self.braceletMqtt.dataSubscribed[0]
            bodyTemperature = self.braceletMqtt.dataSubscribed[1]
            heartFrequency = self.braceletMqtt.dataSubscribed[2]
            sample = [False, timestamp, bodyTemperature, heartFrequency]
            self.dailySamples.append(sample)
            self.lastSample = sample

            with open('/home/pi/database/app/'+self.startDateTime+'.samples', 'wb') as file:
                pickle.dump(self.dailySamples, file)

        elif newRead is False:
            self.braceletTimeout = self.braceletTimeout + 1
            if self.braceletTimeout == 20:
                print("  Bracelet not connected")

        self.checkUpload()

    def uploadingToCloud(self, first):
        if first is True:
            print("[INFO] Uploading to cloud state")

        self.timeToUpload = False
        self.nextUpload = None

        dataOrigin = "base_local"
        bodyTemperature = list()
        heartFrequency = list()
        timestamp = list()

        print("  Uploading data to cloud")
        for sample in self.dailySamples:
            if sample[0] is False:
                timestamp.append(sample[1])
                bodyTemperature.append(sample[2])
                heartFrequency.append(sample[3])
                sample[0] = True

        data = {
                 "origem_dado":dataOrigin,
                 "temperatura":bodyTemperature,
                 "frequencia_cardiaca":heartFrequency,
                 "timestamp":timestamp
               }

        dataDump = json.dumps(data)
        self.cloudMqtt.publish("pgcc008/problem02/data", dataDump)
        print("  Data uploaded to cloud")

    def downloadingFromCloud(self, first):
        if first is True:
            print("[INFO] Downloading from cloud state")

        self.nextUploadInterval = self.cloudMqtt.uploadInterval

        if self.dataFromCloud != self.cloudMqtt.braceletData:
            self.nextDownload = None
            self.dataFromCloud = self.cloudMqtt.braceletData
            data = json.loads(self.dataFromCloud)

            if data['origem_dado'] != "base_local":
                for i in range(len(data['temperatura'])):
                    sample = [True, data['timestamp'][i], data['temperatura'][i], data['frequencia_cardiaca'][i]]
                    self.dailySamples.append(sample)

                with open('/home/pi/database/app/'+self.startDateTime+'.samples', 'wb') as file:
                    pickle.dump(self.dailySamples, file)
                print("  Data downloaded from cloud")

        else:
            if self.nextDownload == None:
                self.nextDownload = (datetime.datetime.now() + datetime.timedelta(minutes = (self.uploadInterval * 2) + 1)).strftime("%H:%M:%S")
                print("  Wait data from cloud until",self.nextDownload)
            elif self.nextDownload <= datetime.datetime.now().strftime("%H:%M:%S") and self.braceletAvailable is True:
                self.setStatus("desconectada")
                print("  Bracelet not available")
                self.braceletAvailable = False

        self.checkUpload()
        newRead = self.checkNewData()
        if newRead is True:
            self.setStatus("conectada")
            print("  Bracelet available")
            self.braceletAvailable = True
            self.braceletTimeout = 0
            self.nextDownload = None

    def checkUpload(self):
        if self.nextUpload != None and (self.nextUpload <= datetime.datetime.now().strftime("%H:%M:%S")):
            self.timeToUpload = True
            print("  Time to upload reached")

    def checkNewData(self):
        newRead = False
        nSamples = len(self.dailySamples)

        if (nSamples == 0 and self.braceletMqtt.dataSubscribed[0] != None) or (nSamples > 0 and self.braceletMqtt.dataSubscribed[0] != self.lastSample[1]):
            newRead = True
        return newRead

    def setStatus(self, status):
        timestamp = datetime.datetime.now().timestamp()
        status = {
                  "timestamp":timestamp,
                  "status":status
                 }
        statusDump = json.dumps(status)
        self.cloudMqtt.publish("pgcc008/problem02/status", statusDump)

    def stop(self):
        self.braceletMqtt.disconnect()
        self.cloudMqtt.disconnect()
