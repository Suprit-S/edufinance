"""Input validation (marshmallow). Invalid input raises ``ValidationError``,
which the error handler turns into HTTP 422 with field messages.

Unknown fields are rejected (marshmallow default ``RAISE``), so typos in API
calls are noticed immediately.
"""

import re
from decimal import ROUND_HALF_UP

from marshmallow import Schema, ValidationError, fields, validate, validates_schema

from app.extensions import db
from app.models import (
    CategoryKind,
    Country,
    Currency,
    Gender,
    PhaseType,
    WalletType,
)

NAME = validate.Length(min=1, max=60)
NOTE = validate.Length(max=255)


def _currency_exists(code: str) -> None:
    if db.session.get(Currency, code) is None:
        raise ValidationError("Unknown currency.")


def _country_exists(code: str) -> None:
    if db.session.get(Country, code) is None:
        raise ValidationError("Unknown country.")


def _password_policy(value: str) -> None:
    if not (re.search(r"[A-Za-z]", value) and re.search(r"\d", value)):
        raise ValidationError("Use at least one letter and one number.")


class CurrencyField(fields.String):
    """ISO 4217 code, upper-cased and checked against the master table."""

    def _deserialize(self, value, attr, data, **kwargs):
        code = super()._deserialize(value, attr, data, **kwargs).strip().upper()
        if not re.fullmatch(r"[A-Z]{3}", code):
            raise ValidationError("Use a 3-letter currency code, e.g. EUR.")
        _currency_exists(code)
        return code


class CountryField(fields.String):
    def _deserialize(self, value, attr, data, **kwargs):
        code = super()._deserialize(value, attr, data, **kwargs).strip().upper()
        if not re.fullmatch(r"[A-Z]{2}", code):
            raise ValidationError("Use a 2-letter country code, e.g. DE.")
        _country_exists(code)
        return code


def Amount(**kwargs):  # noqa: N802 - field factory
    """Positive money amount, rounded half-up to cents."""
    kwargs.setdefault("validate", validate.Range(min=0, min_inclusive=False, max=10**11))
    return fields.Decimal(places=2, rounding=ROUND_HALF_UP, as_string=True, **kwargs)


def RateValue(**kwargs):  # noqa: N802
    return fields.Decimal(
        places=8,
        rounding=ROUND_HALF_UP,
        as_string=True,
        validate=validate.Range(min=0, min_inclusive=False, max=10**9),
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Account
# ---------------------------------------------------------------------------
class ProfileSchema(Schema):
    full_name = fields.String(required=True, validate=validate.Length(min=2, max=120))
    date_of_birth = fields.Date(required=True)
    gender = fields.Enum(Gender, allow_none=True, load_default=None)
    home_currency = CurrencyField(required=True)
    base_currency = CurrencyField(required=True)
    destination_country = CountryField(required=True)
    planning_start_date = fields.Date(required=True)
    arrival_date = fields.Date(required=True)
    study_start_date = fields.Date(required=True)
    study_end_date = fields.Date(required=True)
    settling_in_days = fields.Integer(validate=validate.Range(min=0, max=365))


class RegisterSchema(ProfileSchema):
    email = fields.Email(required=True, validate=validate.Length(max=255))
    password = fields.String(
        required=True,
        load_only=True,
        validate=[validate.Length(min=8, max=128), _password_policy],
    )


class ProfileUpdateSchema(ProfileSchema):
    """All fields optional (used with partial=True); e-mail may change too."""

    email = fields.Email(validate=validate.Length(max=255))


class LoginSchema(Schema):
    email = fields.String(required=True, validate=validate.Length(min=1, max=255))
    password = fields.String(required=True, validate=validate.Length(min=1, max=128))


class PasswordChangeSchema(Schema):
    current_password = fields.String(required=True)
    new_password = fields.String(
        required=True, validate=[validate.Length(min=8, max=128), _password_policy]
    )


# ---------------------------------------------------------------------------
# Phases
# ---------------------------------------------------------------------------
class PhaseCreateSchema(Schema):
    name = fields.String(required=True, validate=NAME)
    phase_type = fields.Enum(PhaseType, load_default=PhaseType.CUSTOM)
    start_date = fields.Date(required=True)
    end_date = fields.Date(allow_none=True, load_default=None)

    @validates_schema
    def _range(self, data, **kwargs):
        if (
            data.get("end_date")
            and data.get("start_date")
            and data["end_date"] < data["start_date"]
        ):
            raise ValidationError({"end_date": ["Must not be before the start date."]})


class PhaseUpdateSchema(Schema):
    name = fields.String(validate=NAME)
    start_date = fields.Date()
    end_date = fields.Date(allow_none=True)


# ---------------------------------------------------------------------------
# Wallets and categories
# ---------------------------------------------------------------------------
class WalletSchema(Schema):
    name = fields.String(required=True, validate=NAME)
    currency_code = CurrencyField(required=True)
    wallet_type = fields.Enum(WalletType, required=True)
    opening_balance = fields.Decimal(
        places=2,
        rounding=ROUND_HALF_UP,
        as_string=True,
        load_default="0.00",
        validate=validate.Range(min=-(10**11), max=10**11),
    )
    opening_date = fields.Date(required=True)
    is_archived = fields.Boolean()


class CategorySchema(Schema):
    name = fields.String(required=True, validate=NAME)
    kind = fields.Enum(CategoryKind, required=True)
    group_name = fields.String(validate=validate.Length(max=40))
    counts_as_earned = fields.Boolean(load_default=True)


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------
class TransactionSchema(Schema):
    kind = fields.String(required=True, validate=validate.OneOf(["INCOME", "EXPENSE"]))
    wallet_id = fields.UUID(required=True)
    category_id = fields.UUID(required=True)
    amount = Amount(required=True)
    txn_date = fields.Date(required=True)
    note = fields.String(allow_none=True, validate=NOTE)
    phase_id = fields.UUID(allow_none=True, load_default=None)
    rate_to_base = RateValue(allow_none=True, load_default=None)
    rate_to_home = RateValue(allow_none=True, load_default=None)


class TransactionUpdateSchema(Schema):
    category_id = fields.UUID()
    amount = Amount()
    txn_date = fields.Date()
    note = fields.String(allow_none=True, validate=NOTE)
    phase_id = fields.UUID(allow_none=True)
    rate_to_base = RateValue(allow_none=True)
    rate_to_home = RateValue(allow_none=True)


class TransactionFilterSchema(Schema):
    wallet_id = fields.UUID()
    kind = fields.String(
        validate=validate.OneOf(["INCOME", "EXPENSE", "TRANSFER_IN", "TRANSFER_OUT"])
    )
    category_id = fields.UUID()
    phase_id = fields.UUID()
    date_from = fields.Date()
    date_to = fields.Date()
    q = fields.String(validate=validate.Length(max=100))
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(load_default=50, validate=validate.Range(min=1, max=200))


class RateQuerySchema(Schema):
    from_ = CurrencyField(required=True, data_key="from")
    to = CurrencyField(required=True)
    date = fields.Date()
