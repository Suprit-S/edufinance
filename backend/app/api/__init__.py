"""HTTP layer. Routes stay thin: parse + validate input, call a service,
serialise the result. All business rules live in ``app.services``."""

from flask import Flask

from . import auth, loans, meta, plan, profile, remittances, transactions, wallets

API_PREFIX = "/api"

# Routes reachable without a session (NFR-06); everything else needs a JWT.
PUBLIC_ENDPOINTS = {
    "meta.health",
    "meta.list_currencies",
    "meta.list_countries",
    "auth.register",
    "auth.login",
}


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(meta.bp, url_prefix=API_PREFIX)
    app.register_blueprint(auth.bp, url_prefix=f"{API_PREFIX}/auth")
    app.register_blueprint(profile.bp, url_prefix=API_PREFIX)
    app.register_blueprint(wallets.bp, url_prefix=API_PREFIX)
    app.register_blueprint(transactions.bp, url_prefix=API_PREFIX)
    app.register_blueprint(remittances.bp, url_prefix=API_PREFIX)
    app.register_blueprint(plan.bp, url_prefix=API_PREFIX)
    app.register_blueprint(loans.bp, url_prefix=API_PREFIX)
