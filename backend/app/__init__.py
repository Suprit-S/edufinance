"""EduFinance backend - Flask application factory."""

import click
from flask import Flask

from .config import CONFIGS
from .errors import error_body, register_error_handlers
from .extensions import cors, db, jwt, migrate


def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(CONFIGS[config_name])
    app.json.sort_keys = False  # keep field order as written (readable API)

    db.init_app(app)
    migrate.init_app(app, db, directory="migrations")
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    from . import models  # noqa: F401  (register tables for Alembic)
    from .api import register_blueprints

    register_blueprints(app)
    register_error_handlers(app)
    _register_jwt_callbacks()
    _register_cli(app)
    return app


def _register_jwt_callbacks() -> None:
    """Turn JWT problems into the standard error body (401) and reject
    tokens revoked on logout."""
    from .models import RevokedToken

    @jwt.token_in_blocklist_loader
    def is_revoked(_header, payload):
        return db.session.get(RevokedToken, payload["jti"]) is not None

    @jwt.unauthorized_loader
    def missing_token(reason):
        return error_body("UNAUTHORIZED", "Please log in to continue."), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return error_body("UNAUTHORIZED", "Your session is invalid. Please log in again."), 401

    @jwt.expired_token_loader
    def expired_token(_header, _payload):
        return error_body("SESSION_EXPIRED", "Your session has expired. Please log in again."), 401

    @jwt.revoked_token_loader
    def revoked_token(_header, _payload):
        return error_body("UNAUTHORIZED", "You have been logged out. Please log in again."), 401


def _register_cli(app: Flask) -> None:
    @app.cli.command("seed-master")
    def seed_master():
        """Insert/update currencies, countries, categories and fallback rates."""
        from .seed.master_data import seed_master_data

        counts = seed_master_data()
        click.echo(f"Master data seeded: {counts}")
