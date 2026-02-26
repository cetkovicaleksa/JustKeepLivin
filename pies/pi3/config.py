import os
import json
from dataclasses import dataclass, field
from typing import Sequence
import gpiohero.sim as sim
import gpiohero.legit as legit


@dataclass
class DeviceConfig:
    # name: str
    pin: str
    simulated: bool = False

@dataclass
class RGBLEDConfig:
    # name: str
    red: str
    green: str
    blue: str
    simulated: bool = False

class LCDConfig:
    # name: str
    pin_rs: str = 25
    pin_e: str = 24
    pins_db: Sequence[str] = (23, 17, 21, 22)
    simulated: bool = False

@dataclass
class MqttConfig:
    host: str = field(default_factory=lambda: os.getenv('MQTT_HOST', "localhost"))
    port: int = field(default_factory=lambda: os.getenv('MQTT_PORT', 1883))

@dataclass
class Pi3Config:
    name: str
    dht1: DeviceConfig
    """Bedroom DHT"""
    dht2: DeviceConfig
    """Master Bedroom DHT"""
    ir: DeviceConfig
    brgb: RGBLEDConfig
    lcd: LCDConfig
    dpir3: DeviceConfig
    simulated: bool = False
    mqtt: MqttConfig = field(default_factory=MqttConfig)

def load_config(path = None):
    path = path or os.getenv("PI2_CONFIG", "config.json")

    with open(path) as f:
        data = json.load(f)

    return Pi3Config(
        name=data["name"],
        simulated=data["simulated"],
        dht1=DeviceConfig(**data["dht1"]),
        dht2=DeviceConfig(**data["dht2"]),
        ir=DeviceConfig(**data["ir"]),
        brgb=RGBLEDConfig(**data["brgb"]),
        lcd=LCDConfig(**data["lcd"]),
        dpir3=DeviceConfig(**data["dpir3"]),
    )

def BedroomDHT(config: Pi3Config, *args, **kwargs):
    clazz = sim.DHT11 if config.simulated or config.dht1.simulated else legit.DHT11
    return clazz(config.dht1.pin, *args, **kwargs)

def MasterBedroomDHT(config: Pi3Config, *args, **kwargs):
    clazz = sim.DHT11 if config.simulated or config.dht2.simulated else legit.DHT11
    return clazz(config.dht2.pin, *args, **kwargs)

def BedroomInfrared(config: Pi3Config, *args, **kwargs):
    clazz = sim.IrReceiver if config.simulated or config.ir.simulated else legit.IrReceiver
    return clazz(config.ir.pin, *args, **kwargs)

def BedroomRGB(config: Pi3Config, *args, **kwargs):
    clazz = sim.RGBLED if config.simulated or config.brgb.simulated else legit.RGBLED
    return clazz(config.brgb.red, config.brgb.green, config.brgb.blue, pwm=False, initial_value=(0, 0, 0), *args, **kwargs)

def LivingRoomDisplay(config: Pi3Config, *args, **kwargs):
    if config.simulated or config.lcd.simulated:
        from gpiohero.sim.lcd import Display as _clazz
    else:
        from gpiohero.legit.lcd import Display as _clazz

    lcd = config.lcd
    return _clazz(lcd.pin_rs, lcd.pin_e, lcd.pins_db, *args, **kwargs)

def LivingRoomMotionSensor(config: Pi3Config, *args, **kwargs):
    clazz = sim.MotionSensor if config.simulated or config.ir.simulated else legit.MotionSensor
    return clazz(config.dpir3.pin, *args, **kwargs)
