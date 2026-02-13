import json
import logging
from json import JSONDecodeError
from typing import Any, Dict, Literal

from flask_mqtt import Mqtt
from paho.mqtt.client import Client, MQTTMessage as Message, ConnectFlags, DisconnectFlags, CallbackOnMessage

_logger = logging.getLogger(__name__)

mqtt = Mqtt()
init_app = mqtt.init_app

@mqtt.on_connect()
def _handle_connect(client: Client, userdata: Any, flags: Dict[str, Any], rc: int): ...

@mqtt.on_disconnect()
def _handle_disconnect(client: Client, userdata: Any, rc: int): ...

@mqtt.on_message()
def _handle_unhandled_message(client: Client, userdata: object, message: Message):
    _logger.warning(
        "Unhandled MQTT message",
        extra={
            "host": client.host,
            "userdata": userdata,
            "topic": message.topic,
            "qos": message.qos,
            "payload": try_parse_message(message)
        }
    )

def try_parse_message(message: Message | bytes, encoding="utf-8", format_: Literal["json"] = "json") -> dict | None:
    payload = message.payload if isinstance(message, Message) else message
    try:
        decoded = payload.decode(encoding)
        match format_:
            case "json" | "JSON":
                return json.loads(decoded)
            case _:
                raise ValueError("Unsupported format: " + format_)
    except (UnicodeDecodeError, JSONDecodeError) as e:
        return None

# class JsonMessage(Message, ABC):
#     @property
#     @abstractmethod
#     def json(self) -> dict | None: ...
#
# def on_json_topic(topic):
#     def decorator(handler):
#         @wraps(handler)
#         def wrapper(client, userdata, message):
#             try:
#                 data = json.loads(message.payload.decode("utf-8"))
#             except (UnicodeDecodeError, JSONDecodeError) as e:
#                 return None
#             else:
#                 message.json = data
#                 handler(client, userdata, message)
#
#         return mqtt.on_topic(topic)(wrapper)
#     return decorator
