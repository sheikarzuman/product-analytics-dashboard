"""Traffic Source Performance page."""
from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.data_loader import load_events, load_orders, load_users
from src.metrics import traffic_source_performance
from src.utils import format_currency

st.set_page_config(page_title="Traffic Sources", page_icon="📡", layout="wide")
st.title("📡 Traffic Source Performance")
st.caption("Which acquisition channels actually drive revenue — not just traffic.")

users, orders, events = load_users(), load_orders(), load_events()
perf = traffic_source_performance(users, orders, events)

best = perf.iloc[0]
st.success(
    f"**Best channel by revenue/visitor:** `{best['channel']}` at "
    f"{format_currency(best['revenue_per_visitor'])} per visitor "
    f"({best['signup_rate_%']:.1f}% signup rate)."
)

c1, c2 = st.columns(2)
fig_rpv = px.bar(
    perf, x="revenue_per_visitor", y="channel", orientation="h",
    template="plotly_white", labels={"revenue_per_visitor": "Revenue / visitor ($)", "channel": ""},
    title="Revenue per visitor",
)
fig_rpv.update_traces(marker_color="#6366f1")
fig_rpv.update_layout(yaxis={"categoryorder": "total ascending"})
c1.plotly_chart(fig_rpv, use_container_width=True)

fig_sr = px.bar(
    perf.sort_values("signup_rate_%"), x="signup_rate_%", y="channel", orientation="h",
    template="plotly_white", labels={"signup_rate_%": "Signup rate (%)", "channel": ""},
    title="Signup rate",
)
fig_sr.update_traces(marker_color="#10b981")
c2.plotly_chart(fig_sr, use_container_width=True)

st.divider()
st.subheader("Channel scorecard")
display = perf.copy()
display["revenue"] = display["revenue"].map(lambda v: format_currency(v))
display["aov"] = display["aov"].map(lambda v: format_currency(v))
display["revenue_per_visitor"] = display["revenue_per_visitor"].map(lambda v: format_currency(v))
display = display.rename(columns={
    "channel": "Channel", "visitors": "Visitors", "signups": "Signups",
    "paying_users": "Paying", "revenue": "Revenue", "orders": "Orders",
    "signup_rate_%": "Signup %", "visit_to_paid_%": "Visit→Paid %",
    "aov": "AOV", "revenue_per_visitor": "Rev/Visitor",
})
st.dataframe(display, use_container_width=True, hide_index=True)
