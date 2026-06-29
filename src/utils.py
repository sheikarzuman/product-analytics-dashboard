"""Small, reusable formatting and date helpers used across the dashboard."""
from __future__ import annotations

import pandas as pd


def format_currency(value: float, symbol: str = "$") -> str:
    """Format a number as compact currency (e.g. $1.6M, $12.4K, $42)."""
    if value is None or pd.isna(value):
        return "—"
    abs_v = abs(value)
    if abs_v >= 1_000_000:
        return f"{symbol}{value / 1_000_000:.2f}M"
    if abs_v >= 1_000:
        return f"{symbol}{value / 1_000:.1f}K"
    return f"{symbol}{value:,.0f}"


def format_number(value: float) -> str:
    """Format an integer-like number with thousands separators."""
    if value is None or pd.isna(value):
        return "—"
    return f"{value:,.0f}"


def format_percent(value: float, decimals: int = 1) -> str:
    """Format a 0–100 value as a percentage string."""
    if value is None or pd.isna(value):
        return "—"
    return f"{value:.{decimals}f}%"


def week_floor(s: pd.Series) -> pd.Series:
    """Snap datetimes to the Monday of their ISO week (for weekly trends)."""
    return pd.to_datetime(s).dt.to_period("W-SUN").dt.start_time
