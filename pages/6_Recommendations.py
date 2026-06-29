"""Recommendations & Insights page — the 'so what' of the dashboard."""
from __future__ import annotations

import streamlit as st

from src.data_loader import load_events, load_orders, load_products, load_users
from src.recommendations import generate_recommendations

st.set_page_config(page_title="Recommendations", page_icon="💡", layout="wide")
st.title("💡 Recommendations & Insights")
st.caption("Auto-generated, prioritised actions derived from the data.")

users, orders, events, products = (
    load_users(), load_orders(), load_events(), load_products()
)
recs = generate_recommendations(users, orders, events, products)

_STYLE = {
    "critical": ("🔴", "Critical"),
    "warning": ("🟠", "Watch"),
    "opportunity": ("🟢", "Opportunity"),
}

counts = {k: sum(r.severity == k for r in recs) for k in _STYLE}
c = st.columns(3)
c[0].metric("🔴 Critical", counts["critical"])
c[1].metric("🟠 Watch", counts["warning"])
c[2].metric("🟢 Opportunities", counts["opportunity"])
st.divider()

for r in recs:
    icon, label = _STYLE.get(r.severity, ("•", r.severity))
    with st.container(border=True):
        st.markdown(f"### {icon} {r.title}")
        st.markdown(f"**{label}** — {r.insight}")
        st.markdown(f"**Recommended action:** {r.action}")
