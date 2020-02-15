import datetime
import decimal
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import json
import logging

#logging.basicConfig(filename='/root/mqtt_publish.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)
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
        
class MQTT:

	def __init__(self):
		self.thingName = "defender_tracker_iot_thing"

		self.myClient = AWSIoTMQTTShadowClient(self.thingName)
		self.myClient.configureEndpoint("a1su4r2osfdyi1-ats.iot.eu-west-2.amazonaws.com", 8883)
		self.myClient.configureCredentials("/root/connect_device_package/root-CA.crt", "/root/connect_device_package/7519928cd5-private.pem.key", "/root/connect_device_package/7519928cd5-certificate.pem.cer")
		self.myClient.configureConnectDisconnectTimeout(10)
		self.myClient.configureMQTTOperationTimeout(120)

	def connect(self):
		print('Connecting to AWS IoT')
		self.myClient.connect()
		
		self.deviceShadowHandler = self.myClient.createShadowHandlerWithName(self.thingName, True)

	def send(self, data):
		logging.info('Updating device shadow')
		
		payload_structure = {
			"state": {
				"reported": data
			}
		}
		payload = json.dumps(payload_structure, default=dumper, indent=0)
		self.deviceShadowHandler.shadowUpdate(payload, custom_callback, 5)

