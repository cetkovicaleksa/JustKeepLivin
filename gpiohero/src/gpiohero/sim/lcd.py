import logging
from contextlib import AbstractContextManager


class Display(AbstractContextManager):

    def __init__(self, pin_rs = 25, pin_e = 24, pins_db = (23, 17, 21, 22)):

        self._logger = logging.getLogger(f"{self.__class__.__name__}")

    def show(self, message: str):
        self._logger.info("[ %s ]", message.ljust(16))

    def clear(self):
        self._logger.info("[ %s ]", " " * 16)

    def close(self):
        self.clear()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __enter__(self) -> 'Display': # just for type hints
        return super().__enter__()

def main():
    logging.basicConfig(level=logging.INFO)

    with Display() as lcd:
        lcd.show("Hello World")

        import time
        time.sleep(5)

if __name__ == "__main__":
    main()
