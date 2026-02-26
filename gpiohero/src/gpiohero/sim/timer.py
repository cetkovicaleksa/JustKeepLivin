import logging
from typing import Iterable
from gpiohero.common import ContdownTimer


class Timer(ContdownTimer):

    def __init__(self, segments: Iterable[int], digits: Iterable[int], duration = 10, tick = 1):
        super().__init__(duration, tick)

        self._logger = logging.getLogger(f"{self.__class__.__name__}#{str(id(self))[:3]}")

    def _start(self):
        super()._start()
        self._logger.info("Starting countdown from %d", self._remaining)

    def _expire(self):
        super()._expire()
        self._logger.info("Countdown finished")

    def _reset(self, duration):
        super()._reset(duration)
        self._logger.info("Reset to %d", self._remaining)

    def _dismiss(self):
        super()._dismiss()
        self._logger.info("Dismissed")

    def _snooze(self, duration):
        super()._snooze(duration)
        self._logger.info("Delayed for %d", duration)

    def _tick(self):
        super()._tick()
        if not self.expired:
            self._logger.debug("Tick @ %d", self._remaining)
        elif not self._dismissed:
            self._logger.debug("Blink")


def main():
    logging.basicConfig(level=logging.DEBUG)

    with Timer(5, .9) as timer:
        timer.start()
        timer.snooze(6)

        import time
        time.sleep(10)
        timer.dismiss()

        time.sleep(3)

        timer.reset(2)
        timer.dismiss()
        time.sleep(5)

if __name__ == "__main__":
    main()
