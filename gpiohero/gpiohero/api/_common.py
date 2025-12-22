from contextlib import AbstractContextManager



class DeviceProtocol(AbstractContextManager):
    def close(self) -> None: ...
    