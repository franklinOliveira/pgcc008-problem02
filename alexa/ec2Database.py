import pymysql
import datetime

#SELECTS
#Consulta os dados atuais-------------------------------------------------------
db = pymysql.connect('database-2.cluster-ciaurtv8pary.us-east-1.rds.amazonaws.com', 'master', 'base2020')
cursor = db.cursor()
cursor.execute('use problem2')
cursor.execute("select * from dados_corporais order by data DESC limit 1")
data = cursor.fetchone()

if data is None:
    speak_output = "Desculpa! Mas não existem dados de monitoramento disponíveis. Tente novamente mais tarde!"
else:
    lastDatetime = data[1].strftime("%d/%m/%Y às %H:%M:%S")
    lastBodyTemperature = data[2]
    lastHeartFrequency = data[3]
    lastDataOrigin = data[4]

    speak_output = "A sua temperatura corporal é de "+str(lastBodyTemperature)+" ºC e a frequencia cardíaca é de "+str(lastHeartFrequency)+" BPM. "
    speak_output = speak_output+"Dados informados no dia "+lastDatetime+" pela "+lastDataOrigin+"."
print(speak_output)

#Consulta status da pulseira----------------------------------------------------
db = pymysql.connect('database-2.cluster-ciaurtv8pary.us-east-1.rds.amazonaws.com', 'master', 'base2020')
cursor = db.cursor()
cursor.execute('use problem2')
cursor.execute("select data,status from status_pulseira order by data DESC limit 1")
data = cursor.fetchone()

if data is None:
    speak_output = "Desculpa! Mas o status da pulseira não está disponível. Tente novamente mais tarde!"
else:
    lastDatetime = data[0].strftime("%d/%m/%Y às %H:%M:%S")
    lastStatus = data[1]

    speak_output = "A pulseira está "+lastStatus+" desde o dia "+lastDatetime+"."
print(speak_output)

#Consulta o tempo de desconexão-------------------------------------------------
db = pymysql.connect('database-2.cluster-ciaurtv8pary.us-east-1.rds.amazonaws.com', 'master', 'base2020')
cursor = db.cursor()
cursor.execute('use consulta_interna')
cursor.execute("select * from alerta_deconec order by data DESC limit 1")
data = cursor.fetchone()

if data is None:
    speak_output = "Desculpa! Mas o tempo máximo de desconexão não está disponível. Tente novamente mais tarde!"
else:
    lastDatetime = data[1].strftime("%d/%m/%Y às %H:%M:%S")
    lastTimeOffline = data[2]

    speak_output = "O tempo máximo de desconexão atual é de "+str(int(lastTimeOffline))+" minutos."
    speak_output = speak_output+" Informação configurada no dia "+lastDatetime+"."
print(speak_output)

#Consulta o tempo de envio------------------------------------------------------
db = pymysql.connect('database-2.cluster-ciaurtv8pary.us-east-1.rds.amazonaws.com', 'master', 'base2020')
cursor = db.cursor()
cursor.execute('use consulta_interna')
cursor.execute("select * from intervalo_envio order by data DESC limit 1")
data = cursor.fetchone()

if data is None:
    speak_output = "Desculpa! Mas o intervalo de envio não está disponível. Tente novamente mais tarde!"
else:
    lastDatetime = data[1].strftime("%d/%m/%Y às %H:%M:%S")
    lastInterval = data[2]

    speak_output = "O intervalo de envio de dados atual é de "+str(int(lastInterval))+" minutos."
    speak_output = speak_output+" Informação configurada no dia "+lastDatetime+"."
print(speak_output)

#INSERTS
#Define o tempo de desconexão---------------------------------------------------
minutes = 2
currentDateTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
db = pymysql.connect('database-2.cluster-ciaurtv8pary.us-east-1.rds.amazonaws.com', 'master', 'base2020')
cursor = db.cursor()
cursor.execute('use consulta_interna')
format = (currentDateTime, str(minutes))
sql = """insert into alerta_deconec (data,tempo_alerta) values (%s, %s)"""
cursor.execute(sql, format)
db.commit()

#Define o tempo de envio--------------------------------------------------------
minutes = 5
currentDateTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
db = pymysql.connect('database-2.cluster-ciaurtv8pary.us-east-1.rds.amazonaws.com', 'master', 'base2020')
cursor = db.cursor()
cursor.execute('use consulta_interna')
format = (currentDateTime, str(minutes))
sql = """insert into intervalo_envio (data,tempo_envio) values (%s, %s)"""
cursor.execute(sql, format)
db.commit()
