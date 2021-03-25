#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Forked from https://github.com/tomgidden/rpi_bluemaestro_mqtt
# Config changes adapted from https://github.com/jenswilly/OpenHAB-Scripts

# TODO:
# * Adapt Config and Logging from NateEaton/igrill

import os
import paho.mqtt.client as paho
import BlueMaestro
import time
import fcntl
import base64
import json

# Simplistic approach to externalizing parameters
configfile = "/home/pi/rpi_bluemaestro_mqtt/config.json"
print("Loading config from: " + configfile)
with open( configfile ) as json_file:
    config = json.load( json_file )

print("Configuration:")
print(config)

mqtt_host = config["MQTT"]["HOST"]
mqtt_port = config["MQTT"]["PORT"]
keepalive = config["MQTT"]["KEEPALIVE"]
username = config["MQTT"]["USERNAME"]
password = config["MQTT"]["PASSWORD"]
client_name = config["MQTT"]["CLIENT_NAME"]
topic = config["MQTT"]["ROOT_TOPIC"]

frequency = config["monitor"]["frequency"]
temperature_calibrate = config["monitor"]["temperature_calibrate"]

mqtt = paho.Client(client_name)

def on_disconnect(mqtt, userdata, rc):
    print("Disconnected from MQTT server with code: %s" % rc)
    print(userdata)
    while rc != 0:
        try:
            time.sleep(1)
            rc = mqtt.reconnect()
        except:
            pass
        print("Reconnected to MQTT server.")

mqtt.on_disconnect = on_disconnect
mqtt.username_pw_set(username, password)
mqtt.connect(mqtt_host, mqtt_port, keepalive)
mqtt.loop_start()


def callback(data):
    now = time.time()
    timestamp = int(now)
    if 'data' in data: data['data'] = base64.b64encode(data['data'])
    print (data)

    try:
        mqtt.publish('{}/{}/watchdog'.format(topic, data['name']), 'reset', retain=False)
        for k, v in data.items():
            mqtt.publish('{}/{}/{}'.format(topic, data['name'], k), v, retain=False)
            mqtt.publish('{}/{}/{}/timestamp'.format(topic, data['name'], k), timestamp, retain=False)
    except ValueError as e:
        print (e)
        print (data)


try:
    while True:
        try:
            sensor = BlueMaestro.init()
            BlueMaestro.get(sensor, callback)
            time.sleep(frequency)

        except IOError as e:
            print("IOError: "+str(e))
            time.sleep(3)

except KeyboardInterrupt:
    pass
