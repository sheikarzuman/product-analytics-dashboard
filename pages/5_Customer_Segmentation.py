"""Customer Segmentation page (RFM-based)."""
from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.data_loader import load_orders, load_users
from src.metrics import rfm_table, segment_summary
from src.utils import format_currency, format_number

st.set_page_config(page_title="Customer Segmentation", page_icon="👥", layout="wide")
st.title("👥 Customer Segmentation")
st.caption(
    "RFM segments buyers by how recently (R) and how often (F) they purchase, "
    "and how much they spend (M)."
)

users, orders = load_users(), load_orders()
rfm = rfm_table(users, orders)
summary = segment_summary(rfm)

c = st.columns(3)
c[0].metric("Buyers analysed", format_number(rfm["user_id"].nunique()))
champ = summary[summary["segment"] == "Champions"]
c[1].metric("Champions", format_number(int(champ["customers"].iloc[0])) if not champ.empty else "0")
c[2].metric("Avg lifetime value", format_currency(rfm["monetary"].mean()))

st.divider()
left, right = st.columns(2)

fig_seg = px.bar(
    summary.sort_values("customers"), x="customers", y="segment", orientation="h",
    template="plotly_white", title="Customers per segment",
    labels={"customers": "Customers", "segment": ""},
)
fig_seg.update_traces(marker_color="#8b5cf6")
left.plotly_chart(fig_seg, use_container_width=True)

fig_val = px.bar(
    summary.sort_values("total_revenue"), x="total_revenue", y="segment", orientation="h",
    template="plotly_white", title="Revenue per segment",
    labels={"total_revenue": "Revenue ($)", "segment": ""},
)
fig_val.update_traces(marker_color="#f59e0b")
right.plotly_chart(fig_val, use_container_width=True)

st.divider()
st.subheader("Segment scorecard")
disp = summary.copy()
disp["avg_monetary"] = disp["avg_monetary"].map(format_currency)
disp["total_revenue"] = disp["total_revenue"].map(format_currency)
st.dataframe(
    disp.rename(columns={"segment": "Segment", "customers": "Customers",
                         "avg_monetary": "Avg value", "total_revenue": "Revenue",
                         "revenue_share_%": "Revenue %"}),
    use_container_width=True, hide_index=True,
)

with st.expander("What do the segments mean?"):
    st.markdown(
        "- **Champions** — recent, frequent, high spend. Reward & upsell.\n"
        "- **Loyal** — buy often; nurture into Champions.\n"
        "- **New / Recent** — bought recently but not yet frequent; onboard.\n"
        "- **At Risk** — used to buy often, slipping in recency; win back.\n"
        "- **Hibernating** — low recency & frequency; low-cost reactivation.\n"
        "- **Needs Attention** — mid-tier; targeted offers."
    )
