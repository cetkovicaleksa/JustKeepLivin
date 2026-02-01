from flask import Flask
from flask_mqtt import Mqtt
from collections.abc import Iterable
from itertools import repeat, chain
from threading import Lock

mqtt = Mqtt()
init_app = mqtt.init_app

_topics = set()
_topic_lock = Lock()

def add_topics(*topics: str, qos: int | Iterable[int] = 0):
    with _topic_lock:
        for topic, qos_ in zip(topics, repeat(qos) if isinstance(qos, int) else chain(qos, repeat(0))):
            _topics.add((topic, qos_))
            mqtt.subscribe(topic, qos_) # fails without throwing if not connected

@mqtt.on_connect()
def handle_connect(client: Mqtt, userdata, flags, rc):
    with _topic_lock:
        for topic, qos in _topics:
            client.subscribe(topic, qos)

@mqtt.on_disconnect()
def handle_disconnect(*args, **kwargs):
    pass
