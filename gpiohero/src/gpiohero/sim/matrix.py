__all__ = [
    "MatrixKeypad",
]

from gpiozero.pins.mock import MockFactory
from gpiohero.legit import MatrixKeypad as _HeroMatrixKeypad

import logging
import random
from itertools import cycle, chain
from typing import Sequence, Union, Optional, Iterable


_mock_factory = MockFactory()



class MatrixKeypad(_HeroMatrixKeypad):
    SIM_TYPE_DELAY: float = .7
    SIM_PAUSE_DELAY: float = 20
    SIM_INITIAL_DELAY: float = 2
    SIM_KEYS: Optional[Iterable[Union[str, None]]] = None


    def __init__(self,
        rows: Sequence[Union[int, str]],
        cols: Sequence[Union[int, str]],
        labels: Optional[Sequence[Sequence[object]]] = None,
        scan_interval = .2,
        scan_row_interval = .001,
        pull_up=True,
        pin_factory=None
    ):
        self._logger = logging.getLogger(self.__class__.__name__)

        super().__init__(rows, cols, labels, scan_interval, scan_row_interval, pull_up, _mock_factory)


    def _scan_matrix(self):
        self._simulator()


    def _simulator(self):
        self._logger.debug("Starting simulation")

        if self.SIM_KEYS:
            keys = self.SIM_KEYS
        else:
            labels = list(chain(*self.labels))

            def cycle_labels():
                while True:
                    random.shuffle(labels)
                    for label in labels:
                        yield label if random.random() > .2 else None

            keys = cycle_labels()

        if self._scan_thread.stopping.wait(self.SIM_INITIAL_DELAY):
            keys = []

        for key_ in keys:
            if key_ is None:
                if self._scan_thread.stopping.wait(self.SIM_PAUSE_DELAY):
                    break
                continue

            self._logger.debug("Key pressed: '%s'", key_)
            if getattr(self, 'when_key', None):
                self.when_key(key_) # type: ignore

            if self._scan_thread.stopping.wait(self.SIM_TYPE_DELAY):
                break

        self._logger.debug("Simulation stopped")


def main():
    import time
    logging.basicConfig(level=logging.INFO)

    class Interfon(MatrixKeypad):
        SIM_TYPE_DELAY = 3
        SIM_KEYS = chain("1402", [None], "003", [None], "aki")

    with Interfon(
        rows="1234",
        cols="567",
        labels=
            [
                "123",
                "456",
                "789",
                "*0#"
            ]) as keypad:

        keypad.when_key = print
        time.sleep(15)

if __name__ == '__main__':
    main()
