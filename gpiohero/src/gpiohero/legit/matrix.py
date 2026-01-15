__all__ = 'MatrixKeypad',

from gpiozero import CompositeDevice, InputDevice, OutputDevice
from gpiozero.mixins import event
from gpiozero.threads import GPIOThread

import time
from queue import Queue
from typing import Sequence, Union, Optional, Callable


class MatrixKeypad(CompositeDevice):
    
    def __init__(self,
        rows: Sequence[Union[int, str]],
        cols: Sequence[Union[int, str]],
        labels: Optional[Sequence[Sequence[object]]] = None,
        scan_interval = .2,
        scan_row_interval = .001,
        pull_up=True,
        pin_factory=None
    ):
        self._rows = [
            OutputDevice(
                row, 
                active_high=pull_up,
                initial_value=False,
                pin_factory=pin_factory
            )
            for row in rows
        ]

        self._cols = [
            InputDevice(
                col, 
                pull_up=pull_up,
                pin_factory=pin_factory
            ) 
            for col in cols
        ]

        super(MatrixKeypad, self).__init__(
            *self._rows,
            *self._cols,
            pin_factory=pin_factory,
            # **{f"r{i}": row for i, row in enumerate(self._rows)}, 
            # **{f"c{i}": col for i, col in enumerate(self._cols)}
        )

        self.labels = labels or tuple( tuple(f"({i}, {j})" for j in cols) for i in rows )

        self.scan_interval = scan_interval
        self.scan_row_interval = scan_row_interval
        self._scan_thread = GPIOThread(self._scan_matrix)
        self._scan_thread.start()
        self.when_key: Optional[Callable[[object,], None]] = None

    # when_key = event()
    
    def _scan_matrix(self):
        while not self._scan_thread.stopping.wait(self.scan_interval):    
            for i, out in enumerate(self._rows):
                out.on()
                if self.scan_row_interval > 0:
                    time.sleep(self.scan_row_interval)

                for j, in_ in enumerate(self._cols):
                    if in_.is_active and self.when_key:
                        key = self.labels[i][j]
                        self.when_key(key) 

                if not self._scan_thread.stopping.is_set():
                    out.off()

    def close(self):
        if getattr(self, '_scan_thread', None):
            self._scan_thread.stop()
        
        super().close()



if __name__ == "__main__":
    from gpiozero.pins.mock import MockFactory, MockPin
    
    keypad = MatrixKeypad(
        rows="1234", 
        cols="5678", 
        labels=
        [
            "123", 
            "456", 
            "789", 
            "*0#"
        ], 
        pin_factory=MockFactory(),
        scan_interval=2,
        scan_row_interval=.001
    )
    # print(list(keypad))
    keypad.when_key = print
    keypad._cols[0].pin.drive_high() # type: ignore # permanently hold all switches in one column
    time.sleep(4)




















# class MatrixKey(Button): # NOTE: Nice idea, but will create a thread explosion. Probably a thread per key (4x4 keypad, 16 threads)
    
#     def __init__(self, pin=None, trigger: Optional[LED] = None, *, label: str = '', pull_up=True, active_state=None, bounce_time=None, hold_time=1, hold_repeat=False, pin_factory=None):
#         super().__init__(pin, pull_up=pull_up, active_state=active_state, bounce_time=bounce_time, hold_time=hold_time, hold_repeat=hold_repeat, pin_factory=pin_factory)

#         self._trigger = trigger
#         self.label = label

#     @property
#     def value(self):
#         return int(super().value and (self._trigger.value if self._trigger else True))

#     def _conflicts_with(self, other): # type: ignore[override]        
#         return (
#             not isinstance(other, MatrixKey) or
#             self._trigger._conflicts_with(other._trigger) if self._trigger and other._trigger else False
#         )
     

# class MatrixKeypad(HoldMixin, CompositeDevice):

#     def __init__(self,
#         rows: Sequence[Union[int, str]],
#         cols: Sequence[Union[int, str]],
#         labels: Optional[Sequence[Sequence[str]]] = None,
#         pin_factory=None
#     ):
#         self._rows = LEDBoard()
#         self._keys = [
#             MatrixKey(col, row, label=..., pin_factory=pin_factory) # : add other kwargs
#             for row in self._rows.leds
#             for col in cols
#         ]

#         super(MatrixKeypad, self).__init__(**{key.label: key for key in self._keys})






# from gpiozero.threads import GPIOThread

# from gpiozero.pins.mock import MockFactory

# Device.pin_factory = MockFactory()

# class MatrixKeypadOld(HoldMixin, CompositeDevice):

#     def __init__(self, rows, cols, labels=None, scan_delay=.02, pull_up=True, bounce_time=None, pin_factory=None) -> None:

#         self.rows = LEDBoard(
#             **{f"r{i}": row for i, row in enumerate(rows)}, 
#             pin_factory=pin_factory,
#             active_high=not pull_up
#         )
        
#         self.cols = ButtonBoard(
#             **{f"c{i}": col for i, col in enumerate(cols)}, 
#             pin_factory=pin_factory,
#             bounce_time=bounce_time,
#             pull_up=pull_up
#         )

#         for col in enumerate(self.cols.all):
#             ...

#         # self._scan_lock = threading.Lock()
        
#         #     row           columns
#         # (0, 0, 1, 0), (0, 1, 1, 0, 0)
#         super(MatrixKeypadOld, self).__init__(row=self.rows, col=self.cols, _order=['row', 'col'])

#     @property
#     def is_active(self):
#         return any(self.cols)

    

# # keypad = MatrixKeypadOld([1, 2, 3], [5, 6, 7], pull_up=False)
# # keypad.rows.on(0)
# # print(keypad, keypad.rows, keypad.cols, keypad.rows.r1, keypad.cols.c1)
# # print(keypad.value)



# # class MatrixKeypad(ButtonBoard):

# #     def __init__(self, rows, cols, labels=None, scan_delay=.1, scan_step_delay=.001, pull_up=True, active_state=None, bounce_time=None, hold_time=1, hold_repeat=False, pin_factory=None):
# #         super(MatrixKeypad, self).__init__(
# #             pull_up=pull_up, 
# #             active_state=active_state, 
# #             bounce_time=bounce_time, 
# #             hold_time=hold_time, 
# #             hold_repeat=hold_repeat, 
# #             pin_factory=pin_factory, 
# #             **{f"c{i}": col for i, col in enumerate(cols)}
# #         )

# #         self._rows = LEDBoard(
# #             **{f"r{i}": row for i, row in enumerate(rows)}, 
# #             pin_factory=pin_factory,
# #             active_high=pull_up,
# #             initial_value=False
# #         )

# #         self.labels = labels or tuple( tuple(range(len(cols))) for _ in rows )

# #         self.when_key = None # simplest way couldn't implement any other
# #         self._current_row = None
# #         self.scan_delay = scan_delay
# #         self.scan_step_delay = scan_step_delay
# #         # self._current_row = None
# #         self._scan_thread = GPIOThread(self._scan_keypad)
# #         self._scan_thread.start()

# #     def _fire_changed(self):
# #         return super()._fire_changed()

# #     def _scan_keypad(self):
# #         while not self._scan_thread.stopping.wait(self.scan_delay):
# #             for i, row in enumerate(self._rows):
# #                 row.on()                    

# #                 if not self._scan_thread.stopping.wait(self.scan_step_delay):
# #                     row.off()
# #                 #else: don't call off(), stopping anyway (cleanup will happen, but calling it may cause exception  
    
# #     def close(self):
# #         if getattr(self, "_scan_thread", None):
# #             self._scan_thread.stop()

# #         if getattr(self, '_rows', None):
# #             self._rows.close()

# #         super().close()


# class MatrixKeypad(CompositeDevice):

#     def __init__(self, rows, cols, labels=None, scan_delay=.1, scan_step_delay=.001, pull_up=True, active_state=None, bounce_time=None, hold_time=1, hold_repeat=False, pin_factory=None):
        
#         self.rows = LEDBoard(
#             **{f"r{i}": row for i, row in enumerate(rows)}, 
#             pin_factory=pin_factory,
#             active_high=pull_up,
#             initial_value=False
#         )

#         self.cols = ButtonBoard(
#             **{f"c{i}": col for i, col in enumerate(cols)}, 
#             pull_up=pull_up,
#             active_state=active_state,
#             bounce_time=bounce_time,
#             hold_time=hold_time,
#             hold_repeat=hold_repeat,
#         )

#         self.labels = labels or tuple( tuple(range(len(cols))) for _ in rows )

#         # kinda hack, not that great :(
#         self.when_key = None
#         self.key_changed = False # TODO: Cannot use this, skips all rows but 1st

#         ...

#         self.scan_delay = scan_delay
#         self.scan_step_delay = scan_step_delay
#         self._scan_thread = GPIOThread(self._scan_keypad)
#         self._scan_thread.start()

#         super().__init__(row=self.rows, col=self.cols)

#     def _scan_keypad(self):
#         while not self._scan_thread.stopping.wait(self.scan_delay):
#             for i, row in enumerate(self.rows):
#                 row.on()                    
#                 for j, col in enumerate(self.cols):
#                     if col.is_pressed and self.key_changed and self.when_key:
#                         key_ = self.labels[i][j]
#                         self.when_key(key_) 
#                         self.key_changed = False

#                 if not self._scan_thread.stopping.wait(self.scan_step_delay):
#                     row.off()
#                 #else: don't call off(), stopping anyway (cleanup will happen, but calling it may cause exception  

#     def close(self):
#         if getattr(self, "_scan_thread", None):
#             self._scan_thread.stop()

#         super().close()


# k = MatrixKeypad([4, 5], [1], [['a'], ['b']])
# k.cols.c0.pin.drive_low()
# k.when_key = lambda key_: print(key_)

# key_ = None
# import time
# while key_ is None:
#     time.sleep(.2)

# print(k, k.value)
