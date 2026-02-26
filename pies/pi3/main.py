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
data_thread: Thread | None = None

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
    ("cmd/home/bedroom/+", 0),
    ("cmd/home/living_room/+", 0)
]

def main():
    logging.basicConfig(level=logging.DEBUG)
    client.on_connect = lambda client, userdata, flags, rc, prop: client.subscribe(TOPICS)

    with (
        BedroomDHT(config) as dht1,
        MasterBedroomDHT(config) as dht2,
        BedroomInfrared(config) as ir,
        BedroomRGB(config) as brgb,
        LivingRoomDisplay(config) as lcd,
        LivingRoomMotionSensor(config) as dpir3,
    ):
        dht1.when_measure = lambda measurement: dht_measured(dht1, measurement)
        dht2.when_measure = lambda measurement: dht_measured(dht2, measurement)
        ir.when_message = when_ir_message
        dpir3.when_motion = dpir3.when_no_motion = motion_sensor_changed

        global data_thread
        data_thread = Thread(target=collect_data, args=(client, shutdown_event)).start()

        def on_message(client: mqtt.Client, userdata, message: mqtt.MQTTMessage):
            data = {}
            try:
                data = json.loads(message.payload.decode('utf-8'))
            except json.JSONDecodeError:
                ...
                return

            match message.topic:
                case "cmd/home/living_room/display":
                    match data.get("action"):
                        case "display" | "DISPLAY":
                            message = data.get("message", "")
                            lcd.show(message)
                        case "clear" | "CLEAR":
                            lcd.clear()

                case "cmd/home/bedroom/light":
                    match data.get("action"):
                        case "on" | "ON":
                            colour = data.get("colour", Color.from_rgb(1, 1, 1).html)
                            brgb.color = Color(colour)
                            rollback = brgb.off
                        case "off" | "OFF":
                            colour = brgb.color
                            def rollback():
                                brgb.color = colour

                            brgb.off()
                    try:
                        if for_ := data.get("for"):
                            timer = Timer(float(for_), rollback)
                            timer.start()
                    except:
                        ...
                case topic:
                    logging.debug("Unhandled message on topic: %s", topic)

        def dht_measured(dht, measurement):
            location, dht_conf = \
                ["bedroom", config.dht1] if dht is dht1 \
            else ["master_bedroom", config.dht2]

            data_queue.put((
                f"home/{location}/temperature",
                json.dumps(dict(
                    **measurement,
                    simulated=config.simulated or dht_conf.simulated,
                ))
            ))

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


def when_ir_message(message: sim.IrMessage):
    data_queue.put((
        "home/bedroom/remote",
        json.dumps(dict(
            button=message.name,
            simulated=config.simulated or config.ir.simulated,
        ))
    ))

def motion_sensor_changed(pir):
    data_queue.put((
        "home/living_room/motion",
        json.dumps({
            "detected": pir.motion_detected,
            "simulated": config.simulated or config.dpir3.simulated,
        })
    ))


if __name__ == "__main__":
    main()
