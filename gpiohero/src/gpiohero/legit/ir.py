# Implemetation for a NEC Extended ir receiver adapted from this one:
#
#-----------------------------------------#
# Name - IR-Finalized.py
# Description - The finalized code to read data from an IR sensor and then reference it with stored values
# Author - Lime Parallelogram
# License - Completely Free
# Date - 12/09/2019
#------------------------------------------------------------#

__all__ = [
    "IrMessage",
    "IrReceiver",
]

from typing import Callable

try:
    import RPi.GPIO as GPIO
except ImportError as e:
    print(e.msg) # idk what else

import time
import datetime
from gpiozero.threads import GPIOThread
from enum import IntEnum


class IrMessage(IntEnum):
    UP = 0x300ff629d
    DOWN = 0x300ffa857
    OK = 0x300ff02fd
    LEFT = 0x300ff22dd
    RIGHT = 0x300ffc23d
    ONE = 0x300ff6897
    TWO = 0x300ff9867
    THREE = 0x300ffb04f
    FOUR = 0x300ff30cf
    FIVE = 0x300ff18e7
    SIX = 0x300ff7a85
    SEVEN = 0x300ff10ef
    EIGHT = 0x300ff38c7
    NINE = 0x300ff5aa5
    ZERO = 0x300ff4ab5
    ASTERIX = 0x300ff42bd
    HASHTAG = 0x300ff52ad

    @classmethod
    def from_hex(cls, value: str) -> 'IrMessage':
        return cls(int(value, 16))

    def hex(self):
        return hex(self.value)

    @classmethod
    def from_bin(cls, value: str) -> 'IrMessage':
        return cls(int(value, 2))

    def bin(self):
        return bin(self.value)


class IrReceiver:

    def __init__(self, pin: int):
        self.pin = pin

        # GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.IN)

        self.when_message: Callable[[IrMessage,], None] | None = None
        self._listening_thread = GPIOThread(self._listen)
        self._listening_thread.start()

    def _listen(self):
        while not self._listening_thread.stopping.is_set():
            try:
                message = IrMessage(self._getBinary())
            except:
                pass
            else:
                if when_message := getattr(self, 'when_message', None):
                    when_message(message)


    def _getBinary(self):
		# Internal vars
        num1s = 0  # Number of consecutive 1s read
        binary = 1  # The binary value
        command = []  # The list to store pulse times in
        previousValue = 0  # The last value
        value = GPIO.input(self.pin)  # The current value

        # Waits for the sensor to pull pin low
        while value:
            time.sleep(0.0001) # This sleep decreases CPU utilization immensely
            value = GPIO.input(self.pin)

        # Records start time
        startTime = datetime.now()

        while True:
            # If change detected in value
            if previousValue != value:
                now = datetime.now()
                pulseTime = now - startTime #Calculate the time of pulse
                startTime = now #Reset start time
                command.append((previousValue, pulseTime.microseconds)) #Store recorded data

            # Updates consecutive 1s variable
            if value:
                num1s += 1
            else:
                num1s = 0

            # Breaks program when the amount of 1s surpasses 10000
            if num1s > 10000:
                break

            # Re-reads pin
            previousValue = value
            value = GPIO.input(self.pin)

        # Converts times to binary
        for (typ, tme) in command:
            if typ == 1: #If looking at rest period
                if tme > 1000: #If pulse greater than 1000us
                    binary = binary *10 +1 #Must be 1
                else:
                    binary *= 10 #Must be 0

        if len(str(binary)) > 34: #Sometimes, there is some stray characters
            binary = int(str(binary)[:34])

        return binary

    def close(self):
        listening_thread: GPIOThread
        if listening_thread := getattr(self, '_listening_thread', None):
            listening_thread.stop()

        GPIO.cleanup(self.pin)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
