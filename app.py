"""Product Analytics Dashboard — Streamlit entry point.

Run:  streamlit run app.py

This file owns page config and the Executive Overview. Additional analytics
pages (Funnel, Trends, Retention, etc.) live under `pages/` and Streamlit
auto-discovers them into the sidebar.
"""
from __future__ import annotations

import streamlit as st

from src.charts import COLORS, area, horizontal_bar, vertical_bar
from src.data_loader import load_orders, load_users
from src.metrics import (
    kpi_summary,
    revenue_by_channel,
    weekly_revenue,
    weekly_signups,
)
from src.utils import format_currency, format_number, format_percent

st.set_page_config(
    page_title="Product Analytics Dashboard",
    page_icon="📊",
    layout="wide",
)


def render_kpi_cards() -> None:
    users = load_users()
    orders = load_orders()
    k = kpi_summary(users, orders)

    st.subheader("Key metrics")
    row1 = st.columns(3)
    row1[0].metric("Total Users", format_number(k.total_users))
    row1[1].metric("Active Users", format_number(k.active_users),
                   help="Users engaged beyond signup")
    row1[2].metric("Conversion Rate", format_percent(k.conversion_rate))

    row2 = st.columns(3)
    row2[0].metric("Revenue", format_currency(k.total_revenue))
    row2[1].metric("Avg Order Value", format_currency(k.average_order_value))
    row2[2].metric("Total Orders", format_number(k.total_orders))


def render_trends() -> None:
    users, orders = load_users(), load_orders()
    st.subheader("Weekly trends")
    left, right = st.columns(2)

    fig_rev = area(weekly_revenue(orders), "week", "revenue", title="Revenue by week",
                   labels={"week": "", "revenue": "Revenue ($)"})
    left.plotly_chart(fig_rev)

    fig_sign = vertical_bar(weekly_signups(users), "week", "signups",
                            title="Signups by week",
                            labels={"week": "", "signups": "Signups"})
    right.plotly_chart(fig_sign)


def render_channel_mix() -> None:
    orders = load_orders()
    st.subheader("Revenue by acquisition channel")
    fig = horizontal_bar(revenue_by_channel(orders), "revenue", "channel",
                         color=COLORS["indigo"],
                         labels={"revenue": "Revenue ($)", "channel": ""})
    st.plotly_chart(fig)


def main() -> None:
    st.title("📊 Product Analytics Dashboard")
    st.caption("Executive Overview · synthetic D2C / e-commerce data · "
               "use the sidebar to navigate analytics pages.")
    render_kpi_cards()
    st.divider()
    render_trends()
    st.divider()
    render_channel_mix()


if __name__ == "__main__":
    main()
