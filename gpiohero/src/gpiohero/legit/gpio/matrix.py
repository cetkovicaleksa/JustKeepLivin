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
        assert labels is None or len(labels) == len(rows) and all(len(row) == len(cols) for row in labels)
      
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
                if self.scan_row_interval > 0 and self._scan_thread.stopping.wait(self.scan_row_interval):
                    break

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
        cols="567", 
        labels=
        [
            "123", 
            "456", 
            "789", 
            "*0#"
        ], 
        pin_factory=MockFactory(),
        scan_interval=2,
        scan_row_interval=.001,
        pull_up=False
    )
    # print(list(keypad))
    keypad.when_key = print
    col = keypad._cols[0]
    (col.pin.drive_high if not col.pull_up else col.pin.drive_low)() # type: ignore # permanently hold all switches in one column
    time.sleep(4)
