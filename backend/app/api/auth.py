"""Authentication: register, login, logout, current user, password (US-01, US-02)."""

from flask import Blueprint, current_app, jsonify
from flask_jwt_extended import create_access_token, get_jwt, jwt_required

from app.extensions import db
from app.services import auth_service

from .common import load, me, user_dict
from .schemas import LoginSchema, PasswordChangeSchema, RegisterSchema

bp = Blueprint("auth", __name__)


def _token_response(user, status=200):
    token = create_access_token(identity=str(user.id))
    expires = int(current_app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds())
    return jsonify(access_token=token, expires_in=expires, user=user_dict(user)), status


@bp.post("/register")
def register():
    data = load(RegisterSchema())
    user = auth_service.register(data, current_app.config["SETTLING_IN_DAYS_DEFAULT"])
    db.session.commit()
    return _token_response(user, 201)


@bp.post("/login")
def login():
    data = load(LoginSchema())
    user = auth_service.authenticate(data["email"], data["password"])
    return _token_response(user)


@bp.post("/logout")
@jwt_required()
def logout():
    claims = get_jwt()
    auth_service.revoke_token(claims["jti"], me().id, claims["exp"])
    db.session.commit()
    return "", 204


@bp.post("/password")
@jwt_required()
def change_password():
    data = load(PasswordChangeSchema())
    auth_service.change_password(me(), data["current_password"], data["new_password"])
    db.session.commit()
    return "", 204
