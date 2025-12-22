from gpiozero import (
    LED as ZeroLED, Buzzer as ZeroBuzzer, RGBLED as ZeroRGBLED,
    Button as ZeroButton, MotionSensor as ZeroMotionSensor, DistanceSensor as ZeroDistanceSensor
)
from functools import wraps
import warnings

try:
    from gpiozero.pins.rpigpio import RPiGPIOFactory as PinFactory
except ImportError:
    warnings.warn(
        "Rpi GPIO not available - legit devices will also be mocked",
        RuntimeWarning,
        stacklevel=3
    )
    from gpiozero.pins.mock import MockFactory as PinFactory

_pin_factory = PinFactory()


@wraps(ZeroLED)
def LED(*args, **kwargs):
    return ZeroLED(*args, **kwargs, pin_factory=_pin_factory)

@wraps(ZeroBuzzer)
def Buzzer(*args, **kwargs):
    return ZeroBuzzer(*args, **kwargs, pin_factory=_pin_factory)

@wraps(ZeroRGBLED)
def RGBLED(*args, **kwargs):
    return ZeroRGBLED(*args, **kwargs, pin_factory=_pin_factory)

@wraps(ZeroButton)
def Button(*args, **kwargs):
    return ZeroButton(*args, **kwargs, pin_factory=_pin_factory)

@wraps(ZeroMotionSensor)
def MotionSensor(*args, **kwargs):
    return ZeroMotionSensor(*args, **kwargs, pin_factory=_pin_factory)

@wraps(ZeroRGBLED)
def DistanceSensor(*args, **kwargs):
    return ZeroDistanceSensor(*args, **kwargs, pin_factory=_pin_factory)
