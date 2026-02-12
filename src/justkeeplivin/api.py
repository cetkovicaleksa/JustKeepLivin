import json
from sqlite3.dbapi2 import paramstyle
from http import HTTPStatus

from .x.mqtt import mqtt
from flask import jsonify, Blueprint, request, Response

api = Blueprint('api', __name__, url_prefix="/api")
for bp in [
    pi1 := Blueprint('pi1', __name__, url_prefix="/pi1"),
    pi2 := Blueprint('pi2', __name__, url_prefix="/pi2"),
    pi3 := Blueprint('pi3', __name__, url_prefix="/pi3")
]:
    api.register_blueprint(bp)

# TODO: Figure out nicer api, and add support for switch with duration to hold for...

# /api/living_room/switch?device=light&state=on
@api.route("/<location>/switch", methods=['PATCH', 'PUT'])
def switch_device(location: str):
    state = request.args.get("state", 'on')
    device = request.args.get("device")

    if not device:
        return jsonify({"error", f'Device must be specified.'}), 400

    match state:
        case 'on' | 'ON' | True | 'off' | 'OFF' | False:
            mqtt.publish(f"cmd/home/{location}/{device}", json.dumps({ "state": state in {'on', 'ON', True} }))
            return Response(status=HTTPStatus.NO_CONTENT)
        case _:
            return jsonify({"error", f'State must be "ON" or "OFF". Not "{state}".'}), HTTPStatus.BAD_REQUEST

#endregion
