"""Performance check for NFR-01 (test case TC-P01).

Creates a temporary user with the realistic demo history plus extra small
expenses until the user owns 2,000 transactions, then calls the heaviest
read endpoints repeatedly through the Flask test client and prints the
median and 95th-percentile response times. The user is deleted afterwards.

Run from the backend folder against a migrated, seeded database:

    python scripts/perf_dashboard.py            # 30 calls per endpoint
    python scripts/perf_dashboard.py --runs 50

Target (NFR-01): p95 <= 2,000 ms for the dashboard and the reports.
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from flask_jwt_extended import create_access_token  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Transaction, User, Wallet  # noqa: E402
from app.seed import demo_data  # noqa: E402
from app.services import account_service, auth_service  # noqa: E402

PERF_EMAIL = "perf-check@edufinance.app"
TARGET_TRANSACTIONS = 2000
TARGET_P95_MS = 2000
ENDPOINTS = [
    "/api/dashboard",
    "/api/reports?period=MONTH",
    "/api/reports?period=LIFETIME",
    "/api/reports/costs",
    "/api/reports/net-worth",
    "/api/reports/loans",
    "/api/transactions?per_page=50",
]
FILLER = ["Groceries", "Eating out", "Public transport", "Personal care", "Other expense"]


def build_user(today: date) -> User:
    old = db.session.scalar(select(User).where(User.email == PERF_EMAIL))
    if old:
        account_service.delete_all_data(old.id)
    demo_data.store_rate_history(demo_data.RATE_HISTORY_START, today)
    user = auth_service.register({**demo_data.PROFILE, "email": PERF_EMAIL})
    demo = demo_data._Demo(user, today)
    demo_data.build(user, today)
    # reuse the wallets the demo created
    demo.w = {
        w.name: w for w in db.session.scalars(select(Wallet).where(Wallet.user_id == user.id))
    }
    daily = next(name for name in demo.w if name.startswith("Daily"))

    count = _count(user)
    day, i = date(2025, 10, 1), 0
    while count < TARGET_TRANSACTIONS:
        demo.spend(daily, day, FILLER[i % len(FILLER)], Decimal("1.50") + i % 7, "perf filler")
        count += 1
        i += 1
        day += timedelta(days=1)
        if day > today:
            day = date(2025, 10, 1)
    db.session.commit()
    return user


def _count(user: User) -> int:
    return db.session.scalar(
        select(func.count()).select_from(Transaction).where(Transaction.user_id == user.id)
    )


def p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, round(0.95 * len(ordered)) - 1)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", type=int, default=30)
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        started = time.perf_counter()
        user = build_user(date.today())
        print(f"Prepared {_count(user)} transactions in {time.perf_counter() - started:.1f} s")
        token = create_access_token(identity=str(user.id))
        headers = {"Authorization": f"Bearer {token}"}
        client = app.test_client()

        failed = False
        print(f"\n{'Endpoint':38} {'median ms':>10} {'p95 ms':>8}  result")
        for url in ENDPOINTS:
            client.get(url, headers=headers)  # warm-up (rate cache, query plans)
            times = []
            for _ in range(args.runs):
                t0 = time.perf_counter()
                res = client.get(url, headers=headers)
                times.append((time.perf_counter() - t0) * 1000)
                if res.status_code != 200:
                    print(f"{url}: HTTP {res.status_code}")
                    return 1
            ok = p95(times) <= TARGET_P95_MS
            failed |= not ok
            print(
                f"{url:38} {statistics.median(times):10.0f} {p95(times):8.0f}  "
                f"{'PASS' if ok else 'FAIL'}"
            )

        account_service.delete_all_data(user.id)
        db.session.commit()
        print(f"\nNFR-01 (p95 <= {TARGET_P95_MS} ms): {'FAIL' if failed else 'PASS'}")
        return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
