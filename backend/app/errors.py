"""JSON error handling.

Every error returned by the API has the same shape::

    {"error": {"code": "<machine-readable>", "message": "<human-readable>"}}

Domain code raises :class:`APIError` with an explicit status; everything else
is funneled through Werkzeug's HTTPException handler or a final catch-all.
"""
from __future__ import annotations

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge


class APIError(Exception):
    """An expected, mapped-to-HTTP error raised by route handlers."""

    def __init__(self, code: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def _payload(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(APIError)
    def _api_error(e: APIError):
        return jsonify(_payload(e.code, e.message)), e.status

    @app.errorhandler(RequestEntityTooLarge)
    def _too_large(_):
        max_mb = app.config.get("MAX_UPLOAD_MB")
        return jsonify(_payload(
            "payload_too_large",
            f"Upload exceeds the {max_mb} MB limit.",
        )), 413

    @app.errorhandler(404)
    def _not_found(_):
        return jsonify(_payload("not_found", "Resource not found.")), 404

    @app.errorhandler(405)
    def _method_not_allowed(_):
        return jsonify(_payload("method_not_allowed", "Method not allowed.")), 405

    @app.errorhandler(HTTPException)
    def _http_exc(e: HTTPException):
        code = (e.name or "http_error").lower().replace(" ", "_")
        return jsonify(_payload(code, e.description or e.name)), e.code or 500

    @app.errorhandler(Exception)
    def _unexpected(e: Exception):
        app.logger.exception("Unhandled error: %s", e)
        return jsonify(_payload(
            "internal_error",
            "Unexpected server error.",
        )), 500
