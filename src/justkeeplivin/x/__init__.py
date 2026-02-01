from flask import Flask
from .influxdb2 import init_app as init_influx
from .mqtt import init_app as init_mqtt
from .pi1 import init_app as init_pi1

extensions = init_influx, init_mqtt, init_pi1

def init_extensions(app: Flask):
    for ext in extensions:
        ext(app)
