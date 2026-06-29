"""Centralised Plotly styling and reusable chart builders.

Keeping colours and chart construction here means every page shares one visual
language and a styling change is made in a single place.
"""
from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go

TEMPLATE = "plotly_white"

COLORS: dict[str, str] = {
    "primary": "#2563eb",
    "green": "#10b981",
    "indigo": "#6366f1",
    "red": "#ef4444",
    "sky": "#0ea5e9",
    "violet": "#8b5cf6",
    "amber": "#f59e0b",
}


def horizontal_bar(
    df, x: str, y: str, color: str = COLORS["indigo"],
    title: str = "", labels: dict | None = None, order_by_total: bool = True,
) -> go.Figure:
    fig = px.bar(df, x=x, y=y, orientation="h", template=TEMPLATE,
                 title=title, labels=labels or {})
    fig.update_traces(marker_color=color)
    if order_by_total:
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return fig


def vertical_bar(
    df, x: str, y: str, color: str = COLORS["green"],
    title: str = "", labels: dict | None = None,
) -> go.Figure:
    fig = px.bar(df, x=x, y=y, template=TEMPLATE, title=title, labels=labels or {})
    fig.update_traces(marker_color=color)
    return fig


def area(
    df, x: str, y: str, color: str = COLORS["primary"],
    title: str = "", labels: dict | None = None,
) -> go.Figure:
    fig = px.area(df, x=x, y=y, template=TEMPLATE, title=title, labels=labels or {})
    fig.update_traces(line_color=color)
    return fig
