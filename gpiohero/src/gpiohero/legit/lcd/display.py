from contextlib import AbstractContextManager

from .PCF8574 import PCF8574_GPIO
from .Adafruit_LCD1602 import Adafruit_CharLCD


class Display(AbstractContextManager):

    def __init__(self, pin_rs = 25, pin_e = 24, pins_db = (23, 17, 21, 22)):
        self.lcd: Adafruit_CharLCD

        for addr in [0x27, 0x3F]: # I2C addresses for PCF8574 and PCF8574A chips
            try:
                mcp = PCF8574_GPIO(addr) # rpi.gpio like adapter for I2C
            except:
                continue
            else:
                self.lcd = Adafruit_CharLCD(pin_rs, pin_e, pins_db, mcp)
                break
        else:
            raise ValueError("I2C Address Error")

        mcp.output(3,1)     # turn on LCD backlight
        self.lcd.begin(16,2)     # set number of LCD lines and columns

    def show(self, message: str):
        self.lcd.setCursor(0, 0)
        self.lcd.message(message)

    def clear(self):
        self.lcd.clear()

    def close(self):
        self.clear()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

