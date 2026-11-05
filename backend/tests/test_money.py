"""Unit tests for exact money arithmetic (test cases TC-M01..TC-M07)."""

from decimal import Decimal

import pytest

from app.services.money import convert, invert_rate, money, rate, to_decimal


def test_tc_m01_money_rounds_half_up():
    assert money("2.345") == Decimal("2.35")
    assert money("2.344") == Decimal("2.34")
    assert money("-2.345") == Decimal("-2.35")


def test_tc_m02_float_is_rejected():
    with pytest.raises(TypeError):
        to_decimal(0.1)


def test_tc_m03_invalid_number_is_rejected():
    with pytest.raises(ValueError):
        to_decimal("12,50€")


def test_tc_m04_convert_inr_to_eur():
    # 14,000 INR at 1 INR = 0.00940512 EUR -> 131.67 EUR
    assert convert("14000", "0.00940512") == Decimal("131.67")


def test_tc_m05_invert_rate():
    # 1 EUR = 106 INR  ->  1 INR = 0.00943396 EUR
    assert invert_rate("106") == Decimal("0.00943396")


def test_tc_m06_invert_rate_rejects_zero():
    with pytest.raises(ValueError):
        invert_rate("0")


def test_tc_m07_rate_keeps_eight_decimals():
    assert rate("0.123456789") == Decimal("0.12345679")
    # 0.1 + 0.2 is exact with Decimal (it is 0.30000000000000004 with float)
    assert money(to_decimal("0.1") + to_decimal("0.2")) == Decimal("0.30")
