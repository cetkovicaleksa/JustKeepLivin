from collections import defaultdict
from typing import Iterable
from gpiohero.common import ContdownTimer
from gpiozero.threads import GPIOThread

# TODO: Add 4dig7seg display

class Timer(ContdownTimer):

    digit_map = defaultdict(lambda: (0,0,0,0,0,0,0), {
        '0':(1,1,1,1,1,1,0),
        '1':(0,1,1,0,0,0,0),
        '2':(1,1,0,1,1,0,1),
        '3':(1,1,1,1,0,0,1),
        '4':(0,1,1,0,0,1,1),
        '5':(1,0,1,1,0,1,1),
        '6':(1,0,1,1,1,1,1),
        '7':(1,1,1,0,0,0,0),
        '8':(1,1,1,1,1,1,1),
        '9':(1,1,1,1,0,1,1)
    })

    def __init__(self, segments: Iterable[int], digits: Iterable[int], duration = 10, tick = 1):
        super().__init__(duration, tick)

        self._display_thread = GPIOThread(self._display)
        self._display_thread.start()

    def _display(self):
        while not self._display_thread.stopping.is_set():
            with self._lock:
                remaining: int = self._remaining
                expired, dismissed = self.expired, self._dismissed

            if not expired:
                # show remaining
                ...
            else:
                # blink some time
                ...
