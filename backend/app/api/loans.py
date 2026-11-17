"""Loan Planner (US-10, US-11)."""

from flask import Blueprint, jsonify

from app.extensions import db
from app.models import Loan, LoanPayment
from app.services import loan_service

from .common import d, load, me, require_auth, s
from .schemas import LoanPaymentSchema, LoanSchema

bp = Blueprint("loans", __name__)
bp.before_request(require_auth)


def payment_dict(p: LoanPayment) -> dict:
    return {
        "id": str(p.id),
        "payment_type": p.payment_type.value,
        "amount": s(p.amount),
        "paid_on": d(p.paid_on),
        "interest_part": s(p.interest_part),
        "principal_part": s(p.principal_part),
        "balance_before": s(p.balance_before),
        "balance_after": s(p.balance_after),
        "interest_saved": s(p.interest_saved),
        "emis_saved": p.emis_saved,
        "transaction_id": s(p.transaction_id),
        "note": p.note,
    }


def loan_dict(loan: Loan, detail: bool = False) -> dict:
    user = me()
    data = {
        "id": str(loan.id),
        "name": loan.name,
        "lender": loan.lender,
        "currency_code": loan.currency_code,
        "annual_rate_pct": s(loan.annual_rate_pct),
        "sanctioned_amount": s(loan.sanctioned_amount),
        "outstanding_amount": s(loan.outstanding_amount),
        "emi_amount": s(loan.emi_amount),
        "emi_start_date": d(loan.emi_start_date),
        "min_part_payment": s(loan.min_part_payment),
        "default_wallet_id": s(loan.default_wallet_id),
        "status": loan.status.value,
        "note": loan.note,
        "summary": loan_service.loan_summary(loan, schedule=detail),
        "affordability": loan_service.affordability(user, loan),
    }
    if detail:
        data["payments"] = [payment_dict(p) for p in reversed(loan.payments)]
    return data


@bp.get("/loans")
def list_loans():
    result = [loan_dict(loan) for loan in loan_service.list_loans(me().id)]
    db.session.commit()
    return jsonify(result)


@bp.post("/loans")
def create_loan():
    loan = loan_service.create_loan(me(), load(LoanSchema()))
    db.session.commit()
    return jsonify(loan_dict(loan, detail=True)), 201


@bp.get("/loans/<uuid:loan_id>")
def get_loan(loan_id):
    result = loan_dict(loan_service.get_loan(me().id, loan_id), detail=True)
    db.session.commit()
    return jsonify(result)


@bp.patch("/loans/<uuid:loan_id>")
def update_loan(loan_id):
    loan = loan_service.update_loan(me(), loan_id, load(LoanSchema(), partial=True))
    db.session.commit()
    return jsonify(loan_dict(loan, detail=True))


@bp.delete("/loans/<uuid:loan_id>")
def delete_loan(loan_id):
    loan_service.delete_loan(me(), loan_id)
    db.session.commit()
    return "", 204


@bp.post("/loans/<uuid:loan_id>/payments")
def record_payment(loan_id):
    payment = loan_service.record_payment(me(), loan_id, load(LoanPaymentSchema()))
    db.session.commit()
    return jsonify(payment_dict(payment)), 201


@bp.delete("/loans/<uuid:loan_id>/payments/<uuid:payment_id>")
def undo_payment(loan_id, payment_id):
    loan_service.undo_payment(me(), loan_id, payment_id)
    db.session.commit()
    return "", 204
