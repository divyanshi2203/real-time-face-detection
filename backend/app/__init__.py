"""Application factory.

Subsequent commits add the API blueprint, persistence, and the detection pipeline.
This commit ships only a health check and (when the React build is present)
serves the built frontend at /.
"""
import os

from flask import Flask, jsonify

STATIC_FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "static_frontend")


def create_app() -> Flask:
    has_frontend = os.path.isdir(STATIC_FRONTEND_DIR)

    app = Flask(
        __name__,
        static_folder=STATIC_FRONTEND_DIR if has_frontend else None,
        static_url_path="/" if has_frontend else None,
    )

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    if has_frontend:
        @app.get("/")
        def index():
            return app.send_static_file("index.html")

    return app
