import logging
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response
import pymysql
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        speak_output = "Olá! O que você deseja fazer?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )
        
        
class IntervalChangeIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("IntervalChangeIntent")(handler_input)

    def handle(self, handler_input):
        minutes = handler_input.request_envelope.request.intent.slots['minutos'].value
        
        try:
            minutes = int(minutes)
            if minutes <= 0:
                None
            else:
                speak_output = "Entendido! O intervalo de envio foi configurado para "+str(minutes)+" minutos."
                try:
                    currentDateTime = (datetime.now() - timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')
                    db = pymysql.connect('database-2.cluster-ciaurtv8pary.us-east-1.rds.amazonaws.com', 'master', 'base2020')
                    cursor = db.cursor()
                    cursor.execute('use consulta_interna')
                    format = (currentDateTime, str(minutes))
                    sql = """insert into intervalo_envio (data,tempo_envio) values (%s, %s)"""
                    cursor.execute(sql, format)
                    db.commit()
                except:
                    speak_output = "Desculpa! O serviço está indisponível no momento. Tente novamente mais tarde!"
                                
        except:
            None
        

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class TimeOfflineChangeIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("TimeOfflineChangeIntent")(handler_input)

    def handle(self, handler_input):
        minutes = handler_input.request_envelope.request.intent.slots['minutos'].value
        
        try:
            minutes = int(minutes)
            if minutes <= 0:
                None
            else:
                speak_output = "Entendido! O tempo de desconexão foi configurado para "+str(minutes)+" minutos."
                
                currentDateTime = (datetime.now() - timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')
                try:
                    db = pymysql.connect('database-2.cluster-ciaurtv8pary.us-east-1.rds.amazonaws.com', 'master', 'base2020')
                    cursor = db.cursor()
                    cursor.execute('use consulta_interna')
                    format = (currentDateTime, str(minutes))
                    sql = """insert into alerta_deconec (data,tempo_alerta) values (%s, %s)"""
                    cursor.execute(sql, format)
                    db.commit()
                except:
                    speak_output = "Desculpa! O serviço está indisponível no momento. Tente novamente mais tarde!"
        except:
            None
            
        

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class GetIntervalIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("GetIntervalIntent")(handler_input)

    def handle(self, handler_input):
        try:
            db = pymysql.connect('database-2.cluster-ciaurtv8pary.us-east-1.rds.amazonaws.com', 'master', 'base2020')
            cursor = db.cursor()
            cursor.execute('use consulta_interna')
            cursor.execute("select * from intervalo_envio order by data DESC limit 1")
            data = cursor.fetchone()
            
            if data is None:
                speak_output = "Desculpa! Mas o tempo de atualização dos dados não está disponível. Tente novamente mais tarde!"
            else:
                lastDatetime = data[1].strftime("%d/%m/%Y às %H horas, %M minutos e %S segundos")
                lastInterval = data[2]
            
                speak_output = "O tempo de atualização dos dados é de "+str(int(lastInterval))+" minutos."
                speak_output = speak_output+" Informação configurada no dia "+lastDatetime+"."
        except:
            speak_output = "Desculpa! O serviço está indisponível no momento. Tente novamente mais tarde!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )
        

class GetTimeOfflineIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("GetTimeOfflineIntent")(handler_input)

    def handle(self, handler_input):
        try:
            db = pymysql.connect('database-2.cluster-ciaurtv8pary.us-east-1.rds.amazonaws.com', 'master', 'base2020')
            cursor = db.cursor()
            cursor.execute('use consulta_interna')
            cursor.execute("select * from alerta_deconec order by data DESC limit 1")
            data = cursor.fetchone()
            
            if data is None:
                speak_output = "Desculpa! A tolerância de ausência de novos dados não está disponível. Tente novamente mais tarde!"
            else:
                lastDatetime = data[1].strftime("%d/%m/%Y às %H horas, %M minutos e %S segundos")
                lastTimeOffline = data[2]
            
                speak_output = "A tolerância de ausência de novos dados é de "+str(int(lastTimeOffline))+" minutos."
                speak_output = speak_output+" Informação configurada no dia "+lastDatetime+"."
        except:
            speak_output = "Desculpa! O serviço está indisponível no momento. Tente novamente mais tarde!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )
        
class GetBraceletStatusIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("GetBraceletStatusIntent")(handler_input)

    def handle(self, handler_input):
        try:
            db = pymysql.connect('database-2.cluster-ciaurtv8pary.us-east-1.rds.amazonaws.com', 'master', 'base2020')
            cursor = db.cursor()
            cursor.execute('use problem2')
            cursor.execute("select data,status from status_pulseira order by data DESC limit 1")
            data = cursor.fetchone()
            
            if data is None:
                speak_output = "Desculpa! Mas o status da pulseira não está disponível. Tente novamente mais tarde!"
            else:
                lastDatetime = data[0].strftime("%d/%m/%Y às %H horas, %M minutos e %S segundos")
                lastStatus = data[1]
            
                speak_output = "A pulseira está "+lastStatus+" desde o dia "+lastDatetime+"."
                
        except:
            speak_output = "Desculpa! O serviço está indisponível no momento. Tente novamente mais tarde!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )
        
class GetDataIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("GetDataIntent")(handler_input)

    def handle(self, handler_input):
        try:
            db = pymysql.connect('database-2.cluster-ciaurtv8pary.us-east-1.rds.amazonaws.com', 'master', 'base2020')
            cursor = db.cursor()
            cursor.execute('use problem2')
            cursor.execute("select * from dados_corporais order by data DESC limit 1")
            data = cursor.fetchone()
            
            if data is None:
                speak_output = "Desculpa! Mas não existem dados de monitoramento disponíveis. Tente novamente mais tarde!"
            else:
                lastDatetime = data[1].strftime("%d/%m/%Y às %H horas, %M minutos e %S segundos")
                lastBodyTemperature = data[2]
                lastHeartFrequency = data[3]
                lastDataOrigin = data[4]
            
                speak_output = "A sua temperatura corporal é de "+str(lastBodyTemperature)+" ºC e a frequência cardíaca é de "+str(int(lastHeartFrequency))+" BPM. "
                speak_output = speak_output+"Dados informados no dia "+lastDatetime+" pela "+lastDataOrigin+"."
                
        except:
            speak_output = "Desculpa! O serviço está indisponível no momento. Tente novamente mais tarde!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        speak_output = "Goodbye!"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)

        speak_output = "O dado informado é inválido! Tente novamente."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(IntervalChangeIntentHandler())
sb.add_request_handler(TimeOfflineChangeIntentHandler())
sb.add_request_handler(GetIntervalIntentHandler())
sb.add_request_handler(GetTimeOfflineIntentHandler())
sb.add_request_handler(GetBraceletStatusIntentHandler())
sb.add_request_handler(GetDataIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) 
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()