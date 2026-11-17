"""Account and security tests (TC-A01..A07, TC-SEC01..SEC03)."""

from app.api import PUBLIC_ENDPOINTS
from app.extensions import db
from app.models import User

from .conftest import ANANYA


def test_tc_a01_register_creates_user_and_four_phases(client):
    res = client.post("/api/auth/register", json=ANANYA)
    assert res.status_code == 201
    body = res.get_json()
    assert body["access_token"]
    assert body["user"]["email"] == "ananya@example.com"
    assert [p["phase_type"] for p in body["user"]["phases"]] == [
        "PRE_DEPARTURE",
        "SETTLING_IN",
        "STUDY",
        "WORK",
    ]


def test_tc_a02_duplicate_email_is_rejected(client, register):
    register()
    res = client.post("/api/auth/register", json={**ANANYA, "email": "ANANYA@example.com"})
    assert res.status_code == 409
    assert res.get_json()["error"]["code"] == "CONFLICT"
    assert db.session.query(User).count() == 1


def test_tc_a03_unknown_currency_is_rejected(client):
    res = client.post("/api/auth/register", json={**ANANYA, "home_currency": "XYZ"})
    assert res.status_code == 422
    assert "home_currency" in res.get_json()["error"]["details"]


def test_tc_a03b_implausible_dates_are_rejected(client):
    res = client.post(
        "/api/auth/register",
        json={**ANANYA, "study_end_date": "2025-09-01", "arrival_date": "2025-05-01"},
    )
    assert res.status_code == 422
    details = res.get_json()["error"]["details"]
    assert "study_end_date" in details and "arrival_date" in details


def test_tc_a03c_weak_password_and_unknown_field_are_rejected(client):
    res = client.post("/api/auth/register", json={**ANANYA, "password": "abcdefgh", "x": 1})
    assert res.status_code == 422
    details = res.get_json()["error"]["details"]
    assert "password" in details and "x" in details


def test_tc_a04_wrong_password_gives_generic_message(client, register):
    register()
    wrong = client.post(
        "/api/auth/login", json={"email": ANANYA["email"], "password": "Wrong#2026"}
    )
    unknown = client.post(
        "/api/auth/login", json={"email": "nobody@example.com", "password": "Wrong#2026"}
    )
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.get_json() == unknown.get_json()
    assert wrong.get_json()["error"]["message"] == "E-mail or password is incorrect."


def test_tc_a05_login_is_case_insensitive_for_email(client, register):
    register()
    res = client.post(
        "/api/auth/login", json={"email": " Ananya@Example.com ", "password": "Demo#2026"}
    )
    assert res.status_code == 200
    assert res.get_json()["expires_in"] == 3600


def test_tc_a06_change_password(client, auth):
    bad = client.post(
        "/api/auth/password",
        json={"current_password": "nope", "new_password": "NewPass2026"},
        headers=auth,
    )
    assert bad.status_code == 422
    ok = client.post(
        "/api/auth/password",
        json={"current_password": "Demo#2026", "new_password": "NewPass2026"},
        headers=auth,
    )
    assert ok.status_code == 204
    login = client.post(
        "/api/auth/login", json={"email": ANANYA["email"], "password": "NewPass2026"}
    )
    assert login.status_code == 200


def test_tc_a07_me_returns_age_but_no_password(client, auth):
    body = client.get("/api/me", headers=auth).get_json()
    assert body["full_name"] == "Ananya Rao"
    assert isinstance(body["age"], int) and body["age"] >= 25
    assert "password" not in str(body).lower()


def test_tc_sec01_password_is_hashed_and_never_returned(client):
    res = client.post("/api/auth/register", json=ANANYA)
    assert "Demo#2026" not in res.get_data(as_text=True)
    user = db.session.query(User).one()
    assert user.password_hash.startswith("$2b$")
    assert "Demo#2026" not in user.password_hash


def test_tc_sec02_logged_out_token_is_rejected(client, auth):
    assert client.get("/api/me", headers=auth).status_code == 200
    assert client.post("/api/auth/logout", headers=auth).status_code == 204
    res = client.get("/api/me", headers=auth)
    assert res.status_code == 401
    assert res.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_tc_sec02b_expired_token_is_rejected(app, client, register):
    from datetime import timedelta

    from flask_jwt_extended import create_access_token

    _, user = register()
    with app.test_request_context():
        token = create_access_token(identity=user["id"], expires_delta=timedelta(seconds=-1))
    res = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401
    assert res.get_json()["error"]["code"] == "SESSION_EXPIRED"


def test_tc_sec03_every_private_route_requires_a_token(app, client):
    """Scan the URL map: every non-public endpoint answers 401 without token."""
    checked = 0
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static" or rule.endpoint in PUBLIC_ENDPOINTS:
            continue
        url = rule.rule
        for arg in rule.arguments:
            url = url.replace(f"<uuid:{arg}>", "00000000-0000-0000-0000-000000000000")
        for method in rule.methods - {"HEAD", "OPTIONS"}:
            res = client.open(url, method=method, json={})
            assert res.status_code == 401, f"{method} {url} -> {res.status_code}"
            checked += 1
    assert checked >= 20
