import datetime
import decimal
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import json
import logging

#logging.basicConfig(filename='/root/mqtt_publish.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.info('Creating and configuring MQTT client')

def get_epoch_time(t, d):
	# get_epoch_time converts time data from SNS message into epoch time

	return int(datetime.datetime.strptime(
		str(d.day) + "-" + str(d.month) + "-" + str(d.year) + " " + str(t.hour) + ":" + str(t.minute) + ":" + str(t.second), '%d-%m-%Y %H:%M:%S').timestamp())

def convert_lat_long(value, dir):
	# convert_lat_long takes the NMEA formatted location data and converts it into decimal latitude and longitude.

	deg, dec = value.split('.')
	precision = len(dec)
	mins = deg[-2:] + '.' + dec
	comp = float(mins) / 60 + float(deg[:-2])
	comp = comp if (dir is 'E' or dir is 'N') else (comp / -1)
	return round(float(str(comp)), precision)

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
		
		minimal = {}
		try:
			minimal['t'] = get_epoch_time(data["fix"]["timestamp"], data["transit_data"]["datestamp"])
			minimal['lon'] = convert_lat_long(data["fix"]["lat"], data["fix"]["lat_dir"])
			minimal['lat'] = convert_lat_long(data["fix"]["lon"], data["fix"]["lon_dir"])
	
			minimal['s'] = data["transit_data"]["spd_over_grnd"]
			minimal['c'] = data["transit_data"]["true_course"]
			minimal['a'] = data["fix"]["altitude"]
		except Exception as e:
			print(e)
			pass
		
		payload_structure = {
			"state": {
				"reported": minimal
			}
		}
		payload = json.dumps(payload_structure, default=dumper, indent=0)
		self.deviceShadowHandler.shadowUpdate(payload, custom_callback, 5)

