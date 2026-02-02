from functools import partial
import os
import json
from dataclasses import dataclass, field
from gpiohero import sim, legit


@dataclass
class DeviceConfig:
    name: str
    pin: str
    simulated: bool = False

@dataclass
class UltrasonicConfig:
    name: str
    trig: str
    echo: str
    simulated: bool = False

@dataclass
class KeypadConfig:
    name: str
    rows: list[str]
    cols: list[str]
    labels: list[str] = None
    simulated: bool = False

@dataclass
class MqttConfig:
    host: str = field(default_factory=lambda: os.getenv('MQTT_HOST', "localhost"))
    port: int = field(default_factory=lambda: os.getenv('MQTT_PORT', 1883))

@dataclass
class Pi1Config:
    name: str
    ds1: DeviceConfig
    dl: DeviceConfig
    db: DeviceConfig
    dpir1: DeviceConfig
    dus1: UltrasonicConfig
    dms: KeypadConfig
    simulated: bool = False
    mqtt: MqttConfig = field(default_factory=MqttConfig)

def load_config(path = None):
    path = path or os.getenv("PI1_CONFIG", "config.json")

    with open(path) as f:
        data = json.load(f)

    return Pi1Config(
        name=data["name"],
        simulated=data["simulated"],
        ds1=DeviceConfig(**data["ds1"]),
        dl=DeviceConfig(**data["dl"]),
        db=DeviceConfig(**data["db"]),
        dpir1=DeviceConfig(**data["dpir1"]),
        dus1=UltrasonicConfig(**data["dus1"]),
        dms=KeypadConfig(**data["dms"]),
    )

# NOTE: Simulators (for sensors) can be configured to detect realistic data
# Just extend the device class, and add SIM_* class properties.

def DoorSensor(config: Pi1Config, *args, **kwargs):
    clazz = sim.Button if config.simulated or config.ds1.simulated else legit.Button
    return clazz(config.ds1.pin, *args, **kwargs)

def DoorMotionSensor(config: Pi1Config, *args, **kwargs):
    clazz = sim.MotionSensor if config.simulated or config.dpir1.simulated else legit.MotionSensor
    return clazz(config.dpir1.pin, *args, **kwargs)

def DoorUltrasonicSensor(config: Pi1Config, *args, **kwargs):
    clazz = sim.DistanceSensor if config.simulated or config.dus1.simulated else legit.DistanceSensor
    return clazz(config.dus1.trig, config.dus1.echo, *args, **kwargs)

def DoorMembraneSwitch(config: Pi1Config, *args, **kwargs):
    clazz = sim.MatrixKeypad if config.simulated or config.dms.simulated else legit.MatrixKeypad
    return clazz(config.dms.rows, config.dms.cols, labels=config.dms.labels, *args, **kwargs)

def DoorLight(config: Pi1Config, *args, **kwargs):
    clazz = sim.LED if config.simulated or config.dl.simulated else legit.LED
    return clazz(config.dl.pin, *args, **kwargs)

def DoorBuzzer(config: Pi1Config, *args, **kwargs):
    clazz = sim.Buzzer if config.simulated or config.db.simulated else legit.Buzzer
    return clazz(config.db.pin, *args, **kwargs)


# DoorSensor = type(
#     "DoorSensor",
#     (sim.Button if config.ds1.simulated else legit.Button, ),
#     {}
# )

# DoorUltrasonicSensor = type(
#     "DoorUltrasonicSensor",
#     (sim.DistanceSensor if config.dus1.simulated else legit.DistanceSensor, ),
#     {}
# )

# DoorMotionSensor = type(
#     "DoorMotionSensor",
#     (sim.MotionSensor if config.dpir1.simulated else legit.MotionSensor, ),
#     {}
# )

# DoorMembraneSwitch = type(
#     "DoorMembraneSwitch",
#     (sim.MatrixKeypad if config.dms.simulated else legit.MatrixKeypad, ),
#     {}
# )

# DoorBuzzer = type(
#     "DoorBuzzer",
#     (sim.Buzzer if config.db.simulated else legit.Buzzer, ),
#     {}
# )

# DoorLight = type(
#     "DoorLight",
#     (sim.LED if config.dl.simulated else legit.LED, ),
#     {}
# )

