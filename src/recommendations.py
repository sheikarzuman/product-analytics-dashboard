"""Rule-based business recommendation engine.

Reads the dataset, computes the same metrics the dashboard shows, and turns
them into a ranked list of plain-English recommendations with concrete actions.
Kept separate from `metrics.py` so the *interpretation* layer is independent of
the *calculation* layer and easy to test or extend.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

from src import metrics as m
from src.utils import format_currency, format_percent

# Severity drives ordering and the colour used on the page.
_SEVERITY_RANK = {"opportunity": 0, "warning": 1, "critical": 2}


@dataclass(frozen=True)
class Recommendation:
    title: str
    insight: str
    action: str
    severity: str  # "critical" | "warning" | "opportunity"

    def to_dict(self) -> dict:
        return asdict(self)


def generate_recommendations(
    users: pd.DataFrame,
    orders: pd.DataFrame,
    events: pd.DataFrame,
    products: pd.DataFrame,
) -> list[Recommendation]:
    recs: list[Recommendation] = []

    # 1. Best vs worst acquisition channel (by revenue per visitor) ---------- #
    traffic = m.traffic_source_performance(users, orders, events)
    best, worst = traffic.iloc[0], traffic.iloc[-1]
    recs.append(
        Recommendation(
            title=f"Double down on `{best['channel']}`",
            insight=(
                f"{best['channel']} returns {format_currency(best['revenue_per_visitor'])} "
                f"per visitor — the highest of any channel — with a "
                f"{best['signup_rate_%']:.1f}% signup rate."
            ),
            action=f"Shift budget toward {best['channel']} and replicate its targeting.",
            severity="opportunity",
        )
    )
    recs.append(
        Recommendation(
            title=f"Fix or cut `{worst['channel']}`",
            insight=(
                f"{worst['channel']} earns only "
                f"{format_currency(worst['revenue_per_visitor'])} per visitor "
                f"({worst['visit_to_paid_%']:.1f}% visit→paid) despite "
                f"{int(worst['visitors']):,} visitors."
            ),
            action=f"Audit {worst['channel']} creative/landing pages or reallocate spend.",
            severity="warning",
        )
    )

    # 2. Biggest funnel drop-off -------------------------------------------- #
    s_from, s_to, drop = m.biggest_dropoff(events)
    recs.append(
        Recommendation(
            title=f"Plug the {s_from} → {s_to} leak",
            insight=f"{format_percent(drop)} of users are lost between {s_from} and {s_to} — the largest funnel drop-off.",
            action=f"Run experiments on the {s_to.lower()} step (friction, messaging, incentives).",
            severity="critical" if drop >= 80 else "warning",
        )
    )

    # 3. Top revenue product / category ------------------------------------- #
    cat = m.category_sales(orders, products).iloc[0]
    prod = m.product_sales(orders, products).iloc[0]
    recs.append(
        Recommendation(
            title=f"Lean into {cat['category']}",
            insight=(
                f"{cat['category']} drives {format_percent(cat['revenue_share_%'])} of revenue; "
                f"top product is {prod['product_name']} at {format_currency(prod['revenue'])}."
            ),
            action=f"Feature {cat['category']} bestsellers and ensure stock/merchandising.",
            severity="opportunity",
        )
    )

    # 4. Churn signal + retargeting ----------------------------------------- #
    churn = m.churn_summary(users)
    cand = m.retarget_candidates(users, orders)
    at_risk_value = cand["lifetime_revenue"].sum()
    recs.append(
        Recommendation(
            title="Launch a win-back campaign",
            insight=(
                f"Churn rate is {format_percent(churn['churn_rate'])}; "
                f"{churn['at_risk']:,} users are at risk, including high-value buyers "
                f"worth {format_currency(at_risk_value)} in the top shortlist."
            ),
            action="Email/retarget the at-risk shortlist before they fully churn.",
            severity="critical" if churn["churn_rate"] >= 60 else "warning",
        )
    )

    # 5. Early retention ---------------------------------------------------- #
    curve = m.retention_curve(users, events, max_weeks=4)
    wk1 = curve.loc[curve["week_index"] == 1, "retention_%"]
    if not wk1.empty:
        v = float(wk1.iloc[0])
        recs.append(
            Recommendation(
                title="Strengthen first-week activation",
                insight=f"Only {format_percent(v)} of users return in week 1 after signup.",
                action="Add onboarding nudges / first-purchase incentive in the first 7 days.",
                severity="warning" if v < 30 else "opportunity",
            )
        )

    recs.sort(key=lambda r: _SEVERITY_RANK.get(r.severity, 0), reverse=True)
    return recs


if __name__ == "__main__":  # quick CLI preview
    from src.data_loader import load_events, load_orders, load_products, load_users

    for r in generate_recommendations(
        load_users(), load_orders(), load_events(), load_products()
    ):
        print(f"[{r.severity.upper():11}] {r.title}\n   {r.insight}\n   → {r.action}\n")
