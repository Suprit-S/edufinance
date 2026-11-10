"""Remittances - money sent and received across currencies (US-07)."""

from datetime import date

from flask import Blueprint, jsonify

from app.extensions import db
from app.models import Remittance
from app.services import remittance_service

from .common import d, load, me, require_auth, s
from .schemas import RemittanceSchema

bp = Blueprint("remittances", __name__)
bp.before_request(require_auth)


def remittance_dict(r: Remittance) -> dict:
    return {
        "id": str(r.id),
        "from_wallet_id": s(r.from_wallet_id),
        "to_wallet_id": s(r.to_wallet_id),
        "direction": "OWN"
        if r.from_wallet_id and r.to_wallet_id
        else ("IN" if r.to_wallet_id else "OUT"),
        "sent_amount": s(r.sent_amount),
        "sent_currency": r.sent_currency,
        "received_amount": s(r.received_amount),
        "received_currency": r.received_currency,
        "fee_amount": s(r.fee_amount),
        "provider": r.provider,
        "remit_date": d(r.remit_date),
        "effective_rate": s(r.effective_rate),
        "market_rate": s(r.market_rate),
        "hidden_cost_base": s(r.hidden_cost_base),
        "category_id": s(r.category_id),
        "note": r.note,
    }


@bp.get("/remittances")
def list_remittances():
    rows = remittance_service.list_remittances(me().id)
    return jsonify(
        items=[remittance_dict(r) for r in rows],
        summary=remittance_service.summary(rows, date.today().year),
    )


@bp.post("/remittances")
def create_remittance():
    rem = remittance_service.create_remittance(me(), load(RemittanceSchema()))
    db.session.commit()
    return jsonify(remittance_dict(rem)), 201


@bp.get("/remittances/<uuid:remittance_id>")
def get_remittance(remittance_id):
    return jsonify(remittance_dict(remittance_service.get_remittance(me().id, remittance_id)))


@bp.delete("/remittances/<uuid:remittance_id>")
def delete_remittance(remittance_id):
    remittance_service.delete_remittance(me(), remittance_id)
    db.session.commit()
    return "", 204
