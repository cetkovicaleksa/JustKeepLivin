from functools import partial
import os
import json
from dataclasses import dataclass, field
from gpiohero import sim, legit


@dataclass
class DeviceConfig:
    # name: str
    pin: str
    simulated: bool = False

@dataclass
class UltrasonicConfig:
    # name: str
    trig: str
    echo: str
    simulated: bool = False

@dataclass
class TimerConfig:
    segments: tuple[str, str, str, str, str, str, str]
    digits: tuple[str, str, str, str]
    btn: str
    simulated: bool = False

@dataclass
class GyroConfig:
    bus: int = 1
    address: int = 104
    sample_interval: float = 2
    simulated: bool = False

@dataclass
class MqttConfig:
    host: str = field(default_factory=lambda: os.getenv('MQTT_HOST', "localhost"))
    port: int = field(default_factory=lambda: os.getenv('MQTT_PORT', 1883))

@dataclass
class Pi2Config:
    name: str
    ds2: DeviceConfig
    dus2: UltrasonicConfig
    dpir2: DeviceConfig
    timer: TimerConfig
    dht3: DeviceConfig
    gsg: GyroConfig
    simulated: bool = False
    mqtt: MqttConfig = field(default_factory=MqttConfig)

def load_config(path = None):
    path = path or os.getenv("PI1_CONFIG", "config.json")

    with open(path) as f:
        data = json.load(f)

    return Pi2Config(
        name=data["name"],
        simulated=data["simulated"],
        ds2=DeviceConfig(**data["ds2"]),
        dus2=UltrasonicConfig(**data["dus2"]),
        dpir2=DeviceConfig(**data["dpir2"]),
        timer=TimerConfig(**data["timer"]),
        dht3=DeviceConfig(**data["dht3"]),
        gsg=GyroConfig(**data["gsg"]),
    )

def DoorSensor(config: Pi2Config, *args, **kwargs):
    clazz = sim.Button if config.simulated or config.ds1.simulated else legit.Button
    return clazz(config.ds2.pin, *args, **kwargs)

def DoorUltrasonicSensor(config: Pi2Config, *args, **kwargs):
    clazz = sim.DistanceSensor if config.simulated or config.dus1.simulated else legit.DistanceSensor
    return clazz(config.dus2.trig, config.dus2.echo, *args, **kwargs)

def DoorMotionSensor(config: Pi2Config, *args, **kwargs):
    clazz = sim.MotionSensor if config.simulated or config.dpir1.simulated else legit.MotionSensor
    return clazz(config.dpir2.pin, *args, **kwargs)

def KitchenDisplayTimer(config: Pi2Config, *args, **kwargs): # could have made a gpiozero composite device :(
    if config.simulated or config.timer.simulated:
        from gpiohero.sim.timer import Timer as _clazz
    else:
        from gpiohero.legit.timer import Timer as _clazz

    return _clazz(config.timer.segments, config.timer.digits, *args, **kwargs)

def KitchenButton(config: Pi2Config, *args, **kwargs):
    clazz = sim.Button if config.simulated or config.timer.simulated else legit.Button
    return clazz(config.timer.btn, *args, **kwargs)

def KitchenDHT(config: Pi2Config, *args, **kwargs):
    clazz = sim.DHT11 if config.simulated or config.dht3.simulated else legit.DHT11
    return clazz(config.dht3.pin, *args, **kwargs)

def Gyroscope(config: Pi2Config, *args, **kwargs):
    if config.simulated or config.gsg.simulated:
        from gpiohero.sim.imu import MPU as _clazz
    else:
        from gpiohero.legit.imu import MPU as _clazz

    _clazz.SIM_MOVEMENT_SCALE = 0.01
    _clazz.SIM_FREQ = 0.06
    _clazz.SIM_GYRO_SCALE = 5
    return _clazz(config.gsg.bus, config.gsg.address, config.gsg.sample_interval, *args, **kwargs)
