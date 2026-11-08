"""Profile and life phases (US-01, US-03)."""

from flask import Blueprint, jsonify

from app.extensions import db
from app.services import auth_service, phase_service

from .common import load, me, phase_dict, require_auth, user_dict
from .schemas import PhaseCreateSchema, PhaseUpdateSchema, ProfileUpdateSchema

bp = Blueprint("profile", __name__)
bp.before_request(require_auth)


@bp.get("/me")
def get_me():
    return jsonify(user_dict(me()))


@bp.patch("/me")
def update_me():
    data = load(ProfileUpdateSchema(), partial=True)
    user = auth_service.update_profile(me(), data)
    db.session.commit()
    db.session.refresh(user)
    return jsonify(user_dict(user))


@bp.get("/phases")
def list_phases():
    return jsonify([phase_dict(p) for p in me().phases])


@bp.post("/phases")
def create_phase():
    phase = phase_service.create_custom_phase(me().id, load(PhaseCreateSchema()))
    db.session.commit()
    return jsonify(phase_dict(phase)), 201


@bp.patch("/phases/<uuid:phase_id>")
def update_phase(phase_id):
    data = load(PhaseUpdateSchema(), partial=True)
    phase = phase_service.update_phase(me().id, phase_id, data)
    db.session.commit()
    return jsonify(phase_dict(phase))


@bp.delete("/phases/<uuid:phase_id>")
def delete_phase(phase_id):
    phase_service.delete_phase(me().id, phase_id)
    db.session.commit()
    return "", 204
