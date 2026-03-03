__all__ = [
    "Button",
    "MotionSensor",
    "DistanceSensor",
    "LED",
    "Buzzer",
    "RGBLED",
]

import logging
import random
from functools import wraps
from gpiozero import (
    Button as _ZeroButton,
    DistanceSensor as _ZeroDistanceSensor,
    MotionSensor as _ZeroMotionSensor,
    LED as _ZeroLED,
    Buzzer as _ZeroBuzzer,
    RGBLED as _ZeroRGBLED,
    LEDCharDisplay as _ZeroLEDCharDisplay,
    LEDMultiCharDisplay as _ZeroLEDMultiCharDisplay,
    Device,
)
from gpiozero.threads import GPIOThread
from gpiozero.pins.mock import MockFactory as _MockFactory

_mock_factory = _MockFactory()

#region Sensors

class Button(_ZeroButton):
    SIM_PRESS_TIME_RANGE: tuple[float, float] = 2, 10
    SIM_HOLD_DURATION_RANGE: tuple[float, float] = .5, 2
    SIM_MSG_PRESSED: str = "Pressed"
    SIM_MSG_RELEASED: str = "Released"

    def __init__(self, pin=None, *, pull_up=True, active_state=None, bounce_time=None, hold_time=1, hold_repeat=False, pin_factory=None):
        self._logger = logging.getLogger(f"{self.__class__.__name__}@{pin}")
        super().__init__(pin, pull_up=pull_up, active_state=active_state, bounce_time=bounce_time, hold_time=hold_time, hold_repeat=hold_repeat, pin_factory=_mock_factory)


        self._simulation_thread = GPIOThread(self._simulator)
        self._simulation_thread.start()

    def _fire_activated(self):
        self._logger.debug(self.SIM_MSG_PRESSED)
        return super()._fire_activated()

    def _fire_deactivated(self):
        self._logger.debug(self.SIM_MSG_RELEASED)
        return super()._fire_deactivated()

    def _simulator(self):
        self._logger.debug("Starting simulation")
        pin = self.pin
        press, release = (pin.drive_high, pin.drive_low) if self.pull_up else (pin.drive_low, pin.drive_high) # type: ignore

        while not self._simulation_thread.stopping.wait(random.uniform(*self.SIM_PRESS_TIME_RANGE)):
            press()

            hold_for = random.uniform(*self.SIM_HOLD_DURATION_RANGE)
            if self._simulation_thread.stopping.wait(hold_for):
                break

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

#endregion

#region Actuators

class LED(_ZeroLED):
    SIM_MSG_ON: str = '[ON]'
    SIM_MSG_OFF: str = '[OFF]'

    def __init__(self, pin=None, *, active_high=True, initial_value=False, pin_factory=None):
        self._logger = logging.getLogger(f"{self.__class__.__name__}@{pin}")
        super().__init__(pin, active_high=active_high, initial_value=initial_value, pin_factory=_mock_factory)


    def _write(self, value):
        old_state = self.pin.state # type: ignore
        super()._write(value)

        if old_state != self._value_to_state(value):
            self._logger.info({True: self.SIM_MSG_ON, False: self.SIM_MSG_OFF}[self.is_active])


class Buzzer(_ZeroBuzzer):
    SIM_MSG_ON: str = '[ON]'
    SIM_MSG_OFF: str = '[OFF]'

    def __init__(self, pin=None, *, active_high=True, initial_value=False, pin_factory=None):
        self._logger = logging.getLogger(f"{self.__class__.__name__}@{pin}")
        super().__init__(pin, active_high=active_high, initial_value=initial_value, pin_factory=_mock_factory)


    def _write(self, value):
        old_state = self.pin.state # type: ignore
        super()._write(value)

        if old_state != self._value_to_state(value):
            self._logger.info({True: self.SIM_MSG_ON, False: self.SIM_MSG_OFF}[self.is_active])


class RGBLED(_ZeroRGBLED):

    def __init__(self, red=None, green=None, blue=None, *, active_high=True, initial_value=..., pwm=True, pin_factory=None):
        self._logger = logging.getLogger(f"{self.__class__.__name__}")

        super().__init__(red, green, blue, active_high=active_high, initial_value=initial_value, pwm=pwm, pin_factory=_mock_factory)

        pins = zip(['red', 'green', 'blue'], map(lambda l: l.pin, self._leds))
        pins = tuple(map(lambda pin: f"{pin[0]}: {pin[1]}", pins))
        self._logger.name = f"{self.__class__.__name__}@{pins}"


    @property
    def value(self):
        return super().value

    @value.setter
    def value(self, value):
        if self.value != value:
            self._logger.info("[%s]", self.color)

        # super().value = value
        _ZeroRGBLED.value.fset(self, value)


@wraps(_ZeroLEDCharDisplay)
def LEDCharDisplay(*pins, dp=None, font=None, pwm=False, active_high=True, initial_value=" ", pin_factory=None):
    return _ZeroLEDCharDisplay(*pins, dp=dp, font=font, pwm=pwm, active_high=active_high, initial_value=initial_value, pin_factory=_mock_factory)

# NOTE: There is a problem when simulating a gpiozero LEDMultiCharDisplay in its __init__ method.
# The plex CompositeOutputDevice is constructed without passing it the given pin_factory, so it always falls back to default pin factory.
# This fails if you want to make a mocked device

# class LedMultiCharDisplay(_ZeroLEDMultiCharDisplay):

#     def __init__(self, char, *pins, active_high=True, initial_value=None, pin_factory=None):
#         self._logger = logging.getLogger(f"{self.__class__.__name__}")

#         super().__init__(char, *pins, active_high=active_high, initial_value=initial_value, pin_factory=_mock_factory)


#     @property
#     def value(self):
#         return super().value

#     @value.setter
#     def value(self, value):
#         _ZeroLEDMultiCharDisplay.value.fset(self, value)
#         self._logger.info("[ %s ]", ''.join(self.value)) # cannot display .

class LEDMultiCharDisplay(Device):

    def __init__(self, char, *pins, active_high=True, initial_value=None, pin_factory=None):
        super().__init__(pin_factory=_mock_factory)

        self._logger = logging.getLogger(f"{self.__class__.__name__}")

    @property
    def value(self):
        return ()

    @value.setter
    def value(self, value):
        self._logger.info("[ %s ]", "".join(value))


#endregion

def main():
    import time
    logging.basicConfig(level=logging.DEBUG)

    with (
        Button(0) as button,
        LEDCharDisplay(1, 2, 3, 4, 5, 6, 7) as c,
        LEDMultiCharDisplay(c, 9, 10, 11, 12) as d
    ):

        def button_changed(btn):
            d.value = "1111" if btn.is_active else "0000"

        button.when_activated = button.when_deactivated = button_changed
        time.sleep(15)

if __name__ == "__main__":
    main()
