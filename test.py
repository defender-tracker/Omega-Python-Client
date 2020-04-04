# Imports
import serial
import datetime
import time
import signal
import sys
import pynmea2
import json
import os
import logging
import shelve
from threading import Thread
from persistqueue import Queue

ts = datetime.datetime.timestamp(datetime.datetime.now())

logging.basicConfig(
	filename='/mnt/mmcblk0p1/logs_' + str(ts) + '.log',
	filemode='w',
	format='%(asctime)s - %(name)s - %(filename)s(%(lineno)d) - %(levelname)s - %(message)s',
	level=logging.DEBUG
)

from utils.nmea import GNSS_Blob
from utils.aws import MQTT
from utils.monitor import Sampler
from utils.error_handling import error_message

##
## MQTT stuff
##

mqtt = MQTT()
mqtt.connect()
	
##
## Queue
##
	
q = Queue(path="/mnt/mmcblk0p1/queue")

def worker():
    while True:
        item = q.get()
        if mqtt.send(item):
        	logging.info("Send was successful")
	        q.task_done()

for i in range(2):
     t = Thread(target=worker)
     t.daemon = True
     t.start()

##
## Monitor stuff
##

def monitor_callback(point):
	#mqtt.send(point)
	q.put(point)

sampler = Sampler(update_callback = monitor_callback)

##
## GNSS stuff
##

blob = GNSS_Blob()


def settings_update(config):
	try:
		if config.get('sampling_distance'):
			sampler.set_sampling_distance(config.get('sampling_distance'))
		else:
			# set default value
			config['sampling_distance'] = 500
			
		if config.get('pause_distance'):
			sampler.set_pause_distance(config.get('pause_distance'))
		else:
			config['pause_distance'] = 0.5
			
		if config.get('resume_distance'):
			sampler.set_resume_distance(config.get('resume_distance'))
		else:
			config['resume_distance'] = 2
			
		if config.get('moving_average_length'):
			sampler.set_moving_average_length(config.get('moving_average_length'))
		else:
			config['moving_average_length'] = 20
		
	except Exception as e:
		logging.error(error_message(e))
		pass
	
with shelve.open('/root/config') as config:
    settings_update(config)
    config.close()

##
## Main loop
##
try:
	os.remove("sampler_history")
except:
	logging.info('Sampler history does not exist')
	pass

with open('/root/test_data.json') as td:
	items = json.load(td)
	
	keys = list(items.keys())
	keys.sort(key=int)
	
	for key in keys:
		update = items.get(key)
		sampler.process_update(update)
