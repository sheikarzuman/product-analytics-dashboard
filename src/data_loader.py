"""Data access layer.

A thin abstraction over the data *source* so the rest of the app never reads
files directly. Today the source is CSV; migrating to SQLite later means
swapping the source in `get_source()` — every metrics/chart function keeps
working unchanged because they all receive plain DataFrames.
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Columns that should be parsed as datetimes, per table.
DATE_COLUMNS: dict[str, list[str]] = {
    "users": ["signup_date", "last_active_date"],
    "orders": ["order_date"],
    "events": ["event_time"],
    "products": [],
}


class DataSource(Protocol):
    """Anything that can return a table as a DataFrame."""

    def load(self, table: str) -> pd.DataFrame: ...


class CSVDataSource:
    """Reads tables from CSV files in a directory."""

    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self.data_dir = data_dir

    def load(self, table: str) -> pd.DataFrame:
        path = self.data_dir / f"{table}.csv"
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found. Run `python -m src.generate_data` first."
            )
        return pd.read_csv(path, parse_dates=DATE_COLUMNS.get(table, []))


class SQLiteDataSource:
    """Reads tables from a SQLite database (post-MVP drop-in).

    Usage later:  switch `get_source()` to return SQLiteDataSource(path).
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def load(self, table: str) -> pd.DataFrame:
        import sqlite3

        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql(f"SELECT * FROM {table}", conn)
        for col in DATE_COLUMNS.get(table, []):
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        return df


def get_source() -> DataSource:
    """Single switch point for the active data source (CSV today)."""
    return CSVDataSource()


# --------------------------------------------------------------------------- #
# Optional Streamlit caching: no-ops cleanly when Streamlit isn't installed   #
# (e.g. when running unit tests or the generator).                            #
# --------------------------------------------------------------------------- #
try:  # pragma: no cover
    import streamlit as st

    _cache = st.cache_data
except Exception:  # pragma: no cover

    def _cache(func=None, **_kwargs):
        if func is None:
            return lambda f: f
        return func


@_cache
def load_table(table: str) -> pd.DataFrame:
    return get_source().load(table)


def load_users() -> pd.DataFrame:
    return load_table("users")


def load_orders() -> pd.DataFrame:
    return load_table("orders")


def load_events() -> pd.DataFrame:
    return load_table("events")


def load_products() -> pd.DataFrame:
    return load_table("products")
