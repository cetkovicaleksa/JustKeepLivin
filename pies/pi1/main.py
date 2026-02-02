import time
import json
import signal
import logging
from queue import Queue, Empty as QueueEmpty
import paho.mqtt.client as mqtt
from dataclasses import dataclass
from threading import Event, Thread, Lock
from typing import TypeVar
from paho.mqtt.enums import CallbackAPIVersion, MQTTProtocolVersion
from config import (
    load_config, Pi1Config, DoorLight, DoorBuzzer,
    DoorSensor, DoorMembraneSwitch, DoorMotionSensor, DoorUltrasonicSensor
)


shutdown_event = Event()
data_thread: Thread | None = None

config = load_config()
client = mqtt.Client(
    client_id=config.name,
    protocol=MQTTProtocolVersion.MQTTv5
)
client.on_connect = lambda client, userdata, flags, rc, prop: client.subscribe("cmd/home/porch/+")


def shutdown():
    shutdown_event.set()

    if data_thread:
        data_thread.join(timeout=3)

        if data_thread.is_alive():
            logging.warning("Failed to join data thread, timeout reached.")

    client.loop_stop()
    client.disconnect()

signal.signal(signal.SIGINT | signal.SIGTERM, lambda signum, frame: shutdown())

# (topic, message)
data_queue = Queue()
BATCH_SIZE = 5

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
            msg.wait_for_publish(timeout=.5)
        except QueueEmpty:
            break
        except (ValueError, RuntimeError):
            # not queued, queue full or other reason
            continue


def main():
    import warnings
    warnings.filterwarnings('ignore') # ignore gpiozero, use pigpio and no echo detected for simulators warnings
    logging.basicConfig(level=logging.DEBUG)

    with (
        DoorSensor(config) as ds1,
        DoorUltrasonicSensor(config) as dus1,
        DoorMotionSensor(config) as dpir1,
        DoorMembraneSwitch(config) as dms,
        DoorBuzzer(config) as db,
        DoorLight(config) as dl,
    ):
        ds1.when_pressed = ds1.when_released = door_sensor_changed
        dus1.when_in_range = dus1.when_out_of_range = door_ultrasonic_sensor_changed
        dpir1.when_motion = dpir1.when_no_motion = door_motion_sensor_changed
        dms.when_key = door_switch_key_pressed

        global data_thread
        data_thread = Thread(target=collect_data, args=(client, shutdown_event)).start()

        Thread(target=key_buffer_thread, args=(shutdown_event,), daemon=True).start()

        def on_message(client: mqtt.Client, userdata, message: mqtt.MQTTMessage):
            match message.topic:
                case "cmd/home/porch/light":
                    device = dl
                case "cmd/home/porch/buzzer":
                    device = db
                case _:
                    ...
                    return

            try:
                data = json.loads(message.payload.decode('utf-8'))
            except json.JSONDecodeError:
                ...
            else:
                on = data.get("state", False)
                device.on() if on else device.off()

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
        "home/porch/door",
        json.dumps({
            "state": "closed" if button.is_pressed else "opened",
            "simulated": config.simulated or config.ds1.simulated,
        })
    ))

def door_motion_sensor_changed(pir):
    data_queue.put((
        "home/porch/motion",
        json.dumps({
            "detected": pir.motion_detected,
            "simulated": config.simulated or config.dpir1.simulated,
        })
    ))

key_buffer = []
key_buffer_lock = Lock()
last_pressed: float = None

def door_switch_key_pressed(key):
    global last_pressed, key_buffer, key_buffer_lock

    with key_buffer_lock:
        key_buffer.append(key)
        last_pressed = time.time()

def key_buffer_thread(stop: Event):
    global last_pressed

    while not stop.wait(.3):
        if stop.is_set():
            break

        with key_buffer_lock:
            if key_buffer and last_pressed is not None and time.time() - last_pressed > 2: # seconds
                data_queue.put((
                    "home/porch/typing",
                    json.dumps({
                        "keys": ''.join(key_buffer),
                        "simulated": config.simulated or config.dms.simulated,
                    })
                ))

                key_buffer.clear()
                last_pressed = None


def door_ultrasonic_sensor_changed(us):
    data_queue.put((
        "home/porch/proximity",
        json.dumps({
            "distance": us.distance,
            "in_range": us.in_range,
            "simulated": config.simulated or config.dus1.simulated,
        })
    ))

if __name__ == "__main__":
    main()
