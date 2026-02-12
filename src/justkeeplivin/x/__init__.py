from flask import Flask
from .mqtt import init_app as init_mqtt
from .influxdb2 import init_app as init_influx

def init_extensions(app: Flask):
    init_influx(app)
    mqtt.init_app(app)
