"""Wallets and categories (US-04, US-05)."""

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import CategoryKind
from app.services import category_service, runway_service, wallet_service

from .common import load, me, require_auth, wallet_dict
from .schemas import CategorySchema, WalletSchema

bp = Blueprint("wallets", __name__)
bp.before_request(require_auth)


@bp.get("/wallets")
def list_wallets():
    user = me()
    balances = wallet_service.balances(user.id)
    runways = runway_service.wallet_runways(user.id)
    return jsonify(
        [
            {**wallet_dict(w, balances.get(w.id)), "runway": _runway(runways, w)}
            for w in wallet_service.list_wallets(user.id)
        ]
    )


def _runway(runways, wallet):
    runway = runways.get(wallet.id)
    return runway.to_dict() if runway and not wallet.is_archived else None


@bp.post("/wallets")
def create_wallet():
    wallet = wallet_service.create_wallet(me().id, load(WalletSchema()))
    db.session.commit()
    return jsonify(wallet_dict(wallet)), 201


@bp.get("/wallets/<uuid:wallet_id>")
def get_wallet(wallet_id):
    user = me()
    wallet = wallet_service.get_wallet(user.id, wallet_id)
    runways = runway_service.wallet_runways(user.id)
    return jsonify(
        {
            **wallet_dict(wallet, wallet_service.balances(user.id).get(wallet.id)),
            "runway": _runway(runways, wallet),
        }
    )


@bp.patch("/wallets/<uuid:wallet_id>")
def update_wallet(wallet_id):
    user = me()
    wallet = wallet_service.update_wallet(user.id, wallet_id, load(WalletSchema(), partial=True))
    db.session.commit()
    return jsonify(wallet_dict(wallet, wallet_service.balances(user.id).get(wallet.id)))


@bp.delete("/wallets/<uuid:wallet_id>")
def delete_wallet(wallet_id):
    wallet_service.delete_wallet(me().id, wallet_id)
    db.session.commit()
    return "", 204


@bp.get("/categories")
def list_categories():
    kind = request.args.get("kind")
    kind = CategoryKind(kind) if kind in CategoryKind.__members__ else None
    return jsonify([c.to_dict() for c in category_service.list_categories(me().id, kind)])


@bp.post("/categories")
def create_category():
    cat = category_service.create_category(me().id, load(CategorySchema()))
    db.session.commit()
    return jsonify(cat.to_dict()), 201


@bp.delete("/categories/<uuid:category_id>")
def delete_category(category_id):
    category_service.delete_category(me().id, category_id)
    db.session.commit()
    return "", 204
