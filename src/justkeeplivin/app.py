from flask import Flask
from itertools import chain

from .routes import routes
from .api import api
from .x import init_extensions


def create_app():
    app = Flask(__name__)
    app.config.from_mapping(

    )
    init_extensions(app)

    for bp in chain(routes, api):
        app.register_blueprint(bp)

    return app
