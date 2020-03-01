# Imports
from utils.error_handling import error_message
from utils.monitor import UpdateMonitor
from utils.aws import MQTT
from utils.nmea import GNSS_Blob
import serial
import datetime
import time
import signal
import sys
import pynmea2
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


# Signal handler

def signal_handler(signal, frame):
    global interrupted
    interrupted = True
    return


signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
signal.signal(signal.SIGTSTP, signal_handler)  # Ctrl+Z

##
# MQTT stuff
##

mqtt = MQTT()
mqtt.connect()

##
# Queue
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
# Monitor stuff
##


def monitor_callback(point):
        # mqtt.send(point)
    q.put(point)


monitor = UpdateMonitor(update_callback=monitor_callback)

##
# GNSS stuff
##

blob = GNSS_Blob()


def settings_update(config):
    try:
        if config.get('sampling_distance'):
            monitor.set_sampling_distance(config.get('sampling_distance'))
        else:
            # set default value
            config['sampling_distance'] = 500

        if config.get('pause_distance'):
            monitor.set_pause_distance(config.get('pause_distance'))
        else:
            config['pause_distance'] = 0.5

        if config.get('resume_distance'):
            monitor.set_resume_distance(config.get('resume_distance'))
        else:
            config['resume_distance'] = 2

        if config.get('moving_average_length'):
            monitor.set_moving_average_length(
                config.get('moving_average_length'))
        else:
            config['moving_average_length'] = 10

    except Exception as e:
        logging.error(error_message(e))
        pass


with shelve.open('config') as config:
    settings_update(config)
    config.close()

##
# Main loop
##

# Global and local variables
interrupted = False
locked = False

# Read serial data in an endless loop
with serial.Serial('/dev/ttyUSB1', timeout=0.1) as tty:

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
                    #logging.DEBUG("Data captured - store/send")
                    minimal, full = blob.get_base_information()
                    monitor.process(minimal)

                    try:
                        with shelve.open('/mnt/mmcblk0p1/raw' + str(ts) + '.db') as raw:
                            raw[str(minimal.get('t'))] = full
                            raw.close()
                    except Exception as e:
                        logging.error("Failed to persit raw data")
                        logging.error(error_message(e))
                        continue

            else:
                locked = False
                blob.reset()

        except Exception as e:
            logging.error("Exception in Main")
            logging.error(error_message(e))
            continue

# Graceful close down
logging.info("Graceful close down")
