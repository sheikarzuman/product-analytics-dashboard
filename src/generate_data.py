"""Synthetic e-commerce dataset generator.

Produces four CSVs in ``data/`` that are deliberately given *business
structure* (not random noise) so the dashboard's funnel, retention, churn,
cohort and channel analyses have real signal to surface:

* Acquisition **channels** differ in volume, signup quality and engagement.
* The **funnel** (visit -> signup -> add_to_cart -> purchase) has realistic,
  channel-dependent drop-off.
* **Retention** decays week-over-week from each user's signup cohort.
* **Revenue** trends upward over time with weekly seasonality.

Run from the project root:  ``python -m src.generate_data``
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# Configuration                                                               #
# --------------------------------------------------------------------------- #
SEED = 42
START = pd.Timestamp("2025-09-01")
END = pd.Timestamp("2026-06-28")  # inclusive last day of data
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Per-channel behaviour. `mix` sums to 1.0 across channels.
#   signup   = P(visitor signs up)
#   cart     = P(signed-up user adds to cart)
#   purchase = P(add_to_cart user purchases)
#   engage   = relative weekly-retention strength
#   aov      = average-order-value multiplier
CHANNELS: dict[str, dict[str, float]] = {
    "email":       {"mix": 0.12, "signup": 0.20, "cart": 0.55, "purchase": 0.50, "engage": 1.10, "aov": 1.10},
    "referral":    {"mix": 0.13, "signup": 0.15, "cart": 0.50, "purchase": 0.45, "engage": 1.00, "aov": 1.15},
    "organic":     {"mix": 0.22, "signup": 0.12, "cart": 0.45, "purchase": 0.40, "engage": 0.90, "aov": 1.00},
    "direct":      {"mix": 0.15, "signup": 0.10, "cart": 0.42, "purchase": 0.38, "engage": 0.80, "aov": 1.00},
    "paid_search": {"mix": 0.20, "signup": 0.09, "cart": 0.40, "purchase": 0.35, "engage": 0.70, "aov": 1.05},
    "social":      {"mix": 0.18, "signup": 0.06, "cart": 0.30, "purchase": 0.22, "engage": 0.50, "aov": 0.85},
}

COUNTRIES = ["US", "UK", "IN", "DE", "CA", "AU", "FR", "BR"]
COUNTRY_W = [0.34, 0.12, 0.16, 0.08, 0.08, 0.06, 0.08, 0.08]
DEVICES = ["mobile", "desktop", "tablet"]
DEVICE_W = [0.58, 0.36, 0.06]

CATEGORIES: dict[str, tuple[float, float]] = {
    # category: (min_price, max_price)
    "Electronics": (40, 600),
    "Apparel": (15, 120),
    "Home": (20, 250),
    "Beauty": (8, 80),
    "Sports": (15, 200),
    "Books": (6, 40),
}
WEEK_RETENTION_DECAY = 0.78  # base weekly survival before per-user noise


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #
def _random_times(rng: np.random.Generator, dates: pd.Series) -> pd.Series:
    """Attach a random intra-day time to a series of dates."""
    secs = rng.integers(0, 24 * 3600, size=len(dates))
    return dates + pd.to_timedelta(secs.astype("int64"), unit="s")


def _growth_weighted_dates(rng: np.random.Generator, n: int) -> pd.DatetimeIndex:
    """Sample `n` dates in [START, END] with mild upward growth over time."""
    span_days = (END - START).days
    # Linearly increasing weight => more recent days are likelier (business growth)
    weights = np.linspace(1.0, 2.2, span_days + 1)
    weights = weights / weights.sum()
    offsets = rng.choice(span_days + 1, size=n, p=weights)
    return START + pd.to_timedelta(offsets, unit="D")


# --------------------------------------------------------------------------- #
# Builders                                                                     #
# --------------------------------------------------------------------------- #
def build_products(rng: np.random.Generator, n_per_cat: int = 7) -> pd.DataFrame:
    rows = []
    pid = 1
    for cat, (lo, hi) in CATEGORIES.items():
        for i in range(n_per_cat):
            price = round(float(rng.uniform(lo, hi)), 2)
            rows.append(
                {
                    "product_id": pid,
                    "product_name": f"{cat} Item {i + 1}",
                    "category": cat,
                    "price": price,
                    "cost": round(price * float(rng.uniform(0.45, 0.70)), 2),
                }
            )
            pid += 1
    return pd.DataFrame(rows)


def build_users_and_events(
    rng: np.random.Generator, n_users_target: int
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generate visitors -> funnel events -> users -> ongoing activity.

    Returns (users_df, events_df, purchase_seed_df) where purchase_seed_df lists
    the first-purchase rows used downstream to build the orders table.
    """
    ch_names = list(CHANNELS)
    ch_mix = np.array([CHANNELS[c]["mix"] for c in ch_names])

    # Size the top of the funnel so signups ~= target users.
    weighted_signup = sum(CHANNELS[c]["mix"] * CHANNELS[c]["signup"] for c in ch_names)
    n_visitors = int(n_users_target / weighted_signup)

    visit_channel = rng.choice(ch_names, size=n_visitors, p=ch_mix)
    visit_date = _growth_weighted_dates(rng, n_visitors)
    visit_time = _random_times(rng, pd.Series(visit_date))

    signup_p = np.array([CHANNELS[c]["signup"] for c in visit_channel])
    signed = rng.random(n_visitors) < signup_p

    events: list[dict] = []
    sid = 1
    for i in range(n_visitors):
        events.append(
            {
                "session_id": sid,
                "user_id": np.nan,
                "event_type": "visit",
                "event_time": visit_time.iloc[i],
                "channel": visit_channel[i],
                "product_id": np.nan,
            }
        )
        sid += 1

    # Promote signers to users.
    signer_idx = np.where(signed)[0]
    n_users = len(signer_idx)
    user_ids = np.arange(1, n_users + 1)
    u_channel = visit_channel[signer_idx]
    u_signup_time = visit_time.iloc[signer_idx].reset_index(drop=True)

    # Map each user's signup back onto their visit session for funnel continuity.
    for uid, sess_i in zip(user_ids, signer_idx):
        events.append(
            {
                "session_id": int(sess_i + 1),
                "user_id": int(uid),
                "event_type": "signup",
                "event_time": visit_time.iloc[sess_i],
                "channel": visit_channel[sess_i],
                "product_id": np.nan,
            }
        )

    cart_p = np.array([CHANNELS[c]["cart"] for c in u_channel])
    add_cart = rng.random(n_users) < cart_p
    purch_p = np.array([CHANNELS[c]["purchase"] for c in u_channel])
    purchased = add_cart & (rng.random(n_users) < purch_p)

    next_sid = sid + n_users  # fresh session ids for funnel follow-up events
    purchase_seed: list[dict] = []
    for k in range(n_users):
        uid = int(user_ids[k])
        if add_cart[k]:
            t = u_signup_time.iloc[k] + pd.Timedelta(minutes=int(rng.integers(2, 90)))
            events.append(
                {
                    "session_id": next_sid,
                    "user_id": uid,
                    "event_type": "add_to_cart",
                    "event_time": t,
                    "channel": u_channel[k],
                    "product_id": np.nan,
                }
            )
            if purchased[k]:
                tp = t + pd.Timedelta(minutes=int(rng.integers(1, 60)))
                events.append(
                    {
                        "session_id": next_sid,
                        "user_id": uid,
                        "event_type": "purchase",
                        "event_time": tp,
                        "channel": u_channel[k],
                        "product_id": np.nan,
                    }
                )
                purchase_seed.append(
                    {"user_id": uid, "order_time": tp, "channel": u_channel[k]}
                )
            next_sid += 1

    # ----- Ongoing weekly activity (retention / churn / cohorts) ----------- #
    activity_rows: list[dict] = []
    repeat_purchases: list[dict] = []
    for k in range(n_users):
        uid = int(user_ids[k])
        ch = u_channel[k]
        engage = CHANNELS[ch]["engage"]
        # per-user latent stickiness
        stickiness = float(np.clip(rng.normal(engage, 0.25), 0.05, 1.6))
        signup_t = u_signup_time.iloc[k]
        weeks_available = max(int((END - signup_t).days // 7), 0)
        alive = purchased[k] or add_cart[k]  # engaged users carry on
        if not alive:
            continue
        for w in range(1, weeks_available + 1):
            p_active = stickiness * (WEEK_RETENTION_DECAY ** (w - 1)) * 0.6
            if rng.random() < min(p_active, 0.95):
                t = signup_t + pd.Timedelta(weeks=w, hours=int(rng.integers(0, 168)))
                if t > END:
                    continue
                activity_rows.append(
                    {
                        "session_id": next_sid,
                        "user_id": uid,
                        "event_type": "visit",
                        "event_time": t,
                        "channel": ch,
                        "product_id": np.nan,
                    }
                )
                next_sid += 1
                # some active weeks convert to a repeat purchase
                if rng.random() < 0.22:
                    repeat_purchases.append(
                        {"user_id": uid, "order_time": t, "channel": ch}
                    )

    events.extend(activity_rows)
    events_df = pd.DataFrame(events)
    events_df.insert(0, "event_id", np.arange(1, len(events_df) + 1))

    # ----- Users table ----------------------------------------------------- #
    last_active = (
        events_df.dropna(subset=["user_id"])
        .groupby("user_id")["event_time"]
        .max()
    )
    users_df = pd.DataFrame(
        {
            "user_id": user_ids,
            "signup_date": u_signup_time.values,
            "channel": u_channel,
            "country": rng.choice(COUNTRIES, size=n_users, p=COUNTRY_W),
            "device": rng.choice(DEVICES, size=n_users, p=DEVICE_W),
        }
    )
    users_df["last_active_date"] = users_df["user_id"].map(last_active)
    # "activated" = engaged beyond signup (any post-signup activity or a purchase)
    post_signup_active = (
        users_df["last_active_date"] > users_df["signup_date"] + pd.Timedelta(hours=1)
    )
    users_df["activated"] = (post_signup_active | pd.Series(purchased)).fillna(False)

    all_purchases = pd.DataFrame(purchase_seed + repeat_purchases)
    return users_df, events_df, all_purchases


def build_orders(
    rng: np.random.Generator, purchases: pd.DataFrame, products: pd.DataFrame
) -> pd.DataFrame:
    """Expand purchase events into order line items."""
    rows: list[dict] = []
    oid = 1
    prod_ids = products["product_id"].to_numpy()
    price_map = products.set_index("product_id")["price"].to_dict()
    # Popularity skew so some products dominate revenue (Pareto-ish).
    pop = rng.random(len(prod_ids)) ** 2
    pop = pop / pop.sum()
    for _, p in purchases.iterrows():
        n_items = int(rng.integers(1, 4))
        chosen = rng.choice(prod_ids, size=n_items, replace=False, p=pop)
        aov_mult = CHANNELS[p["channel"]]["aov"]
        for pid in chosen:
            qty = int(rng.integers(1, 4))
            unit = round(price_map[int(pid)] * aov_mult, 2)
            rows.append(
                {
                    "order_id": oid,
                    "user_id": int(p["user_id"]),
                    "order_date": p["order_time"],
                    "channel": p["channel"],
                    "product_id": int(pid),
                    "quantity": qty,
                    "unit_price": unit,
                    "revenue": round(unit * qty, 2),
                }
            )
        oid += 1
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Entry point                                                                  #
# --------------------------------------------------------------------------- #
def generate(n_users: int = 8000, out_dir: Path = DATA_DIR) -> None:
    rng = np.random.default_rng(SEED)
    out_dir.mkdir(parents=True, exist_ok=True)

    products = build_products(rng)
    users, events, purchases = build_users_and_events(rng, n_users)
    orders = build_orders(rng, purchases, products)

    products.to_csv(out_dir / "products.csv", index=False)
    users.to_csv(out_dir / "users.csv", index=False)
    events.to_csv(out_dir / "events.csv", index=False)
    orders.to_csv(out_dir / "orders.csv", index=False)

    print("Generated dataset in", out_dir)
    print(f"  products.csv : {len(products):>7,} rows")
    print(f"  users.csv    : {len(users):>7,} rows")
    print(f"  events.csv   : {len(events):>7,} rows")
    print(f"  orders.csv   : {len(orders):>7,} rows")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate synthetic e-commerce data.")
    ap.add_argument("--users", type=int, default=8000, help="approx. number of users")
    args = ap.parse_args()
    generate(n_users=args.users)
