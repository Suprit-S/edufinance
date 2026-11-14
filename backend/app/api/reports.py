"""Reports, dashboard and data rights (US-13, US-14, US-15)."""

import json
from datetime import date

from flask import Blueprint, Response, jsonify, request

from app.extensions import db
from app.services import account_service, report_service

from .common import load, me, require_auth
from .schemas import AccountDeleteSchema

bp = Blueprint("reports", __name__)
bp.before_request(require_auth)


@bp.get("/reports")
def report():
    """?period=MONTH|YEAR|PHASE|LIFETIME&value=2026-11|2026|<phase id>"""
    user = me()
    period = report_service.resolve_period(
        user, request.args.get("period", "MONTH"), request.args.get("value")
    )
    result = report_service.period_report(user, period)
    return jsonify(result)


@bp.get("/reports/costs")
def costs():
    return jsonify(report_service.cost_reports(me()))


@bp.get("/reports/net-worth")
def net_worth():
    result = report_service.net_worth_timeline(me())
    db.session.commit()  # keep freshly cached FX rates
    return jsonify(result)


@bp.get("/reports/loans")
def loans_timeline():
    result = report_service.loan_timeline(me())
    db.session.commit()
    return jsonify(result)


@bp.get("/dashboard")
def dashboard():
    result = report_service.dashboard(me())
    db.session.commit()
    return jsonify(result)


@bp.get("/account/export")
def export():
    """Download of all own data as a JSON file (FR-42)."""
    data = account_service.export_data(me())
    name = f"edufinance-export-{date.today().isoformat()}.json"
    return Response(
        json.dumps(data, indent=2, ensure_ascii=False),
        mimetype="application/json",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )


@bp.delete("/account")
def delete_account():
    data = load(AccountDeleteSchema())
    account_service.delete_account(me(), data["password"])
    db.session.commit()
    return "", 204
