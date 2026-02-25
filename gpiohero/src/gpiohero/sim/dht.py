__all__ = [
    "DHT11",
]

import logging
import random
from typing import Callable
from gpiozero.threads import GPIOThread

class DHT11:
    SIM_INITIAL_TEMP = 20
    SIM_TEMP_FLUX = .5
    SIM_INITAL_HUM = 60
    SIM_HUM_FLUX = 1

    when_measure: Callable[[dict,], None] | None

    def __init__(self, pin: int = 0, sample_interval: float = 1):
        self._logger = logging.getLogger(f"{self.__class__.__name__}@GPIO{pin}")

        self.sample_interval = sample_interval
        self._simulator_thread = GPIOThread(self._simulator)
        self._simulator_thread.start()

    def _simulator(self):
        self._logger.debug("Starting simulation")

        temperature = self.SIM_INITIAL_TEMP
        humidity = self.SIM_INITAL_HUM

        while not self._simulator_thread.stopping.wait(self.sample_interval):
            if when_measure := getattr(self, 'when_measure', None):
                temperature = max(-273.15, temperature + random.uniform(-self.SIM_TEMP_FLUX, self.SIM_TEMP_FLUX))
                humidity = min(100, max(0, humidity + random.uniform(-self.SIM_HUM_FLUX, self.SIM_HUM_FLUX)))

                self._logger.debug("Temperature: %.2f℃ Humidity: %.2f%%", temperature, humidity)
                when_measure({
                    "temperature": temperature,
                    "humidity": humidity,
                })

        self._logger.debug("Simulation stopped")


    def close(self):
        simulator_thread: GPIOThread
        if simulator_thread := getattr(self, '_simulator_thread', None):
            simulator_thread.stop()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


def main():
    import time
    logging.basicConfig(level=logging.DEBUG)

    with DHT11() as dht:
        dht.when_measure = lambda x: None
        time.sleep(20)

if __name__ == "__main__":
    main()
