"""Monthly Plan and Target to Earn (US-08, US-09)."""

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import MonthlyPlanItem
from app.services import plan_service

from .common import d, load, me, require_auth, s
from .schemas import PlanItemSchema

bp = Blueprint("plan", __name__)
bp.before_request(require_auth)


def item_dict(item: MonthlyPlanItem, active: bool | None = None) -> dict:
    return {
        "id": str(item.id),
        "name": item.name,
        "category_id": s(item.category_id),
        "amount": s(item.amount),
        "currency_code": item.currency_code,
        "valid_from": d(item.valid_from),
        "valid_to": d(item.valid_to),
        "phase_id": s(item.phase_id),
        "loan_id": s(item.loan_id),
        "active_this_month": active,
    }


@bp.get("/plan")
def get_plan():
    """All plan items plus the minimum target of a month (?month=YYYY-MM)."""
    user = me()
    month = plan_service.parse_month(request.args.get("month"))
    target = plan_service.minimum_target(user, month)
    active = {line["item"].id: line for line in target["lines"]}
    db.session.commit()  # keep freshly cached FX rates
    return jsonify(
        month=month.strftime("%Y-%m"),
        currency=user.base_currency,
        minimum_target=str(target["total"]),
        estimated_rates=target["estimated"],
        items=[
            {
                **item_dict(i, i.id in active),
                "amount_base": s(active[i.id]["amount_base"]) if i.id in active else None,
            }
            for i in plan_service.list_items(user.id)
        ],
    )


@bp.post("/plan")
def create_item():
    item = plan_service.create_item(me().id, load(PlanItemSchema()))
    db.session.commit()
    return jsonify(item_dict(item)), 201


@bp.patch("/plan/<uuid:item_id>")
def update_item(item_id):
    item = plan_service.update_item(me().id, item_id, load(PlanItemSchema(), partial=True))
    db.session.commit()
    return jsonify(item_dict(item))


@bp.delete("/plan/<uuid:item_id>")
def delete_item(item_id):
    plan_service.delete_item(me().id, item_id)
    db.session.commit()
    return "", 204


@bp.get("/target")
def target_to_earn():
    """Target to Earn for a month (?month=YYYY-MM, default current)."""
    user = me()
    result = plan_service.target_to_earn(user, plan_service.parse_month(request.args.get("month")))
    db.session.commit()
    return jsonify(result)
