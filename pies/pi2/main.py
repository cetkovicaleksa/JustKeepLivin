import time
import json
import signal
import logging
from queue import Queue, Empty as QueueEmpty
import paho.mqtt.client as mqtt
from dataclasses import dataclass
from threading import Event, Thread, Lock, Timer
from typing import TypeVar
from paho.mqtt.enums import CallbackAPIVersion, MQTTProtocolVersion
from config import *
from colorzero import Color

shutdown_event = Event()
data_thread: 'Thread | None' = None

config = load_config()
client = mqtt.Client(
    client_id=config.name,
    protocol=MQTTProtocolVersion.MQTTv5
)


def shutdown():
    shutdown_event.set()

    if data_thread:
        data_thread.join(timeout=10)

        if data_thread.is_alive():
            logging.warning("Failed to join data thread, timeout reached.")

    client.loop_stop()
    client.disconnect()

signal.signal(signal.SIGINT | signal.SIGTERM, lambda signum, frame: shutdown())

# (topic, message)
data_queue = Queue()
BATCH_SIZE = 30

def collect_data(client: mqtt.Client, stop: Event):
    batch = []
    outgoing = Queue(50)

    def flush():
        # NOTE: Not sure if we should use publish_multiple here
        for topic, msg in batch:
            outgoing.put( client.publish(topic, msg) )

        batch.clear()

    while not stop.is_set():
        try:
            topic, msg = data_queue.get(timeout=1)
        except QueueEmpty:
            pass
        else:
            batch.append((topic, msg))

            if len(batch) >= BATCH_SIZE:
                flush()

    flush()

    msg: mqtt.MQTTMessageInfo
    while True:
        try:
            msg = outgoing.get_nowait()
            msg.wait_for_publish(timeout=2)
        except QueueEmpty:
            break
        except (ValueError, RuntimeError):
            # not queued, queue full or other reason
            continue

TOPICS = [
    ("cmd/home/kitchen/+", 0),
]

def main():
    import warnings
    warnings.filterwarnings('ignore') # ignore gpiozero, use pigpio and no echo detected for simulators warnings
    logging.basicConfig(level=logging.DEBUG)
    client.on_connect = lambda client, userdata, flags, rc, prop: client.subscribe(TOPICS)

    with DoorSensor(config) as ds2, \
        DoorUltrasonicSensor(config) as dus2, \
        DoorMotionSensor(config) as dpir2, \
        KitchenDisplayTimer(config) as timer, \
        KitchenButton(config) as btn, \
        KitchenDHT(config) as dht3, \
        Gyroscope(config) as gsg:

        ds2.when_pressed = ds2.when_released = door_sensor_changed
        dus2.when_in_range = dus2.when_out_of_range = door_ultrasonic_sensor_changed
        dpir2.when_motion = dpir2.when_no_motion = door_motion_sensor_changed
        dht3.when_measure = dht_measured
        gsg.when_measure = gsg_measured
        btn.when_pressed = kitchen_button_pressed

        # TODO: add callbacks to timer when_expired, ... to send mqtt msg events

        global data_thread
        data_thread = Thread(target=collect_data, args=(client, shutdown_event)).start()

        def on_message(client: mqtt.Client, userdata, message: mqtt.MQTTMessage):
            data = {}
            try:
                data = json.loads(message.payload.decode('utf-8'))
            except json.JSONDecodeError:
                ...
                return

            if "cmd/home/kitchen/timer" == message.topic:
                ... # TODO
            else:
                logging.debug("Unhandled message on topic: %s", message.topic)

        client.on_message = on_message
        client.connect(
            config.mqtt.host,
            config.mqtt.port
        )
        client.loop_start()

        try:
            while True:
                time.sleep(1)
        except: # signal handler was not working :(
            shutdown()

def door_sensor_changed(button):
    data_queue.put((
        "home/garage/door",
        json.dumps({
            "open": not button.is_pressed,
            "simulated": config.simulated or config.ds2.simulated,
        })
    ))

def kitchen_button_pressed():
    data_queue.put((
        "home/kitchen/timer",
        json.dumps({
            "event": "snoozed",
            "simulated": config.simulated or config.ds2.simulated,
        })
    ))

def door_motion_sensor_changed(pir):
    data_queue.put((
        "home/garage/motion",
        json.dumps({
            "detected": pir.motion_detected,
            "simulated": config.simulated or config.dpir2.simulated,
        })
    ))

def door_ultrasonic_sensor_changed(us):
    data_queue.put((
        "home/garage/proximity",
        json.dumps({
            "distance": us.distance,
            "in_range": us.in_range,
            "simulated": config.simulated or config.dus2.simulated,
        })
    ))

def dht_measured(measurement):
    data_queue.put((
        f"home/kitchen/temperature",
        json.dumps(dict(
            **measurement,
            simulated=config.simulated or config.dht3.simulated,
        ))
    ))

def gsg_measured(measurement):
    data_queue.put((
        f"home/икона/gyro",
        json.dumps(dict(
            **measurement,
            simulated=config.simulated or config.gsg.simulated,
        ))
    ))

if __name__ == "__main__":
    main()
