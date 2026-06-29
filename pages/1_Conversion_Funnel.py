"""Conversion Funnel page: Visit → Signup → Add to Cart → Purchase."""
from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data_loader import load_events
from src.metrics import biggest_dropoff, funnel_by_channel, funnel_counts
from src.utils import format_number, format_percent

st.set_page_config(page_title="Conversion Funnel", page_icon="🪜", layout="wide")
st.title("🪜 Conversion Funnel")
st.caption("Where prospects drop off on the path from first visit to purchase.")

events = load_events()
funnel = funnel_counts(events)

# ---- Headline: biggest leak ------------------------------------------------ #
src_stage, dst_stage, drop = biggest_dropoff(events)
st.info(
    f"**Biggest drop-off:** {src_stage} → {dst_stage}, "
    f"losing **{format_percent(drop)}** of users at that step."
)

# ---- Funnel chart ---------------------------------------------------------- #
left, right = st.columns([3, 2])
fig = go.Figure(
    go.Funnel(
        y=funnel["stage"],
        x=funnel["count"],
        textposition="inside",
        textinfo="value+percent initial",
        marker={"color": ["#93c5fd", "#60a5fa", "#3b82f6", "#1d4ed8"]},
    )
)
fig.update_layout(template="plotly_white", margin=dict(t=10, b=10))
left.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Step conversion")
    for _, r in funnel.iterrows():
        st.metric(
            r["stage"],
            format_number(r["count"]),
            help=f"{format_percent(r['pct_of_top'])} of all visitors",
        )
        st.caption(f"Step conversion: {format_percent(r['step_conversion'])}")

st.divider()

# ---- Funnel by channel ----------------------------------------------------- #
st.subheader("Funnel by acquisition channel")
by_ch = funnel_by_channel(events)
st.caption("Visit→purchase conversion reveals which channels send buyers, not just clicks.")

fig2 = px.bar(
    by_ch.sort_values("visit_to_purchase_%"),
    x="visit_to_purchase_%", y="channel", orientation="h",
    template="plotly_white", text="visit_to_purchase_%",
    labels={"visit_to_purchase_%": "Visit → Purchase (%)", "channel": ""},
)
fig2.update_traces(marker_color="#1d4ed8", texttemplate="%{text:.2f}%")
st.plotly_chart(fig2, use_container_width=True)

st.dataframe(
    by_ch.rename(columns={"visit_to_purchase_%": "Visit→Purchase %",
                          "signup_to_purchase_%": "Signup→Purchase %"}),
    use_container_width=True, hide_index=True,
)
