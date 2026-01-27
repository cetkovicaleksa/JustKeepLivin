import os
from pathlib import Path
from flask import Flask
from itertools import chain

from .routes import routes
from .api import api
from .x import init_extensions


def create_app():
    app = Flask(__name__)
    load_config(app)
    init_extensions(app)

    for bp in chain(routes, api):
        app.register_blueprint(bp)

    return app

def load_config(app: Flask):
    if not (cfg := os.getenv('JKL_CONFIG', None)):
        return

    cfg = Path(cfg)
    match cfg.suffix.lower():
        case '.toml':
            ...
        case '.py':
            app.config.from_pyfile(cfg)
        case _:
            raise ValueError('Config format not supported: ' + cfg.suffix)


