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
from utils.error_handling import error_message

# Signal handler
def signal_handler(signal, frame):
	global interrupted
	interrupted = True
	return

signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
signal.signal(signal.SIGTSTP, signal_handler) # Ctrl+Z

##
## MQTT stuff
##

mqtt = MQTT()
mqtt.connect()

def monitor_callback(point):
	mqtt.send(point)

##
## Monitor stuff
##

monitor = UpdateMonitor(update_callback = monitor_callback)

##
## GNSS stuff
##

blob = GNSS_Blob()

##
## Main loop
##

# Global and local variables	
interrupted = False
locked = False

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



