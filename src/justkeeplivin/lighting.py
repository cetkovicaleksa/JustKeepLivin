import json

from .x.mqtt import mqtt, try_parse_message, Message, Client


topics = [
    ("home/+/motion", 0),
]

def init_app(app):
    mqtt.subscribe(topics)

@mqtt.on_topic("home/+/motion")
def on_motion_switch_light_on(client: Client, userdata: object, message: Message):
    location = message.topic.split('/')[1]

    if (data := try_parse_message(message)) and data.get("detected"):
        mqtt.publish(
            f"cmd/home/{location}/light",
            json.dumps({
                "action": "on",
                "for": 10
            })
        )

@mqtt.on_topic("home/master_bedroom/remote")
def on_brgb_remote_message(client: Client, userdata: object, message: Message):
    if data := try_parse_message(message):
        match button := data.get("button"):
            case _:
                # TODO: send commands to "cmd/home/master_bedroom/brgb"
                ...
