#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Forked from https://github.com/tomgidden/rpi_bluemaestro_mqtt
# Revised logic for parsing arguments and loading config (switching from json to yaml)

import os
import paho.mqtt.client as paho
import BlueMaestro
import time
import fcntl
import base64
import yaml
import argparse
import logging

# Set up argument parsing
parser = argparse.ArgumentParser(description='Monitor Blue Maestro Tempo Discs and send results via MQTT')
parser.add_argument('-c', '--config', action='store', dest='configdir', default='.',
                    help='Set config directory, default: \'.\'')
parser.add_argument('-l', '--log', action='store', dest='loglevel', default='INFO',
                    help='Set log level, default: \'info\'')
options = parser.parse_args()

# Set up loging
numeric_level = getattr(logging, options.loglevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % options.loglevel)
logging.basicConfig(level=numeric_level)

# Load externalized parameters
configfile = options.configdir + "/config.yaml"
logging.info("Loading config from: " + configfile)
with open( configfile ) as file:
    config = yaml.safe_load( file )

logging.info("Configuration:")
for name, list in config.items():
    logging.info("  Section: {}".format(name))
    for name, value in list.items():
        # We could create a formatter for logging to hide senstive data 
        # but as all we care about is the password, we'll handle it here
        if name == "password":
            logging.info("    {}: {}".format(name, "........"))
        else:
            logging.info("    {}: {}".format(name, value))

mqtt_host = config["mqtt"]["host"]
mqtt_port = config["mqtt"]["port"]
keepalive = config["mqtt"]["keepalive"]
username = config["mqtt"]["username"]
password = config["mqtt"]["password"]
client_name = config["mqtt"]["client_name"]
topic = config["mqtt"]["root_topic"]

frequency = config["monitor"]["frequency"]
temperature_calibrate = config["monitor"]["temperature_calibrate"]

# Initialize MQTT
mqtt = paho.Client(client_name)

def on_disconnect(mqtt, userdata, rc):
    logging.info("Disconnected from MQTT server with code: %s" % rc)
    logging.info(userdata)
    while rc != 0:
        try:
            time.sleep(1)
            rc = mqtt.reconnect()
        except:
            pass
        logging.info("Reconnected to MQTT server.")

mqtt.on_disconnect = on_disconnect
mqtt.username_pw_set(username, password)
mqtt.connect(mqtt_host, mqtt_port, keepalive)
mqtt.loop_start()

#  Begin monitoring 
try:

    sensor = BlueMaestro.init()

    while True:
        try:
            resultList = BlueMaestro.parse_events(sensor, 10)

            now = time.time()
            timestamp = int(now)

            logging.info("Number of devices found: %s" % ( len(resultList) ))

            for data in resultList:

                if 'data' in data: data['data'] = base64.b64encode(data['data'])
                logging.debug (data)

                try:
                    mqtt.publish('{}/{}/watchdog'.format(topic, data['name']), 'reset', retain=False)
                    for k, v in data.items():
                        mqtt.publish('{}/{}/{}'.format(topic, data['name'], k), v, retain=False)
                        mqtt.publish('{}/{}/{}/timestamp'.format(topic, data['name'], k), timestamp, retain=False)
                except ValueError as e:
                    logging.error(e)
                    logging.error(data)

            time.sleep(frequency)

        except IOError as e:
            logging.error("IOError: "+str(e))
            time.sleep(3)

except KeyboardInterrupt:
    pass
