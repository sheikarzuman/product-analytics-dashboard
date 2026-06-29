"""Tests for the recommendation engine."""
from __future__ import annotations

from src.recommendations import Recommendation, generate_recommendations

_SEV = {"opportunity": 0, "warning": 1, "critical": 2}


def test_recommendations_structure(users, orders, events, products):
    recs = generate_recommendations(users, orders, events, products)
    assert recs, "should produce at least one recommendation"
    assert all(isinstance(r, Recommendation) for r in recs)
    assert all(r.severity in _SEV for r in recs)
    # ranked by severity (critical first)
    ranks = [_SEV[r.severity] for r in recs]
    assert ranks == sorted(ranks, reverse=True)


def test_recommendations_mentions_best_channel(users, orders, events, products):
    recs = generate_recommendations(users, orders, events, products)
    titles = " ".join(r.title for r in recs)
    assert "email" in titles      # best channel in the fixture
