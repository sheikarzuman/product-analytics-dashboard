"""Core business metrics.

Every function is *pure*: it takes DataFrame(s) and returns a number or a small
DataFrame, with no I/O and no Streamlit dependency. That makes them trivial to
unit-test and reuse across pages.

Glossary
--------
Conversion rate : share of signed-up users who placed at least one paid order.
AOV             : average order value = total revenue / number of orders.
Active user     : a user flagged `activated` (engaged beyond signup).
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.utils import week_floor


# --------------------------------------------------------------------------- #
# Headline KPIs                                                                #
# --------------------------------------------------------------------------- #
def total_users(users: pd.DataFrame) -> int:
    return int(len(users))


def active_users(users: pd.DataFrame) -> int:
    return int(users["activated"].sum())


def total_orders(orders: pd.DataFrame) -> int:
    return int(orders["order_id"].nunique())


def total_revenue(orders: pd.DataFrame) -> float:
    return float(orders["revenue"].sum())


def average_order_value(orders: pd.DataFrame) -> float:
    n = total_orders(orders)
    return float(orders["revenue"].sum() / n) if n else 0.0


def paying_users(orders: pd.DataFrame) -> int:
    return int(orders["user_id"].nunique())


def conversion_rate(users: pd.DataFrame, orders: pd.DataFrame) -> float:
    """Paying users as a percentage of all signed-up users."""
    n = total_users(users)
    return float(paying_users(orders) / n * 100) if n else 0.0


def activation_rate(users: pd.DataFrame) -> float:
    n = total_users(users)
    return float(active_users(users) / n * 100) if n else 0.0


@dataclass(frozen=True)
class KpiSummary:
    """Bundle of headline numbers consumed by the KPI cards."""

    total_users: int
    active_users: int
    activation_rate: float
    conversion_rate: float
    total_revenue: float
    total_orders: int
    average_order_value: float
    paying_users: int


def kpi_summary(users: pd.DataFrame, orders: pd.DataFrame) -> KpiSummary:
    return KpiSummary(
        total_users=total_users(users),
        active_users=active_users(users),
        activation_rate=activation_rate(users),
        conversion_rate=conversion_rate(users, orders),
        total_revenue=total_revenue(orders),
        total_orders=total_orders(orders),
        average_order_value=average_order_value(orders),
        paying_users=paying_users(orders),
    )


# --------------------------------------------------------------------------- #
# Weekly trends (used by the Executive Overview + Trends pages)               #
# --------------------------------------------------------------------------- #
def weekly_signups(users: pd.DataFrame) -> pd.DataFrame:
    df = users.copy()
    df["week"] = week_floor(df["signup_date"])
    out = df.groupby("week").size().reset_index(name="signups")
    return out.sort_values("week")


def weekly_revenue(orders: pd.DataFrame) -> pd.DataFrame:
    df = orders.copy()
    df["week"] = week_floor(df["order_date"])
    out = (
        df.groupby("week")
        .agg(revenue=("revenue", "sum"), orders=("order_id", "nunique"))
        .reset_index()
    )
    return out.sort_values("week")


def revenue_by_channel(orders: pd.DataFrame) -> pd.DataFrame:
    out = (
        orders.groupby("channel")
        .agg(revenue=("revenue", "sum"), orders=("order_id", "nunique"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    return out


# --------------------------------------------------------------------------- #
# Conversion funnel (Visit -> Signup -> Add to Cart -> Purchase)              #
# --------------------------------------------------------------------------- #
FUNNEL_STAGES: list[str] = ["Visit", "Signup", "Add to Cart", "Purchase"]


def _stage_counts(events: pd.DataFrame) -> dict[str, int]:
    """Distinct-entity counts for each acquisition-funnel stage.

    Top-of-funnel `Visit` counts only *acquisition* visits (anonymous, i.e.
    no user_id). Post-signup engagement is also logged as `visit` events but
    carries a user_id, so excluding those keeps the funnel honest.
    """
    visits = events[(events["event_type"] == "visit") & (events["user_id"].isna())]
    return {
        "Visit": int(visits["session_id"].nunique()),
        "Signup": int((events["event_type"] == "signup").sum()),
        "Add to Cart": int(
            events.loc[events["event_type"] == "add_to_cart", "user_id"].nunique()
        ),
        "Purchase": int(
            events.loc[events["event_type"] == "purchase", "user_id"].nunique()
        ),
    }


def funnel_counts(events: pd.DataFrame) -> pd.DataFrame:
    """Overall funnel with conversion from the top and from the previous step."""
    counts = _stage_counts(events)
    top = counts["Visit"] or 1
    rows = []
    prev: int | None = None
    for stage in FUNNEL_STAGES:
        c = counts[stage]
        rows.append(
            {
                "stage": stage,
                "count": c,
                "pct_of_top": round(c / top * 100, 2),
                "step_conversion": round(c / prev * 100, 2) if prev else 100.0,
            }
        )
        prev = c
    return pd.DataFrame(rows)


def funnel_by_channel(events: pd.DataFrame) -> pd.DataFrame:
    """Funnel stage counts per acquisition channel (+ visit→purchase rate)."""
    rows = []
    for ch, grp in events.groupby("channel"):
        counts = _stage_counts(grp)
        visit = counts["Visit"] or 1
        rows.append(
            {
                "channel": ch,
                **counts,
                "visit_to_purchase_%": round(counts["Purchase"] / visit * 100, 2),
                "signup_to_purchase_%": round(
                    counts["Purchase"] / (counts["Signup"] or 1) * 100, 2
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("Purchase", ascending=False)


def biggest_dropoff(events: pd.DataFrame) -> tuple[str, str, float]:
    """Return (from_stage, to_stage, drop_pct) for the largest funnel leak."""
    f = funnel_counts(events)
    worst_from, worst_to, worst_drop = "", "", -1.0
    for i in range(1, len(f)):
        drop = 100 - f.iloc[i]["step_conversion"]
        if drop > worst_drop:
            worst_drop = drop
            worst_from = f.iloc[i - 1]["stage"]
            worst_to = f.iloc[i]["stage"]
    return worst_from, worst_to, round(worst_drop, 1)


# --------------------------------------------------------------------------- #
# Traffic-source performance                                                  #
# --------------------------------------------------------------------------- #
def traffic_source_performance(
    users: pd.DataFrame, orders: pd.DataFrame, events: pd.DataFrame
) -> pd.DataFrame:
    """Per-channel acquisition economics, ranked by revenue per visitor."""
    visits = events[(events["event_type"] == "visit") & (events["user_id"].isna())]
    visitors = visits.groupby("channel")["session_id"].nunique()
    signups = users.groupby("channel").size()
    paying = orders.groupby("channel")["user_id"].nunique()
    revenue = orders.groupby("channel")["revenue"].sum()
    n_orders = orders.groupby("channel")["order_id"].nunique()

    df = pd.DataFrame({"visitors": visitors}).fillna(0)
    df["signups"] = signups
    df["paying_users"] = paying
    df["revenue"] = revenue
    df["orders"] = n_orders
    df = df.fillna(0)

    df["signup_rate_%"] = (df["signups"] / df["visitors"].replace(0, pd.NA) * 100).round(2)
    df["visit_to_paid_%"] = (df["paying_users"] / df["visitors"].replace(0, pd.NA) * 100).round(2)
    df["aov"] = (df["revenue"] / df["orders"].replace(0, pd.NA)).round(2)
    df["revenue_per_visitor"] = (df["revenue"] / df["visitors"].replace(0, pd.NA)).round(2)

    return df.reset_index().sort_values("revenue_per_visitor", ascending=False)


# --------------------------------------------------------------------------- #
# Retention, churn & cohorts                                                  #
# --------------------------------------------------------------------------- #
def _user_week_activity(
    users: pd.DataFrame, events: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (activity_with_week_index, user_cohorts).

    `week_index` = whole weeks between an event and the user's signup week
    (0 = signup week). Only signed-up users' events are considered.
    """
    ev = events.dropna(subset=["user_id"]).copy()
    ev["user_id"] = ev["user_id"].astype(int)
    ev["ev_week"] = week_floor(ev["event_time"])

    cohorts = users[["user_id", "signup_date"]].copy()
    cohorts["cohort"] = week_floor(cohorts["signup_date"])

    ev = ev.merge(
        cohorts[["user_id", "signup_date", "cohort"]], on="user_id", how="inner"
    )
    # Weeks since each user's own signup (not calendar weeks) avoids
    # boundary smearing for users who signed up mid-week.
    ev["week_index"] = (ev["event_time"] - ev["signup_date"]).dt.days // 7
    ev = ev[ev["week_index"] >= 0]
    return ev, cohorts


def cohort_retention(
    users: pd.DataFrame, events: pd.DataFrame, max_weeks: int = 8
) -> pd.DataFrame:
    """Cohort (signup week) × weeks-since-signup retention percentages."""
    ev, cohorts = _user_week_activity(users, events)
    sizes = cohorts.groupby("cohort").size()
    act = (
        ev[ev["week_index"] <= max_weeks]
        .groupby(["cohort", "week_index"])["user_id"]
        .nunique()
        .reset_index()
    )
    pivot = act.pivot(index="cohort", columns="week_index", values="user_id")
    ret = pivot.div(sizes, axis=0) * 100
    return ret.round(1)


def retention_curve(
    users: pd.DataFrame, events: pd.DataFrame, max_weeks: int = 8
) -> pd.DataFrame:
    """Average retention by week-since-signup across all cohorts."""
    ret = cohort_retention(users, events, max_weeks)
    curve = ret.mean(axis=0, skipna=True).reset_index()
    curve.columns = ["week_index", "retention_%"]
    curve["retention_%"] = curve["retention_%"].round(1)
    return curve.sort_values("week_index")


def churn_summary(
    users: pd.DataFrame,
    reference_date: pd.Timestamp | None = None,
    risk_days: int = 14,
    churn_days: int = 30,
) -> dict:
    """Segment users by recency into active / at-risk / churned."""
    ref = reference_date or users["last_active_date"].max()
    days = (ref - users["last_active_date"]).dt.days
    churned = days > churn_days
    at_risk = (days > risk_days) & (days <= churn_days)
    active = days <= risk_days
    n = len(users) or 1
    return {
        "reference_date": ref,
        "active": int(active.sum()),
        "at_risk": int(at_risk.sum()),
        "churned": int(churned.sum()),
        "active_rate": round(active.sum() / n * 100, 1),
        "at_risk_rate": round(at_risk.sum() / n * 100, 1),
        "churn_rate": round(churned.sum() / n * 100, 1),
    }


def churn_by_channel(
    users: pd.DataFrame,
    reference_date: pd.Timestamp | None = None,
    churn_days: int = 30,
) -> pd.DataFrame:
    """Churn rate per acquisition channel."""
    ref = reference_date or users["last_active_date"].max()
    df = users.copy()
    df["days_inactive"] = (ref - df["last_active_date"]).dt.days
    df["churned"] = df["days_inactive"] > churn_days
    out = (
        df.groupby("channel")
        .agg(users=("user_id", "size"), churned=("churned", "sum"))
        .reset_index()
    )
    out["churn_rate_%"] = (out["churned"] / out["users"] * 100).round(1)
    return out.sort_values("churn_rate_%", ascending=False)


def retarget_candidates(
    users: pd.DataFrame,
    orders: pd.DataFrame,
    reference_date: pd.Timestamp | None = None,
    risk_days: int = 14,
    churn_days: int = 30,
    top_n: int = 25,
) -> pd.DataFrame:
    """High-value at-risk users (lapsing buyers) worth a win-back campaign."""
    ref = reference_date or users["last_active_date"].max()
    rev = orders.groupby("user_id")["revenue"].sum().rename("lifetime_revenue")
    df = users.merge(rev, on="user_id", how="left")
    df["lifetime_revenue"] = df["lifetime_revenue"].fillna(0.0)
    df["days_inactive"] = (ref - df["last_active_date"]).dt.days
    at_risk = df[(df["days_inactive"] > risk_days) & (df["days_inactive"] <= churn_days)]
    cols = ["user_id", "channel", "country", "days_inactive", "lifetime_revenue"]
    return (
        at_risk.sort_values("lifetime_revenue", ascending=False)[cols]
        .head(top_n)
        .reset_index(drop=True)
    )


# --------------------------------------------------------------------------- #
# Product & category sales                                                    #
# --------------------------------------------------------------------------- #
def product_sales(orders: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Revenue, units and orders per product (descending by revenue)."""
    df = orders.merge(
        products[["product_id", "product_name", "category"]],
        on="product_id", how="left",
    )
    out = (
        df.groupby(["product_id", "product_name", "category"])
        .agg(revenue=("revenue", "sum"), units=("quantity", "sum"),
             orders=("order_id", "nunique"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    return out


def category_sales(orders: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Revenue, units and revenue share per category."""
    df = orders.merge(products[["product_id", "category"]], on="product_id", how="left")
    out = (
        df.groupby("category")
        .agg(revenue=("revenue", "sum"), units=("quantity", "sum"),
             orders=("order_id", "nunique"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    out["revenue_share_%"] = (out["revenue"] / out["revenue"].sum() * 100).round(1)
    return out


def top_products(orders: pd.DataFrame, products: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    return product_sales(orders, products).head(n)


# --------------------------------------------------------------------------- #
# RFM customer segmentation                                                   #
# --------------------------------------------------------------------------- #
def _rfm_segment(r: int, f: int, m: int) -> str:
    """Map R/F (1–4) scores to a human-readable segment."""
    if r >= 3 and f >= 3:
        return "Champions"
    if r >= 3 and f >= 2:
        return "Loyal"
    if r >= 3:
        return "New / Recent"
    if r == 2 and f >= 3:
        return "At Risk"
    if f >= 3:
        return "At Risk"
    if r <= 2 and f <= 2:
        return "Hibernating"
    return "Needs Attention"


def rfm_table(
    users: pd.DataFrame, orders: pd.DataFrame,
    reference_date: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Compute Recency/Frequency/Monetary scores and a segment per buyer."""
    ref = reference_date or orders["order_date"].max()
    agg = (
        orders.groupby("user_id")
        .agg(
            recency=("order_date", lambda s: int((ref - s.max()).days)),
            frequency=("order_id", "nunique"),
            monetary=("revenue", "sum"),
        )
        .reset_index()
    )
    # Quartile scores. Lower recency = better, so reverse its labels.
    agg["R"] = pd.qcut(agg["recency"], 4, labels=[4, 3, 2, 1], duplicates="drop").astype(int)
    agg["F"] = pd.qcut(
        agg["frequency"].rank(method="first"), 4, labels=[1, 2, 3, 4]
    ).astype(int)
    agg["M"] = pd.qcut(agg["monetary"], 4, labels=[1, 2, 3, 4], duplicates="drop").astype(int)
    agg["segment"] = agg.apply(lambda x: _rfm_segment(x["R"], x["F"], x["M"]), axis=1)
    # attach channel for downstream analysis
    agg = agg.merge(users[["user_id", "channel"]], on="user_id", how="left")
    return agg


def segment_summary(rfm: pd.DataFrame) -> pd.DataFrame:
    """Customer counts and value per RFM segment."""
    out = (
        rfm.groupby("segment")
        .agg(customers=("user_id", "nunique"),
             avg_monetary=("monetary", "mean"),
             total_revenue=("monetary", "sum"))
        .reset_index()
        .sort_values("total_revenue", ascending=False)
    )
    out["avg_monetary"] = out["avg_monetary"].round(2)
    out["revenue_share_%"] = (out["total_revenue"] / out["total_revenue"].sum() * 100).round(1)
    return out
