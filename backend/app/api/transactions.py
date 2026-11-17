"""Transactions and market rates (US-05, US-06)."""

from datetime import date

from flask import Blueprint, jsonify

from app.errors import ApiError
from app.extensions import db
from app.services import fx_service, transaction_service

from .common import load, me, require_auth, transaction_dict
from .schemas import (
    RateQuerySchema,
    TransactionFilterSchema,
    TransactionSchema,
    TransactionUpdateSchema,
)

bp = Blueprint("transactions", __name__)
bp.before_request(require_auth)


@bp.get("/transactions")
def list_transactions():
    f = load(TransactionFilterSchema(), source="args")
    rows, total = transaction_service.list_transactions(
        me().id,
        wallet_id=f.get("wallet_id"),
        kind=f.get("kind"),
        category_id=f.get("category_id"),
        phase_id=f.get("phase_id"),
        date_from=f.get("date_from"),
        date_to=f.get("date_to"),
        search=f.get("q"),
        page=f["page"],
        per_page=f["per_page"],
    )
    return jsonify(
        items=[transaction_dict(t) for t in rows],
        total=total,
        page=f["page"],
        per_page=f["per_page"],
    )


@bp.post("/transactions")
def create_transaction():
    txn = transaction_service.create_transaction(me(), load(TransactionSchema()))
    db.session.commit()
    return jsonify(transaction_dict(txn)), 201


@bp.get("/transactions/<uuid:txn_id>")
def get_transaction(txn_id):
    return jsonify(transaction_dict(transaction_service.get_transaction(me().id, txn_id)))


@bp.patch("/transactions/<uuid:txn_id>")
def update_transaction(txn_id):
    data = load(TransactionUpdateSchema(), partial=True)
    txn = transaction_service.update_transaction(me(), txn_id, data)
    db.session.commit()
    return jsonify(transaction_dict(txn))


@bp.delete("/transactions/<uuid:txn_id>")
def delete_transaction(txn_id):
    transaction_service.delete_transaction(me(), txn_id)
    db.session.commit()
    return "", 204


@bp.get("/fx/rate")
def market_rate():
    """Market rate to pre-fill forms (FR-16). ``estimated`` = not current."""
    q = load(RateQuerySchema(), source="args")
    try:
        result = fx_service.get_rate(q["from_"], q["to"], q.get("date") or date.today())
    except fx_service.UnknownCurrency as exc:
        raise ApiError(str(exc), 422, "VALIDATION_ERROR") from exc
    db.session.commit()  # keep freshly cached rates
    return jsonify(result.to_dict())
