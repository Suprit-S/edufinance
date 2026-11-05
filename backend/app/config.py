"""Application configuration.

All settings are read from environment variables so that the same image runs
unchanged in development, CI and production (NFR6). Defaults are safe for local
development only; production MUST override SECRET_KEY and JWT_SECRET_KEY.
"""

import os
from datetime import timedelta
from decimal import Decimal


def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, default))


class Config:
    # --- Core ---------------------------------------------------------------
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://edufinance:edufinance@localhost:5432/edufinance",
    )
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # --- Authentication (NFR4: session expires after 60 min) ----------------
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-jwt-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=_env_int("JWT_EXPIRES_MINUTES", 60))
    JWT_TOKEN_LOCATION = ["headers"]

    # --- CORS (only needed when the frontend runs on another origin) --------
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

    # --- Exchange rates (NFR5) ----------------------------------------------
    FX_API_URL = os.getenv("FX_API_URL", "https://open.er-api.com/v6/latest/{base}")
    FX_CACHE_HOURS = _env_int("FX_CACHE_HOURS", 24)
    FX_MAX_STALE_DAYS = _env_int("FX_MAX_STALE_DAYS", 7)
    FX_TIMEOUT_SECONDS = _env_int("FX_TIMEOUT_SECONDS", 5)

    # --- Business rules (kept in config, not code; see ADR-0006) -----------
    SETTLING_IN_DAYS_DEFAULT = _env_int("SETTLING_IN_DAYS_DEFAULT", 60)
    RUNWAY_HEALTHY_DAYS = _env_int("RUNWAY_HEALTHY_DAYS", 90)
    RUNWAY_OK_DAYS = _env_int("RUNWAY_OK_DAYS", 60)
    RUNWAY_WARNING_DAYS = _env_int("RUNWAY_WARNING_DAYS", 30)
    BURN_RATE_WINDOW_DAYS = _env_int("BURN_RATE_WINDOW_DAYS", 30)
    AFFORDABILITY_LOOKBACK_MONTHS = _env_int("AFFORDABILITY_LOOKBACK_MONTHS", 3)
    AFFORDABILITY_SAFETY_BUFFER = Decimal(os.getenv("AFFORDABILITY_SAFETY_BUFFER", "0.20"))


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://edufinance:edufinance@localhost:5432/edufinance_test",
    )
    # Never call the real exchange-rate API from tests.
    FX_API_URL = ""


CONFIGS = {"default": Config, "test": TestConfig}
