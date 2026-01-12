import time
import random
import logging
import threading
from functools import wraps

from gpiozero.pins.mock import MockFactory
from gpiozero import (
    LED as _ZeroLED, Buzzer as _ZeroBuzzer, RGBLED as _ZeroRGBLED,
    Button as _ZeroButton, MotionSensor as _ZeroMotionSensor, DistanceSensor as _ZeroDistanceSensor
)

_mock_factory = MockFactory()

# TODO: Simulate devices, not just mock

# region Sensors

class Button(_ZeroButton):

    def __init__(self, pin=None, *, pull_up=True, active_state=None, bounce_time=None, hold_time=1, hold_repeat=False, pin_factory=None):
        super().__init__(pin, pull_up=pull_up, active_state=active_state, bounce_time=bounce_time, hold_time=hold_time, hold_repeat=hold_repeat, pin_factory=_mock_factory)

        self._logger = logging.getLogger(f"{self.__class__.__name__}@{self.pin}")

        self._stop_simulation = threading.Event()
        threading.Thread(target=self._simulator, daemon=True).start()

    def _fire_activated(self):
        self._logger.debug("Pressed")
        return super()._fire_activated()
    
    def _fire_deactivated(self):
        self._logger.debug("Released", extra={'held_for': f'{self.held_time}s'})
        return super()._fire_deactivated()
    
    def _simulator(self):
        self._logger.debug("Starting simulation")
        pin = self.pin 

        while not self._stop_simulation.wait(delay := random.uniform(5, 20)): # 5 - 20s between button presses
            pin.drive_low() # type: ignore

            hold_for = random.uniform(.5, max(5, self.hold_time + .5)) # hold for .5 - 5 (or more if hold time is longer)
            time.sleep(hold_for)
            
            pin.drive_high() # type: ignore

# TODO: Add pir and ultrasonic sensor simulators

@wraps(_ZeroMotionSensor)
def MotionSensor(*args, **kwargs):
    return _ZeroMotionSensor(*args, **kwargs, pin_factory=_mock_factory)

@wraps(_ZeroDistanceSensor)
def DistanceSensor(*args, **kwargs):
    return _ZeroDistanceSensor(*args, **kwargs, pin_factory=_mock_factory)

# endregion

# region Actuators

class LED(_ZeroLED):

    def __init__(self, pin=None, *, active_high=True, initial_value=False, pin_factory=None):
        super().__init__(pin, active_high=active_high, initial_value=initial_value, pin_factory=_mock_factory)

        self._logger = logging.getLogger(f"{self.__class__.__name__}@{self.pin}")

    def _write(self, value):
        old_state = self.pin.state # type: ignore
        super()._write(value)

        if old_state != self._value_to_state(value):
            self._logger.info("[%s]", {True: 'ON', False: 'OFF'}[self.is_active])

class Buzzer(_ZeroBuzzer):

    def __init__(self, pin=None, *, active_high=True, initial_value=False, pin_factory=None):
        super().__init__(pin, active_high=active_high, initial_value=initial_value, pin_factory=_mock_factory)

        self._logger = logging.getLogger(f"{self.__class__.__name__}@{self.pin}")

    def _write(self, value):
        old_state = self.pin.state # type: ignore
        super()._write(value)

        if old_state != self._value_to_state(value):
            self._logger.info("[%s]", {True: 'ON', False: 'OFF'}[self.is_active])

class RGBLED(_ZeroRGBLED):

    def __init__(self, red=None, green=None, blue=None, *, active_high=True, initial_value=..., pwm=True, pin_factory=None):
        super().__init__(red, green, blue, active_high=active_high, initial_value=initial_value, pwm=pwm, pin_factory=_mock_factory)

        pins = zip(['red', 'green', 'blue'], map(lambda l: l.pin, self._leds))
        pins = tuple(map(lambda pin: f"{pin[0]}: {pin[1]}", pins))
        
        self._logger = logging.getLogger(f"{self.__class__.__name__}@{pins}")

    @property
    def value(self):
        return super().value
    
    @value.setter
    def value(self, value):
        if self.value != value:
            self._logger.info("[%s]", self.color)

        super().value = value

# endregion
