"""Consistent JSON error responses.

Every error leaves the API in the same shape, so the frontend can show it
without special cases:

    {"error": {"code": "VALIDATION_ERROR", "message": "...", "details": {...}}}
"""

from flask import Flask, jsonify
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    """Raise from services/routes for an expected, user-facing error."""

    def __init__(self, message: str, status: int = 400, code: str = "BAD_REQUEST", details=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.details = details


class NotFound(ApiError):
    def __init__(self, what: str = "Resource"):
        super().__init__(f"{what} not found.", 404, "NOT_FOUND")


class Conflict(ApiError):
    def __init__(self, message: str):
        super().__init__(message, 409, "CONFLICT")


def error_body(code: str, message: str, details=None):
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return body


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(err: ApiError):
        return jsonify(error_body(err.code, err.message, err.details)), err.status

    @app.errorhandler(ValidationError)
    def handle_validation(err: ValidationError):
        # 422 for well-formed requests with invalid content (NFR, test TC-V*).
        return (
            jsonify(error_body("VALIDATION_ERROR", "Some fields are invalid.", err.messages)),
            422,
        )

    @app.errorhandler(HTTPException)
    def handle_http(err: HTTPException):
        code = (err.name or "HTTP_ERROR").upper().replace(" ", "_")
        return jsonify(error_body(code, err.description or err.name)), err.code

    @app.errorhandler(Exception)
    def handle_unexpected(err: Exception):  # pragma: no cover - safety net
        app.logger.exception("Unhandled error: %s", err)
        return jsonify(error_body("INTERNAL_ERROR", "Something went wrong.")), 500
