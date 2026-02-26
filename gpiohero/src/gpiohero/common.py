
import logging
from threading import Lock
from typing import Callable
from gpiozero.threads import GPIOThread
from contextlib import AbstractContextManager


# TODO: Recheck logic, probably has some bugs

class ContdownTimer(AbstractContextManager):
    # when_tick: Callable[[], None] = None
    # when_expired: Callable[[], None] = None
    # when_dismissed: Callable[[], None] = None
    # when_reset: Callable[[], None] = None

    def __init__(self, duration: int = 10, tick: float = 1):
        self._dt = tick
        self._duration = self._remaining = duration
        self._dismissed = False
        self._lock = Lock()

    @property
    def remaining(self):
        return self._remaining

    @property
    def expired(self):
        return self.remaining == 0

    def _countdown(self):
        was_expired = self.expired

        while not self._countdown_thread.stopping.wait(self._dt):
            with self._lock:
                if self.expired:
                    if not was_expired:
                        was_expired = True
                        self._expire()

                    self._tick()
                    continue

                if was_expired:
                    was_expired = False
                self._tick()

    def start(self):
        countdown_thread: GPIOThread

        with self._lock:
            self._start()

    def stop(self):
        countdown_thread: GPIOThread

        with self._lock:
            self._stop()

    def reset(self, duration: int | None = None, start: bool = True):
        with self._lock:
            self._stop()
            self._reset(duration or self._duration)

        if start:
            self.start()

    def snooze(self, duration: int = 10):
        with self._lock:
            self._snooze(duration)

    def dismiss(self):
        with self._lock:
            self._dismiss()

    def _tick(self):
        self._remaining = max(0, self._remaining - 1)

    def _start(self):
        if (
            self.expired
            or (countdown_thread := getattr(self, "_countdown_thread", None))
            and countdown_thread.is_alive()
        ):
                return

        self._countdown_thread = GPIOThread(self._countdown)
        self._countdown_thread.start()

    def _dismiss(self):
        self._dismissed = True

    def _reset(self, duration):
        self._remaining = duration
        self._dismissed = False

    def _snooze(self, duration):
        if not self.expired:
                self._remaining += duration

    def _stop(self):
        if (
            (countdown_thread := getattr(self, "_countdown_thread", None))
            and countdown_thread.is_alive()
        ):
            self._countdown_thread.stop()
            self._countdown_thread = None

    def _expire(self):
        self._dismissed = False

    def close(self):
        self.stop()

    def __exit__(self, exc_type, exc_value, traceback):
        return self.close()

    def __enter__(self) -> 'ContdownTimer': # just for type hints
        return super().__enter__()


# class LoggingCountdownTimer(ContdownTimer):

#     def __init__(self, duration = 10, tick = 1, logger: logging.Logger | None = None): # just make a logger for 4dig7seg and regular logger
#         super().__init__(duration, tick)

#         self._logger = logger or logging.getLogger(f"{self.__class__.__name__}#{str(id(self))[:4]}")

#     def _start(self):
#         super()._start()
#         self._logger.debug("Starting countdown from %.2f", self._remaining)

#     def _tick(self):
#         super()._tick()
#         self._logger.info(self.remaining)

#     def _

