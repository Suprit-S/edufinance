"""Exact decimal helpers used by every financial calculation.

Rules (ADR-0002):
* amounts are rounded to 2 decimals with ROUND_HALF_UP (commercial rounding);
* exchange rates keep 8 decimals;
* never construct a Decimal from a float (``Decimal(0.1)`` is not 0.1).
"""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

CENT = Decimal("0.01")
RATE_STEP = Decimal("0.00000001")
ZERO = Decimal("0.00")


def to_decimal(value) -> Decimal:
    """Convert int/str/Decimal to Decimal. Floats are rejected on purpose."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool) or isinstance(value, float):
        raise TypeError("Use str or Decimal for money, never float/bool.")
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Not a valid number: {value!r}") from exc


def money(value) -> Decimal:
    """Round to cents (2 decimals, half-up)."""
    return to_decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def rate(value) -> Decimal:
    """Round an exchange rate to 8 decimals (half-up)."""
    return to_decimal(value).quantize(RATE_STEP, rounding=ROUND_HALF_UP)


def convert(amount, fx_rate) -> Decimal:
    """Convert ``amount`` with ``fx_rate`` (1 source unit = fx_rate target units)."""
    return money(to_decimal(amount) * to_decimal(fx_rate))


def invert_rate(fx_rate) -> Decimal:
    """1 / rate, e.g. EUR->INR 106 becomes INR->EUR 0.00943396."""
    r = to_decimal(fx_rate)
    if r <= 0:
        raise ValueError("Exchange rate must be positive.")
    return rate(Decimal(1) / r)
