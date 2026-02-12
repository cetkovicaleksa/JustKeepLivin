from typing import cast

from .x.mqtt import mqtt, Client, try_parse_message, Message
from .x.influxdb2 import write, Point

topics = [
    ("home/+/door", 0),
    ("home/+/motion", 0),
    ("home/+/proximity", 0),
    ("home/+/temperature", 0),
    ("home/+/typing", 0),
    ("home/+/gyro", 0),
    ("home/+/remote", 0),
]

def init_app(app):
    mqtt.subscribe(topics)

KEY_LOCATION = "location"
KEY_SIMULATED = "simulated"

def _is_simulated(data: dict) -> bool:
    return data.get(KEY_SIMULATED, False) in {True, 'true', 'True', 1}

@mqtt.on_topic("home/+/door")
def on_door_message(client: Client, userdata: object, message: Message):
    location = message.topic.split('/')[1]

    if data := try_parse_message(message):
        write(
            Point("door")
            .tag(KEY_LOCATION, location.upper())
            .tag(KEY_SIMULATED, _is_simulated(data))
            .field("state", data["state"]) # open/closed
        )

@mqtt.on_topic("home/+/motion")
def on_motion_message(client: Client, userdata: object, message: Message):
    location = message.topic.split('/')[1]

    if data := try_parse_message(message):
        write(
            Point("motion")
            .tag(KEY_LOCATION, location)
            .tag(KEY_SIMULATED, _is_simulated(data))
            .field("detected", data["detected"]) # true/false
        )

@mqtt.on_topic("home/+/proximity")
def on_proximity_message(client: Client, userdata: object, message: Message):
    location = message.topic.split('/')[1]

    if data := try_parse_message(message):
        write(
            Point("proximity")
            .tag(KEY_LOCATION, location)
            .tag(KEY_SIMULATED, _is_simulated(data))
            .field("distance", data["distance"]) # meters (see if it could be like 2m or 20cm)
            .field("in_range", data["in_range"])
        )

@mqtt.on_topic("home/+/typing")
def on_typing_message(client: Client, userdata: object, message: Message):
    location = message.topic.split('/')[1]

    if data := try_parse_message(message):
        write(
            Point("typing")
            .tag(KEY_LOCATION, location)
            .tag(KEY_SIMULATED, _is_simulated(data))
            .field("keys", data["keys"]) # typed keys
        )

@mqtt.on_topic("home/+/temperature")
def on_temperature_message(client: Client, userdata: object, message: Message):
    location = message.topic.split('/')[1]

    if data := try_parse_message(message):
        write(
            Point("temperature")
            .tag(KEY_LOCATION, location)
            .tag(KEY_SIMULATED, _is_simulated(data))
            .field("temperature", data["temperature"])
            .field("humidity", data["humidity"])
        )

@mqtt.on_topic("home/+/remote")
def on_ir_message(client: Client, userdata: object, message: Message):
    location = message.topic.split('/')[1]

    if data := try_parse_message(message):
        write(
            Point("remote")
            .tag(KEY_LOCATION, location)
            .tag(KEY_SIMULATED, _is_simulated(data))
            .field("button", data["button"])
        )

@mqtt.on_topic("home/+/gyro")
def on_gyro_message(client: Client, userdata: object, message: Message):
    location = message.topic.split('/')[1]

    if data := try_parse_message(message):
        write(
            Point("gyro")
            .tag(KEY_LOCATION, location)
            .tag(KEY_SIMULATED, _is_simulated(data))
            .field("accel", accel := cast(dict, data["accel"]))
            .field("gyro", data["gyro"])
            .field("magnitude", magnitude := sum(xi**2 for xi in accel.values())**-2)
            .field("significant_movement", magnitude > 0.5) # g
        )
