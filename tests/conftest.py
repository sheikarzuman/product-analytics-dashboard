"""Deterministic, hand-built fixtures with known expected values.

Using tiny in-memory tables (rather than the generated CSVs) lets the tests
assert exact numbers, so a regression in any metric fails loudly.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

BASE = pd.Timestamp("2026-01-01 10:00")
REF = pd.Timestamp("2026-06-28")  # max last_active_date


@pytest.fixture
def products() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"product_id": 1, "product_name": "A1", "category": "A", "price": 50, "cost": 25},
            {"product_id": 2, "product_name": "B1", "category": "B", "price": 20, "cost": 10},
        ]
    )


@pytest.fixture
def users() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"user_id": 1, "signup_date": BASE, "channel": "email", "country": "US",
             "device": "mobile", "last_active_date": REF, "activated": True},
            {"user_id": 2, "signup_date": BASE, "channel": "social", "country": "US",
             "device": "desktop", "last_active_date": pd.Timestamp("2026-06-20"), "activated": True},
            {"user_id": 3, "signup_date": BASE, "channel": "email", "country": "UK",
             "device": "mobile", "last_active_date": pd.Timestamp("2026-05-01"), "activated": True},
            {"user_id": 4, "signup_date": BASE, "channel": "social", "country": "US",
             "device": "mobile", "last_active_date": BASE, "activated": False},
        ]
    )


@pytest.fixture
def orders() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"order_id": 101, "user_id": 1, "order_date": pd.Timestamp("2026-02-01"),
             "channel": "email", "product_id": 1, "quantity": 1, "unit_price": 50, "revenue": 50},
            {"order_id": 101, "user_id": 1, "order_date": pd.Timestamp("2026-02-01"),
             "channel": "email", "product_id": 2, "quantity": 1, "unit_price": 50, "revenue": 50},
            {"order_id": 102, "user_id": 1, "order_date": pd.Timestamp("2026-03-01"),
             "channel": "email", "product_id": 2, "quantity": 1, "unit_price": 30, "revenue": 30},
            {"order_id": 103, "user_id": 2, "order_date": pd.Timestamp("2026-02-10"),
             "channel": "social", "product_id": 1, "quantity": 1, "unit_price": 20, "revenue": 20},
            {"order_id": 104, "user_id": 3, "order_date": pd.Timestamp("2026-02-15"),
             "channel": "email", "product_id": 1, "quantity": 1, "unit_price": 80, "revenue": 80},
        ]
    )


@pytest.fixture
def events() -> pd.DataFrame:
    rows: list[dict] = []
    eid = sid = 1

    def add(user_id, etype, when, ch):
        nonlocal eid, sid
        rows.append({"event_id": eid, "session_id": sid, "user_id": user_id,
                     "event_type": etype, "event_time": when, "channel": ch,
                     "product_id": np.nan})
        eid += 1
        sid += 1

    # 5 anonymous acquisition visits per channel (top of funnel = 10)
    for ch, n in [("email", 5), ("social", 5)]:
        for _ in range(n):
            add(np.nan, "visit", BASE, ch)

    signup_ch = {1: "email", 2: "social", 3: "email", 4: "social"}
    for uid, ch in signup_ch.items():           # 4 signups
        add(uid, "signup", BASE, ch)
    for uid in (1, 2, 3):                        # 3 add_to_cart
        add(uid, "add_to_cart", BASE, signup_ch[uid])
    for uid in (1, 2, 3):                        # 3 purchases
        add(uid, "purchase", BASE, signup_ch[uid])

    # user 1 returns in week 1 and week 2 (for retention)
    add(1, "visit", BASE + pd.Timedelta(days=8), "email")
    add(1, "visit", BASE + pd.Timedelta(days=15), "email")
    return pd.DataFrame(rows)
