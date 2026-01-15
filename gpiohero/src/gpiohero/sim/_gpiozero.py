__all__ = [ 
    'Button', 
    'MotionSensor', 
    'DistanceSensor',
# ---
    'LED', 
    'RGBLED', 
    'Buzzer', 
]

import time
import random
import logging
from functools import wraps

from gpiozero.pins.mock import MockFactory
from gpiozero.threads import GPIOThread
from gpiozero import (
    LED as _ZeroLED, Buzzer as _ZeroBuzzer, RGBLED as _ZeroRGBLED,
    Button as _ZeroButton, MotionSensor as _ZeroMotionSensor, DistanceSensor as _ZeroDistanceSensor
)

_mock_factory = MockFactory()

# region Sensors

class Button(_ZeroButton):
    SIM_PRESS_TIME_RANGE = 2, 10
    SIM_HOLD_DURATION_RANGE = .5, 2

    def __init__(self, pin=None, *, pull_up=True, active_state=None, bounce_time=None, hold_time=1, hold_repeat=False, pin_factory=None):
        super().__init__(pin, pull_up=pull_up, active_state=active_state, bounce_time=bounce_time, hold_time=hold_time, hold_repeat=hold_repeat, pin_factory=_mock_factory)

        self._logger = logging.getLogger(f"{self.__class__.__name__}@{self.pin}")

        self._simulation_thread = GPIOThread(self._simulator)
        self._simulation_thread.start()

    def _fire_activated(self):
        self._logger.debug("Pressed")
        return super()._fire_activated()
    
    def _fire_deactivated(self):
        self._logger.debug("Released", extra={'held_for': f'{self.held_time}s'})
        return super()._fire_deactivated()
    
    def _simulator(self):
        self._logger.debug("Starting simulation")
        pin = self.pin 
        press, release = (pin.drive_high, pin.drive_low) if self.pull_up else (pin.drive_low, pin.drive_high) # type: ignore

        while not self._simulation_thread.stopping.wait(delay := random.uniform(*self.SIM_PRESS_TIME_RANGE)):
            press()

            hold_for = random.uniform(*self.SIM_HOLD_DURATION_RANGE)
            time.sleep(hold_for)
            
            release()
        
        self._logger.debug("Simulation stopped")

    def close(self):
        if getattr(self, '_simulation_thread', None):
            self._simulation_thread.stop()
        
        super().close()

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


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    button = Button(1, pull_up=True)
    time.sleep(15)
