import os
from pathlib import Path
from flask import Flask

from .routes import main
from .api import api
from .x import init_extensions
from .telemetry import init_app as init_telemetry


def create_app():
    app = Flask(__name__)
    load_config(app)
    init_extensions(app)

    for bp in [main, api]:
        app.register_blueprint(bp)

    init_telemetry(app)
    return app

def load_config(app: Flask):
    cfg = Path(os.getenv('JKL_CONFIG', app.instance_path + "/config.py"))
    match cfg.suffix.lower():
        case '.toml':
            ...
        case '.py':
            app.config.from_pyfile(cfg)
        case _:
            raise ValueError('Config format not supported: ' + cfg.suffix)


