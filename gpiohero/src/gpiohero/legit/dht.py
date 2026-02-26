__all__ = [
    "DHT11",
]

import time
import logging
try:
    import RPi.GPIO as GPIO
except ImportError as e:
    print(e.msg) # idk what else
from enum import IntEnum
from itertools import count
from typing import Callable
from gpiozero.threads import GPIOThread


class DHT11:
    DHTLIB_OK = 0
    DHTLIB_ERROR_CHECKSUM = -1
    DHTLIB_ERROR_TIMEOUT = -2
    DHTLIB_INVALID_VALUE = -999

    DHTLIB_DHT11_WAKEUP = 0.020#0.018		#18ms
    DHTLIB_TIMEOUT = 0.0001			#100us

    when_measure: Callable[[dict,], None] | None

    def __init__(self, pin: int, sample_interval: float = 1):
        self.pin = pin
        self._bits = [0,0,0,0,0]
        GPIO.setmode(GPIO.BCM)

        self._logger = logging.getLogger(f"{self.__class__.__name__}@GPIO{pin}")

        self.sample_interval = sample_interval
        self._polling_thread = GPIOThread(self._poll)
        self._polling_thread.start()

    #Read DHT sensor, store the original data in bits[]
    def readSensor(self,pin,wakeupDelay):
        mask = 0x80
        idx = 0
        self._bits = [0,0,0,0,0]
        GPIO.setup(pin,GPIO.OUT)
        GPIO.output(pin,GPIO.LOW)
        time.sleep(wakeupDelay)
        GPIO.output(pin,GPIO.HIGH)
        #time.sleep(40*0.000001)
        GPIO.setup(pin,GPIO.IN)

        loopCnt = self.DHTLIB_TIMEOUT
        t = time.time()
        while(GPIO.input(pin) == GPIO.LOW):
            if((time.time() - t) > loopCnt):
                #print ("Echo LOW")
                return self.DHTLIB_ERROR_TIMEOUT
        t = time.time()
        while(GPIO.input(pin) == GPIO.HIGH):
            if((time.time() - t) > loopCnt):
                #print ("Echo HIGH")
                return self.DHTLIB_ERROR_TIMEOUT
        for i in range(0,40,1):
            t = time.time()
            while(GPIO.input(pin) == GPIO.LOW):
                if((time.time() - t) > loopCnt):
                    #print ("Data Low %d"%(i))
                    return self.DHTLIB_ERROR_TIMEOUT
            t = time.time()
            while(GPIO.input(pin) == GPIO.HIGH):
                if((time.time() - t) > loopCnt):
                    #print ("Data HIGH %d"%(i))
                    return self.DHTLIB_ERROR_TIMEOUT
            if((time.time() - t) > 0.00005):
                self._bits[idx] |= mask
            #print("t : %f"%(time.time()-t))
            mask >>= 1
            if(mask == 0):
                mask = 0x80
                idx += 1
        #print (self.bits)
        GPIO.setup(pin,GPIO.OUT)
        GPIO.output(pin,GPIO.HIGH)
        return self.DHTLIB_OK
    #Read DHT sensor, analyze the data of temperature and humidity
    def readDHT11(self):
        rv = self.readSensor(self.pin,self.DHTLIB_DHT11_WAKEUP)
        if (rv is not self.DHTLIB_OK):
            self.humidity = self.DHTLIB_INVALID_VALUE
            self.temperature = self.DHTLIB_INVALID_VALUE
            return rv
        self.humidity = self._bits[0]
        self.temperature = self._bits[2] + self._bits[3]*0.1
        sumChk = ((self._bits[0] + self._bits[1] + self._bits[2] + self._bits[3]) & 0xFF)
        if(self._bits[4] is not sumChk):
            return self.DHTLIB_ERROR_CHECKSUM
        return self.DHTLIB_OK

    def _poll(self):
        total = 0
        ok = 0

        while not self._polling_thread.stopping.wait(self.sample_interval):
            if when_measure := getattr(self, 'when_measure', None):
                total += 1

                match chk := self.readDHT11():
                    case self.DHTLIB_OK:
                        ok += 1
                        when_measure({
                            "temperature": self.temperature,
                            "humidity": self.humidity,
                        })
                    case _:
                        self._logger.info("Reading error: %s [%d sucessfull readings out of %d, %f accuracy]", chk, ok, total, ok/total * 100)

    def close(self):
        polling_thread: GPIOThread
        if polling_thread := getattr(self, '_polling_thread', None):
            polling_thread.stop()

        GPIO.cleanup(self.pin)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
