"""HTTP layer. Routes stay thin: parse + validate input, call a service,
serialise the result. All business rules live in ``app.services``."""

from flask import Flask

from . import meta

API_PREFIX = "/api"


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(meta.bp, url_prefix=API_PREFIX)
