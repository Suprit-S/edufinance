"""Public endpoints: health check and master data needed before login
(the registration form needs the currency and country lists)."""

from flask import Blueprint, jsonify
from sqlalchemy import text

from app.extensions import db
from app.models import Country, Currency

bp = Blueprint("meta", __name__)


@bp.get("/health")
def health():
    """Liveness + database connectivity. Used by Docker and the frontend."""
    db.session.execute(text("SELECT 1"))
    return jsonify(status="ok", database="ok")


@bp.get("/currencies")
def list_currencies():
    rows = Currency.query.order_by(Currency.code).all()
    return jsonify([c.to_dict() for c in rows])


@bp.get("/countries")
def list_countries():
    rows = Country.query.order_by(Country.name).all()
    return jsonify([c.to_dict() for c in rows])
