import logging
import random
from functools import wraps
from gpiozero import (
    Button as _ZeroButton,
    DistanceSensor as _ZeroDistanceSensor,
    MotionSensor as _ZeroMotionSensor,

)
from gpiozero.threads import GPIOThread
from gpiozero.pins.mock import MockFactory as _MockFactory

_mock_factory = _MockFactory()



class Button(_ZeroButton):
    SIM_PRESS_TIME_RANGE = 2, 10
    SIM_HOLD_DURATION_RANGE = .5, 2
    SIM_MSG_PRESSED = "Pressed"
    SIM_MSG_RELEASED = "Released"

    def __init__(self, pin=None, *, pull_up=True, active_state=None, bounce_time=None, hold_time=1, hold_repeat=False, pin_factory=None):
        super().__init__(pin, pull_up=pull_up, active_state=active_state, bounce_time=bounce_time, hold_time=hold_time, hold_repeat=hold_repeat, pin_factory=_mock_factory)

        self._logger = logging.getLogger(f"{self.__class__.__name__}@{self.pin}")

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

        while not self._simulation_thread.stopping.wait(delay := random.uniform(*self.SIM_PRESS_TIME_RANGE)):
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


if __name__ == "__main__":
    import time
    logging.basicConfig(level=logging.DEBUG)

    button = Button(1, pull_up=True)
    time.sleep(15)
