import datetime
import decimal
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient, AWSIoTMQTTShadowClient
import json
import logging

logging.info('Creating and configuring MQTT client')

def custom_callback(message, something, meh):
	json_object = json.loads(message)
	formatted_message = json.dumps(json_object, indent=2)
	logging.info(formatted_message)
	logging.info(something)
	logging.info(meh)

def dumper(obj):
	try:
		return obj.toJSON()
	except:
		if isinstance(obj, datetime.date):
			return dict(year=obj.year, month=obj.month, day=obj.day)
		elif isinstance(obj, datetime.time):
			return dict(hour=obj.hour, minute=obj.minute, second=obj.second)
		elif isinstance(obj, decimal.Decimal):
			return float(obj)
		else:
			return obj.__dict__
			
class CallbackContainer(object):

	def __init__(self, client):
		self._client = client

	def messagePrint(self, client, userdata, message):
		print("Received a new message: ")
		print(message.payload)
		print("from topic: ")
		print(message.topic)
		print("--------------\n\n")

	def messageForward(self, client, userdata, message):
		topicRepublish = message.topic + "/republish"
		print("Forwarding message from: %s to %s" % (message.topic, topicRepublish))
		print("--------------\n\n")
		self._client.publishAsync(topicRepublish, str(message.payload), 1, self.pubackCallback)

	def pubackCallback(self, mid):
		print("Received PUBACK packet id: ")
		print(mid)
		print("++++++++++++++\n\n")

	def subackCallback(self, mid, data):
		print("Received SUBACK packet id: ")
		print(mid)
		print("Granted QoS: ")
		print(data)
		print("++++++++++++++\n\n")
		
		
def delta_callback(payload, responseStatus, token):
	# payload is a JSON string ready to be parsed using json.loads(...)
	# in both Py2.x and Py3.x
	print(responseStatus)
	payloadDict = json.loads(payload)
	print("++++++++DELTA++++++++++")
	print("property: " + str(payloadDict["state"]["property"]))
	print("version: " + str(payloadDict["version"]))
	print("+++++++++++++++++++++++\n\n")



class MQTT:

	def __init__(self):
		self.thingName = "defender_tracker_iot_thing"
		
		self.pub_client = AWSIoTMQTTClient(self.thingName)
		#self.shadow_client = AWSIoTMQTTShadowClient(self.thingName)

		self.pub_client.configureEndpoint(
			"a1su4r2osfdyi1-ats.iot.eu-west-2.amazonaws.com",
			8883
		)
		self.pub_client.configureCredentials(
			"/root/root-CA.crt",
			"/root/7519928cd5-private.pem.key",
			"/root/7519928cd5-certificate.pem.cer"
		)
		self.pub_client.configureOfflinePublishQueueing(-1)
		self.pub_client.configureConnectDisconnectTimeout(10)
		self.pub_client.configureMQTTOperationTimeout(120)
		
		#self.shadow_client.configureEndpoint(
		#	"a1su4r2osfdyi1-ats.iot.eu-west-2.amazonaws.com",
		#	8883
		#)
		#self.shadow_client.configureCredentials(
		#	"/root/root-CA.crt",
		#	"/root/7519928cd5-private.pem.key",
		#	"/root/7519928cd5-certificate.pem.cer"
		#)
		#self.shadow_client.configureAutoReconnectBackoffTime(1, 32, 20)
		#self.shadow_client.configureConnectDisconnectTimeout(10)  # 10 sec
		#self.shadow_client.configureMQTTOperationTimeout(5)  # 5 sec


	def connect(self):
		print('Connecting to AWS IoT')
		self.pub_client.connect()
		#self.shadow_client.connect()

		#self.shadow_handler = self.shadow_client.createShadowHandlerWithName(self.thingName, True)
		#self.shadow_handler.shadowRegisterDeltaCallback(delta_callback)
		
		#self.deviceShadowHandler.shadowUpdate(payload, custom_callback, 5)

		
	def send(self, data):
		logging.info('Sending data to AWS')
		
		payload = json.dumps(data, default=dumper, indent=0)
		return self.pub_client.publish(self.thingName + "/transit", payload, 1)
	

