"""Application factory."""
from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify

from .config import Config
from .errors import register_error_handlers
from .extensions import db

STATIC_FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "static_frontend")


def create_app(config_object: type = Config) -> Flask:
    has_frontend = os.path.isdir(STATIC_FRONTEND_DIR)

    app = Flask(
        __name__,
        static_folder=STATIC_FRONTEND_DIR if has_frontend else None,
        static_url_path="/" if has_frontend else None,
    )
    app.config.from_object(config_object)

    # Derived setting — done here (not on the Config class) so subclasses
    # only need to override MAX_UPLOAD_MB.
    app.config["MAX_CONTENT_LENGTH"] = app.config["MAX_UPLOAD_MB"] * 1024 * 1024

    # Make sure data directories exist before SQLite tries to open the file.
    for key in ("DATA_DIR", "UPLOAD_DIR", "PROCESSED_DIR"):
        Path(app.config[key]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)

    from .api import api_bp
    app.register_blueprint(api_bp)

    register_error_handlers(app)

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    if has_frontend:
        @app.get("/")
        def index():
            return app.send_static_file("index.html")

    with app.app_context():
        db.create_all()

    return app
