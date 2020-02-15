# Imports
import serial
import datetime
import time
import signal
import sys
import pynmea2
import logging

logging.basicConfig(filename='/root/mqtt_publish.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)

from utils.nmea import GNSS_Blob
from utils.aws import MQTT
from utils.monitor import UpdateMonitor

# Signal handler
def signal_handler(signal, frame):
	global interrupted
	interrupted = True
	return
	
def error_message(err):
	template = "An exception of type {0} occurred. Arguments:\n{1!r}"
	message = template.format(type(err).__name__, err.args)
	return message

# Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

# Ctrl+Z
signal.signal(signal.SIGTSTP, signal_handler)

# Global and local variables	
interrupted = False
locked = False

reader = pynmea2.NMEAStreamReader()
mqtt = MQTT()
mqtt.connect()

blob = GNSS_Blob()
monitor = UpdateMonitor()

def monitor_callback(point):
	mqtt.send(point)
	
monitor.accepted_callback = monitor_callback

# Read serial data in an endless loop
with serial.Serial('/dev/ttyUSB1', timeout = 0.1) as tty:

	while not interrupted:
		try:
			# Read data line from serial
			line = tty.readline()
			line = line.decode('utf-8').strip()
			
			if len(line) > 6:
				sentence_type = line[1:6]
				try:
					msg = pynmea2.parse(line)
				except Exception as e:
					logging.error(error_message(e))
					continue
					
				if not locked:
					if msg.sentence_type == 'GSV':
						# GPS Satellites in view
						blob.add_satellite(msg)
						
					locked = blob.check_satellites()	
					
				else:
					if msg.sentence_type == 'GGA':
						# Global Positioning System Fix Data
						blob.add_fix_data(msg)
						
					elif msg.sentence_type == 'VTG':
						# Track made good and ground speed
						blob.add_track_and_ground_speed(msg)
						
					elif msg.sentence_type == 'RMC':
						# Recommended minimum specific GPS/Transit data
						blob.add_minimum_transit_data(msg)
						
					elif msg.sentence_type == 'GSA':
						# GPS DOP and active satellites
						blob.add_DOP(msg)
						
				if blob.is_complete():
					monitor.process(blob.get_base_information())	
					
			else:
				locked = False
				blob.reset()
				
		except Exception as e:
			logging.error(error_message(e))
			continue
	
# Graceful close down
logging.info("Graceful close down")



