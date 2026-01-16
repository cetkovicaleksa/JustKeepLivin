import logging
from gpiozero import (
    LED as _ZeroLED, 
    Buzzer as _ZeroBuzzer,
    RGBLED as _ZeroRGBLED,
)
from gpiozero.pins.mock import MockFactory as _MockFactory

_mock_factory = _MockFactory()



class LED(_ZeroLED):
    SIM_MSG_ON = '[ON]'
    SIM_MSG_OFF = '[OFF]'

    def __init__(self, pin=None, *, active_high=True, initial_value=False, pin_factory=None):
        super().__init__(pin, active_high=active_high, initial_value=initial_value, pin_factory=_mock_factory)

        self._logger = logging.getLogger(f"{self.__class__.__name__}@{self.pin}")

    def _write(self, value):
        old_state = self.pin.state # type: ignore
        super()._write(value)

        if old_state != self._value_to_state(value):
            self._logger.info({True: self.SIM_MSG_ON, False: self.SIM_MSG_OFF}[self.is_active])


class Buzzer(_ZeroBuzzer):
    SIM_MSG_ON = '[ON]'
    SIM_MSG_OFF = '[OFF]'

    def __init__(self, pin=None, *, active_high=True, initial_value=False, pin_factory=None):
        super().__init__(pin, active_high=active_high, initial_value=initial_value, pin_factory=_mock_factory)

        self._logger = logging.getLogger(f"{self.__class__.__name__}@{self.pin}")

    def _write(self, value):
        old_state = self.pin.state # type: ignore
        super()._write(value)

        if old_state != self._value_to_state(value):
            self._logger.info({True: self.SIM_MSG_ON, False: self.SIM_MSG_OFF}[self.is_active])


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
