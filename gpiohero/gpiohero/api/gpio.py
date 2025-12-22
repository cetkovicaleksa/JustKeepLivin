from typing import Callable
from ._common import DeviceProtocol

#region Actuators

class LED(DeviceProtocol):

    @property
    def is_lit(self) -> bool: ...

    def on(self): ...
    
    def off(self): ...
    
    def toggle(self): ...
    
    def blink(
            self, 
            on_time: float = 1, 
            off_time: float = 1, 
            n: int | None = None, 
            background: bool = True
        ): ...


class Buzzer(DeviceProtocol):

    @property
    def is_active(self) -> bool: ...

    def on(self): ...
    
    def off(self): ...
    
    def toggle(self): ...

    def beep(
            self, 
            on_time: float = 1, 
            off_time: float = 1, 
            n: int | None = None, 
            background: bool = True
        ): ...


class RGBLED(DeviceProtocol):
    value: tuple[float, float, float]
    red: float
    blue: float
    green: float
    
    @property
    def is_lit(self) -> bool: ...

    def on(self): ...
    
    def off(self): ...
    
    def toggle(self): ...
    
    def blink(
            self, 
            on_time: float = 1, 
            off_time: float = 1, 
            fade_in_time: float = 0, 
            fade_out_time: float = 0, 
            on_color: tuple[float, float, float] = (1, 1, 1), 
            off_color: tuple[float, float, float] = (0, 0, 0), 
            n: int | None = None, 
            background: bool = True
        ): ...

    def pulse(
            self, 
            fade_in_time: float = 0, 
            fade_out_time: float = 0, 
            on_color: tuple[float, float, float] = (1, 1, 1), 
            off_color: tuple[float, float, float] = (0, 0, 0), 
            n: int | None = None, 
            background: bool = True
        ): ...

#endregion

#region Sensors


_Callback = Callable[[], None]


class Button(DeviceProtocol):
    when_pressed: _Callback
    when_released: _Callback
    
    @property
    def is_pressed(self) -> bool: ...

    @property
    def is_held(self) -> bool: ...

    @property
    def held_time(self) -> float: ...

    def wait_for_press(self, timeout: float | None = None): ...
    def wait_for_release(self, timeout: float | None = None): ...


class MotionSensor(DeviceProtocol):
    when_motion: _Callback
    when_no_motion: _Callback

    @property
    def motion_detected(self) -> bool: ...

    def wait_for_motion(self, timeout: float | None = None): ...
    def wait_for_no_motion(self, timeout: float | None = None): ...


class DistanceSensor(DeviceProtocol):
    max_distance: float
    threshold_distancd: float
    when_in_range: _Callback
    when_out_of_range: _Callback

    @property
    def distance(self) -> float: ...

    def wait_for_in_range(self, timeout: float | None = None): ...
    def wait_for_out_of_range(self, timeout: float | None = None): ...


#endregion