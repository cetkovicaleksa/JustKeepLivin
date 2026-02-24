from typing import Callable

from .mpu6050 import MPU6050, MPUConstants as C
from gpiozero.threads import GPIOThread


# class MPUMeasurment(NamedTuple):
#     accel: tuple
#     gyro: tuple

# # class AccelRange(IntEnum):
# #     G2 = 2
# #     G4 = 4
# #     G8 = 8
# #     G16 = 16

# #     @property
# #     def sensitivity(self) -> float:
# #         return {
# #             AccelRange.G2: 16384.0,
# #             AccelRange.G4: 8192.0,
# #             AccelRange.G8: 4096.0,
# #             AccelRange.G16: 2048.0,
# #         }[self]


# # class GyroRange(IntEnum):
# #     DPS250 = 250
# #     DPS500 = 500
# #     DPS1000 = 1000
# #     DPS2000 = 2000

# #     @property
# #     def sensitivity(self) -> float:
# #         return {
# #             GyroRange.DPS250: 131.0,
# #             GyroRange.DPS500: 65.5,
# #             GyroRange.DPS1000: 32.8,
# #             GyroRange.DPS2000: 16.4,
# #         }[self]


class MPU:
    when_measure: Callable[[dict,], None] | None

    def __init__(self, bus: int = 1, address: int = C.MPU6050_DEFAULT_ADDRESS, sample_interval: float = .5):
        self._mpu = MPU6050(bus, address)
        self._mpu.dmp_initialize()

        self.sample_interval = sample_interval
        self._polling_thread = GPIOThread(self._poll)
        self._polling_thread.start()

    def _poll(self):
        while not self._polling_thread.stopping.wait(self.sample_interval):
            if when_measure := getattr(self, 'when_measure', None):
                accel, gyro = self._mpu.get_acceleration(), self._mpu.get_rotation()

                when_measure(dict(
                    accel=tuple(a / 131.0 for a in accel),
                    gyro=tuple(g / 16384.0 for g in gyro),
                ))

    def close(self):
        polling_thread: GPIOThread
        if polling_thread := getattr(self, '_polling_thread', None):
            polling_thread.stop()

        # cleanup??

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
