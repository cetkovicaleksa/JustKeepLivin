import os
from pathlib import Path
from flask import Flask

from .routes import routes
from .x import init_extensions


def create_app():
    app = Flask(__name__)
    load_config(app)
    init_extensions(app)

    for bp in routes:
        app.register_blueprint(bp)

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


