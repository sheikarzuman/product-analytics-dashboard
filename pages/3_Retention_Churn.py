"""Retention & Churn Analysis page: cohorts, retention curve, churn segments."""
from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data_loader import load_events, load_orders, load_users
from src.metrics import (
    churn_by_channel,
    churn_summary,
    cohort_retention,
    retarget_candidates,
    retention_curve,
)
from src.utils import format_currency, format_number, format_percent

st.set_page_config(page_title="Retention & Churn", page_icon="🔁", layout="wide")
st.title("🔁 Retention & Churn Analysis")
st.caption("Do we keep the users we acquire? Where and when do they lapse?")

users, events, orders = load_users(), load_events(), load_orders()

with st.sidebar:
    st.header("Churn settings")
    risk_days = st.slider("At-risk after (days inactive)", 7, 30, 14)
    churn_days = st.slider("Churned after (days inactive)", 21, 90, 30)
    max_weeks = st.slider("Cohort weeks to show", 4, 12, 8)

churn = churn_summary(users, risk_days=risk_days, churn_days=churn_days)

# ---- Churn KPIs ------------------------------------------------------------ #
st.subheader("User health")
c = st.columns(4)
c[0].metric("Active", format_number(churn["active"]), help=f"≤{risk_days}d since last activity")
c[1].metric("At risk", format_number(churn["at_risk"]), help=f"{risk_days}–{churn_days}d inactive")
c[2].metric("Churned", format_number(churn["churned"]), help=f">{churn_days}d inactive")
c[3].metric("Churn rate", format_percent(churn["churn_rate"]))
st.caption(f"Reference date: {churn['reference_date'].date()}")

st.divider()

# ---- Retention curve ------------------------------------------------------- #
left, right = st.columns(2)
curve = retention_curve(users, events, max_weeks=max_weeks)
fig_curve = px.line(
    curve, x="week_index", y="retention_%", markers=True, template="plotly_white",
    title="Average retention curve", labels={"week_index": "Weeks since signup", "retention_%": "Retention (%)"},
)
fig_curve.update_traces(line_color="#2563eb")
left.plotly_chart(fig_curve)

# ---- Churn by channel ------------------------------------------------------ #
cbc = churn_by_channel(users, churn_days=churn_days)
fig_cbc = px.bar(
    cbc.sort_values("churn_rate_%"), x="churn_rate_%", y="channel", orientation="h",
    template="plotly_white", title="Churn rate by channel",
    labels={"churn_rate_%": "Churn rate (%)", "channel": ""},
)
fig_cbc.update_traces(marker_color="#ef4444")
right.plotly_chart(fig_cbc)

st.divider()

# ---- Cohort heatmap -------------------------------------------------------- #
st.subheader("Cohort retention heatmap")
st.caption("Each row is a signup-week cohort; columns are weeks since signup. "
           "Read down a column to see if newer cohorts retain better.")
ret = cohort_retention(users, events, max_weeks=max_weeks)
ret.index = ret.index.strftime("%Y-%m-%d")
fig_hm = go.Figure(
    go.Heatmap(
        z=ret.values, x=[f"W{c}" for c in ret.columns], y=ret.index,
        colorscale="Blues", zmin=0, zmax=100,
        text=ret.values, texttemplate="%{text:.0f}",
        colorbar={"title": "Retention %"},
    )
)
fig_hm.update_layout(template="plotly_white", height=max(400, 18 * len(ret)),
                     yaxis={"title": "Signup cohort"}, xaxis={"title": "Weeks since signup"})
st.plotly_chart(fig_hm)

st.divider()

# ---- Retargeting list ------------------------------------------------------ #
st.subheader("🎯 High-value users to win back")
st.caption("At-risk users (lapsing), ranked by lifetime revenue — the shortlist for a win-back campaign.")
cand = retarget_candidates(users, orders, risk_days=risk_days, churn_days=churn_days)
disp = cand.copy()
disp["lifetime_revenue"] = disp["lifetime_revenue"].map(format_currency)
disp = disp.rename(columns={
    "user_id": "User", "channel": "Channel", "country": "Country",
    "days_inactive": "Days inactive", "lifetime_revenue": "Lifetime revenue",
})
st.dataframe(disp, width='stretch', hide_index=True)
