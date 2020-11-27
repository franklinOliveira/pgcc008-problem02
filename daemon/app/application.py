import sys
sys.path.append('/home/franklin/Desktop/Projetos/pgcc008-problem02/daemon/interfaces')
from awsMqtt import AwsMQTT
import time
import json
from datetime import datetime
import pymysql

currentIntervalChangeDT = datetime.strptime("2020-11-26 12:00:00" ,'%Y-%m-%d %H:%M:%S')
cloudMqtt = AwsMQTT()
cloudMqtt.connect()

print("[INFO] Establishing connection with cloud broker")
print("  Connected with cloud broker")

print("[INFO] Running")
while True:
    try:
        db = pymysql.connect('database-2.cluster-ciaurtv8pary.us-east-1.rds.amazonaws.com', 'master', 'base2020')
        cursor = db.cursor()
        cursor.execute('use consulta_interna')
        cursor.execute("select * from intervalo_envio order by data DESC limit 1")
        data = cursor.fetchone()
        lastIntervalChangeDT = data[1]
        interval = int(data[2])

        if lastIntervalChangeDT > currentIntervalChangeDT:
            print("[INFO] New data send interval")
            print(" ",interval,"minute(s)")
            cloudMqtt.publish("pgcc008/problem02/interval", interval)
            currentIntervalChangeDT = lastIntervalChangeDT
    except:
        None

    if cloudMqtt.data != None:
        print("[INFO] New monitoring data received")
        try:
            db = pymysql.connect('database-2.cluster-ciaurtv8pary.us-east-1.rds.amazonaws.com', 'master', 'base2020')
            cursor = db.cursor()
            cursor.execute('use problem2')
            print("  Connected with database")

            data = json.loads(cloudMqtt.data)
            for i in range(len(data['temperatura'])):
                sampleDatetime = datetime.fromtimestamp(data['timestamp'][i]).strftime('%Y-%m-%d %H:%M:%S')
                dataOrigin = data['origem_dado']
                heartFrequency = data['frequencia_cardiaca'][i]
                bodyTemperature = data['temperatura'][i]

                print(" ",dataOrigin+" at "+sampleDatetime+":",str(bodyTemperature)+"ºC e",str(heartFrequency)+" BPM")

                format = (sampleDatetime, bodyTemperature, heartFrequency, dataOrigin)
                sql = """insert into dados_corporais (data,temperatura,freq_card,origem_dado) values (%s, %s, %s, %s)"""
                cursor.execute(sql,format)
                db.commit()

            print("  Disconnected")
            cloudMqtt.data = None
        except:
            print("  Not connected with database")

    if cloudMqtt.status != None:
        print("[INFO] New status received")
        try:
            db = pymysql.connect('database-2.cluster-ciaurtv8pary.us-east-1.rds.amazonaws.com', 'master', 'base2020')
            cursor = db.cursor()
            cursor.execute('use problem2')
            print("  Connected with database")

            data = json.loads(cloudMqtt.status)
            statusDatetime = datetime.fromtimestamp(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            status = data['status']

            print(" ",sampleDatetime+":",str(status))

            format = (statusDatetime, status)
            sql = """insert into status_pulseira (data,status) values (%s, %s)"""
            cursor.execute(sql,format)
            db.commit()

            print("  Disconnected")
            cloudMqtt.status = None
        except:
            print("  Not connected with database")
    time.sleep(1)

cloudMqtt.disconnect()
