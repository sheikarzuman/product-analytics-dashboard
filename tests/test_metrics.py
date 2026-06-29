"""Exact-value unit tests for the metrics module."""
from __future__ import annotations

import pandas as pd

from src import metrics as m


# ---- Headline KPIs --------------------------------------------------------- #
def test_kpis(users, orders):
    k = m.kpi_summary(users, orders)
    assert k.total_users == 4
    assert k.active_users == 3
    assert k.activation_rate == 75.0
    assert k.total_orders == 4              # distinct order_ids
    assert k.total_revenue == 230.0
    assert k.average_order_value == 57.5    # 230 / 4
    assert k.paying_users == 3
    assert k.conversion_rate == 75.0        # 3 / 4


# ---- Funnel ---------------------------------------------------------------- #
def test_funnel_counts(events):
    f = m.funnel_counts(events)
    assert list(f["count"]) == [10, 4, 3, 3]
    assert f.iloc[0]["step_conversion"] == 100.0
    # monotonically non-increasing
    assert (f["count"].diff().dropna() <= 0).all()


def test_biggest_dropoff(events):
    s_from, s_to, drop = m.biggest_dropoff(events)
    assert (s_from, s_to) == ("Visit", "Signup")
    assert drop == 60.0                      # 10 -> 4 == 40% survive


# ---- Traffic --------------------------------------------------------------- #
def test_traffic_source(users, orders, events):
    t = m.traffic_source_performance(users, orders, events)
    top = t.iloc[0]
    assert top["channel"] == "email"
    assert top["revenue_per_visitor"] == 42.0   # 210 / 5
    assert top["signup_rate_%"] == 40.0         # 2 / 5


# ---- Product / category ---------------------------------------------------- #
def test_category_sales(orders, products):
    c = m.category_sales(orders, products)
    assert c["revenue"].sum() == 230.0
    assert abs(c["revenue_share_%"].sum() - 100.0) < 0.5
    top = m.product_sales(orders, products).iloc[0]
    assert top["product_name"] == "A1"          # product 1 = 150 revenue
    assert top["revenue"] == 150.0


# ---- Retention / churn ----------------------------------------------------- #
def test_cohort_retention(users, events):
    ret = m.cohort_retention(users, events, max_weeks=3)
    assert (ret[0].dropna() == 100.0).all()     # week 0 always 100%
    assert ret[1].iloc[0] == 25.0               # only user 1 returns -> 1/4


def test_churn_summary(users):
    cs = m.churn_summary(users)                 # ref = max last_active = REF
    assert cs["active"] + cs["at_risk"] + cs["churned"] == 4
    assert cs["churned"] == 2                    # users 3 and 4
    assert cs["churn_rate"] == 50.0
