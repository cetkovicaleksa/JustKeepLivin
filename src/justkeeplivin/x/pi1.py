import json
from flask.json import jsonify
from .mqtt import mqtt, add_topics
from .influxdb2 import write, Point
from flask import Flask, Blueprint, request, Response


def init_app(app: Flask):

    add_topics("home/porch/+")

    @mqtt.on_topic("home/porch/door")
    def on_door_message(client, userdata, message):
        try:
            data = json.loads(message.payload.decode('utf-8'))
        except json.JSONDecodeError:
            return
        else:
            write(
                Point("door")
                .tag("location", "porch")
                .tag("simulated", data["simulated"])
                .field("state", data["state"]) # open/closed
            )

    @mqtt.on_topic("home/porch/motion")
    def on_motion_message(client, userdata, message):
        try:
            data = json.loads(message.payload.decode('utf-8'))
        except json.JSONDecodeError:
            return
        else:
            write(
                Point("motion")
                .tag("location", "porch")
                .tag("simulated", data["simulated"])
                .field("detected", data["detected"]) # true/false
            )

    @mqtt.on_topic("home/porch/proximity")
    def on_proximity_message(client, userdata, message):
        try:
            data = json.loads(message.payload.decode('utf-8'))
        except json.JSONDecodeError:
            return
        else:
            write(
                Point("proximity")
                .tag("location", "porch")
                .tag("simulated", data["simulated"])
                .field("distance", data["distance"]) # meters (see if it could be like 2m or 20cm)
                .field("in_range", data["in_range"])
            )

    @mqtt.on_topic("home/porch/typing")
    def on_typing_message(client, userdata, message):
        try:
            data = json.loads(message.payload.decode('utf-8'))
        except json.JSONDecodeError:
            return
        else:
            write(
                Point("typing")
                .tag("location", "porch")
                .tag("simulated", data["simulated"])
                .field("keys", data["keys"]) # typed keys
            )

    api = Blueprint("pi1_api", __package__, url_prefix="/api/pi1")

    @api.route("/light", methods=['PATCH'])
    def switch_light():
        state = request.get_json().get("state")

        match state:
            case 'on' | 'ON' | True | 'off' | 'OFF' | False:
                mqtt.publish("cmd/home/porch/light", json.dumps({ "state": state in {'on', 'ON', True} }))
                return Response(status=204)
            case _:
                return jsonify({"error", f'State must be "ON" or "OFF". Not "{state}".'}), 400


    @api.route("/buzz", methods=['PATCH'])
    def switch_buzzer():
        state = request.get_json().get("state")

        match state:
            case 'on' | 'ON' | True | 'off' | 'OFF' | False:
                mqtt.publish("cmd/home/porch/light", json.dumps({ "state": state in {'on', 'ON', True} }))
                return Response(status=204)
            case _:
                return jsonify({"error", f'State must be "ON" or "OFF". Not "{state}".'}), 400

    app.register_blueprint(api)
