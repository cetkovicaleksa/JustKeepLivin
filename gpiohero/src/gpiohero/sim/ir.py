__all__ = [
    "IrMessage",
    "IrReceiver",
]

from itertools import cycle
from typing import Callable, Iterable

from gpiohero.legit.ir import IrMessage
from gpiozero.threads import GPIOThread

import logging

class IrReceiver:
    SIM_PRESS_DELAY: float = 1
    SIM_PAUSE_DELAY: float = 10
    SIM_INITIAL_DELAY: float = .0001
    SIM_MESSAGES: 'Iterable[IrMessage | None] | None' = None

    def __init__(self, pin: int = 0):
        self.pin = pin
        self.when_message: 'Callable[[IrMessage,], None] | None' = None

        self._logger = logging.getLogger(f"{self.__class__.__name__}@GPIO{self.pin}")
        self._simulator_thread = GPIOThread(self._simulator)
        self._simulator_thread.start()

    def _simulator(self):
        self._logger.debug("Starting simulation")
        messages = self.SIM_MESSAGES or cycle(IrMessage)

        if self._simulator_thread.stopping.wait(self.SIM_INITIAL_DELAY):
            messages = []

        for message in messages:
            if message is None:
                if self._simulator_thread.stopping.wait(self.SIM_PAUSE_DELAY):
                    break
                continue

            self._logger.debug("Received message: %s", message.name)
            if getattr(self, 'when_message', None):
                self.when_message(message)

            if self._simulator_thread.stopping.wait(self.SIM_PRESS_DELAY):
                break

        self._logger.debug("Simulation stopped")

    def close(self):
        if getattr(self, '_simulator_thread', None):
            self._simulator_thread.stop()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

def main():
    import time
    logging.basicConfig(level=logging.INFO)

    with IrReceiver(1) as ir:
        ir.when_message = lambda msg: print(msg.name)
        time.sleep(20)

if __name__ == '__main__':
    main()
