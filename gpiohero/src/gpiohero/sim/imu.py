__all__ = [
    "MPU",
]

import time
import logging
from typing import Callable
from math import sin, cos, pi
from gpiozero.threads import GPIOThread


class MPU:
    SIM_MOVEMENT_SCALE = 1.0        # Base movement amplitude
    SIM_FREQ = 0.5            # Hz (oscillation frequency)
    SIM_GYRO_SCALE = 50.0     # deg/s multiplier
    SIM_GRAVITY = 9.81                # m/s²

    when_measure: 'Callable[[dict,], None] | None'

    def __init__(self, bus: int = 1, address: int = 104, sample_interval: float = .5):
        self._logger = logging.getLogger(f"{self.__class__.__name__}@(bus={bus}, addr={address})")

        self.sample_interval = sample_interval
        self._simulator_thread = GPIOThread(self._simulator)
        self._simulator_thread.start()

    def _simulator(self): # thanks to chat.openai.com
        self._logger.debug("Starting simulation")
        init_t = time.perf_counter()

        while not self._simulator_thread.stopping.wait(self.sample_interval):
            if getattr(self, 'when_measure', None):
                t = time.perf_counter() - init_t

                angle = sin(2 * pi * self.SIM_FREQ * t)
                angular_velocity = (
                    2 * pi * self.SIM_FREQ
                    * cos(2 * pi * self.SIM_FREQ * t)
                    * 180 / pi
                )

                accel = self.SIM_MOVEMENT_SCALE * angle * self.SIM_GRAVITY, 0, self.SIM_GRAVITY
                gyro = self.SIM_MOVEMENT_SCALE * angular_velocity * self.SIM_GYRO_SCALE, 0, 0

                self._logger.debug("Accel: %s [g] Gyro: %s [deg/s]", accel, gyro)
                self.when_measure({
                    "accel": accel,
                    "gyro": gyro,
                })

        self._logger.debug("Simulation stopped")


    def close(self):
        if getattr(self, '_simulator_thread', None):
            self._simulator_thread.stop()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


def main():
    logging.basicConfig(level=logging.DEBUG)

    class IkonaSensor(MPU):
        SIM_MOVEMENT_SCALE = 0.01
        SIM_FREQ = 0.06
        SIM_GYRO_SCALE = 5

    with IkonaSensor(sample_interval=1) as mpu:
        mpu.when_measure = lambda _: None
        time.sleep(20)

if __name__ == "__main__":
    main()
