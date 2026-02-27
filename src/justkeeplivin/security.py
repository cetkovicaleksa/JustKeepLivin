import json
from dataclasses import dataclass, field
from threading import Timer, Lock

from flask import Flask
from abc import ABC, abstractmethod
from .x.mqtt import mqtt, Client, try_parse_message, Message
from .x.influxdb2 import write, Point

# NOTE: there are some threading races but should be fine :)

@dataclass
class SecurityEvent:
    type: str
    source: str | None = None
    extra: dict = field(default_factory=dict)

    PERSON_ENTERED = "PERSON_ENTERED"
    PERSON_EXITED = "PERSON_EXITED"
    MOTION_DETECTED = "MOTION_DETECTED"
    APPROACHED_DOOR = "APPROACHED_DOOR"
    IKONA_TILTED = "IKONA_TILTED"
    PIN_ENTERED = "PIN_ENTERED"
    # for convenience to manually trigger states
    DISARM = "DISARM"
    ARMING = "ARMING"
    ARM = "ARM"
    ALARM = "ALARM"

class SecurityState(ABC):

    @abstractmethod
    def handle_event(self, event: SecurityEvent): ...

    def on_enter(self):
        pass

    def on_exit(self):
        pass

class SecurityContext:

    def __init__(self, security_pin: str):
        self._state_lock = Lock()
        self.security_pin = security_pin
        self.people_counter: int = 0
        self.state = DisarmedState(self)

    def handle_event(self, event: SecurityEvent | str):
        event = event if isinstance(event, SecurityEvent) else SecurityEvent(type=event)

        match event.type:
            case SecurityEvent.PERSON_ENTERED:
                self.people_counter += 1
            case SecurityEvent.PERSON_EXITED:
                self.people_counter = min(0, self.people_counter - 1)
            case SecurityEvent.DISARM | SecurityEvent.ARM | SecurityEvent.ALARM | SecurityEvent.ARMING:
                State = {
                    SecurityEvent.DISARM: DisarmedState,
                    SecurityEvent.ARMING: ArmingState,
                    SecurityEvent.ARM: ArmedState,
                    SecurityEvent.ALARM: AlarmState,
                }[event.type]

                if not isinstance(self.state, State):
                    self.state = State(self)

        self.state.handle_event(event)

    def is_pin_correct(self, event: SecurityEvent):
        return self.security_pin == event.extra.get("pin")

    @property
    def state(self) -> SecurityState:
        return self._state

    @state.setter
    def state(self, new_state: SecurityState):
        with self._state_lock: # at least make this atomic change
            if hasattr(self, "_state"): self._state.on_exit()
            new_state.on_enter()
            self._state = new_state


class DisarmedState(SecurityState):

    def __init__(self, context: SecurityContext):
        self.context = context

    def handle_event(self, event: SecurityEvent):
        match event.type:
            case SecurityEvent.PIN_ENTERED if self.context.is_pin_correct(event):
                self.context.state = ArmingState(self.context)


class ArmingState(SecurityState):

    def __init__(self, context: SecurityContext, arming_delay: float = 10):
        self.context = context
        self.timer = Timer(arming_delay, self._arm)

    def handle_event(self, event: SecurityEvent):
        match event.type:
            case SecurityEvent.PIN_ENTERED if self.context.is_pin_correct(event):
                self.context.state = DisarmedState(self.context)

    def on_enter(self):
        self.timer.start()

    def on_exit(self):
        self.timer.cancel()

    def _arm(self):
        self.context.state = ArmedState(self.context)


class ArmedState(SecurityState):

    def __init__(self, context: SecurityContext):
        self.context = context
        self.alarm_timer: Timer | None = None
        self.alarm_lock = Lock()

    def handle_event(self, event: SecurityEvent):
        match event.type:
            case SecurityEvent.IKONA_TILTED:
                self._trigger_alarm()
            case SecurityEvent.MOTION_DETECTED if self.context.people_counter == 0:
                self._trigger_alarm()
            case SecurityEvent.APPROACHED_DOOR:
                self._schedule_alarm()
            case SecurityEvent.PIN_ENTERED if self.context.is_pin_correct(event):
                self._dismiss_alarm()
            # case SecurityEvent.PIN_ENTERED if self.context.is_pin_correct(event):
            #     self.context.state = DisarmedState(self.context)

    def _dismiss_alarm(self):
        with self.alarm_lock:
            if self.alarm_timer:
                self.alarm_timer.cancel()
                self.alarm_timer = None

    def _schedule_alarm(self, delay: float = 10):
        with self.alarm_lock:
            if not self.alarm_timer:
                self.alarm_timer = Timer(delay, self._trigger_alarm)
                self.alarm_timer.start()

    def _trigger_alarm(self):
        self.context.state = AlarmState(self.context)

    def on_exit(self):
        self._dismiss_alarm()


class AlarmState(SecurityState):

    def __init__(self, context: SecurityContext):
        self.context = context

    def handle_event(self, event: SecurityEvent):
        match event.type:
            case SecurityEvent.PIN_ENTERED if self.context.is_pin_correct(event):
                 self.context.state = DisarmedState(self.context)

    # TODO: Notification?!
    def on_enter(self):
        write(
            Point("alarm")
            .field("enabled", True)
        )
        mqtt.publish(
            "cmd/home/porch/buzz",
            json.dumps({
                "action": "on"
            })
        )

    def on_exit(self):
        write(
            Point("alarm")
            .field("enabled", False)
        )
        mqtt.publish(
            "cmd/home/porch/buzz",
            json.dumps({
                "action": "off"
            })
        )

topics = [
    ("home/+/motion", 0),
    ("home/+/typing", 0),
]

def init_app(app: Flask):
    security_context = SecurityContext(security_pin=app.config.get("HOME_PIN"))
    app.security_context = security_context

    @mqtt.on_topic("home/+/motion")
    def on_motion(client: Client, userdata: object, message: Message):
        location = message.topic.split('/')[1]

        if (data := try_parse_message(message)) and data.get("detected", False):
            security_context.handle_event(SecurityEvent.MOTION_DETECTED)

            if location in {"porch", "garage"}:
                security_context.handle_event(SecurityEvent.APPROACHED_DOOR)

                # TODO: Based on ultrasonic sensor data determine if person is approaching/leaving (entering or exiting the house)
                import random
                security_context.handle_event(random.choice([SecurityEvent.PERSON_ENTERED, SecurityEvent.PERSON_EXITED]))

    @mqtt.on_topic("home/porch/typing")
    def on_pin_entered(client: Client, userdata: object, message: Message):
        if data := try_parse_message(message):
            security_context.handle_event(SecurityEvent(
                SecurityEvent.PIN_ENTERED,
                extra={
                    "keys": data.get("keys"),
                }
            ))

    @mqtt.on_topic("home/икона/gyro")
    def on_ikona_gyro(client: Client, userdata: object, message: Message):
        if data := try_parse_message(message):
            accel = data["accel"]
            magnitude = sum(xi**2 for xi in accel.values())**1/2

            if magnitude > 0.5:
                security_context.handle_event(SecurityEvent.IKONA_TILTED)

    mqtt.subscribe(topics)
