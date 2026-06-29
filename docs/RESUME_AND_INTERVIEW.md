# Resume & Interview Prep — Product Analytics Dashboard

> Note: the dataset is **synthetic** (realistically modelled, not real company
> data). Frame the project as demonstrating analytics & engineering skill, not
> as real business impact. All figures below come from the generated dataset.

---

## 1. Resume bullet points (pick 2–3)

- Built an 8-page **product analytics dashboard** (Streamlit, Pandas, Plotly)
  computing acquisition funnel, retention, churn, RFM segmentation and channel
  performance over a synthetic ~8,000-user e-commerce dataset.
- Designed a **layered architecture** (swappable data source → pure-function
  metrics → Streamlit UI) enabling a **pytest** suite of unit tests and a
  one-line CSV→SQLite migration path.
- Implemented a **rule-based recommendation engine** that converts metrics into
  ranked, actionable insights (e.g., flagging the largest funnel drop-off and a
  revenue-weighted win-back list of at-risk customers).
- Modelled **cohort retention** and an **RFM segmentation** that revealed ~64%
  of revenue concentrated in two customer segments.

## 2. One-line description
> An interactive Streamlit dashboard that turns raw e-commerce events into
> funnel, retention, churn, and segmentation analytics — and auto-generates
> prioritised business recommendations.

## 3. Short paragraph (portfolio / LinkedIn)
> A product analytics dashboard for a D2C/e-commerce business, built with
> Python, Pandas, Streamlit and Plotly. It covers the full analytics surface a
> growth team needs — KPIs, a visit→purchase conversion funnel, traffic-source
> economics, cohort retention and churn, product/category sales, and RFM
> customer segmentation — and layers a recommendation engine on top that ranks
> the highest-impact actions. The codebase is cleanly separated into data,
> logic and presentation layers, with pure, unit-tested metric functions and a
> data layer designed to migrate from CSV to SQLite without touching business
> logic.

---

## 4. Key results to quote (from the synthetic dataset)

| Metric | Value |
|---|---|
| Users / events / orders | ~7,900 / ~91k / ~6.2k |
| Revenue · AOV | $1.57M · ~$502 |
| Signup→paid conversion | 28.3% |
| Activation rate | 42.5% |
| Funnel | 77.9k visits → 7.9k signups → 3.6k carts → 1.5k purchases |
| Biggest funnel leak | Visit → Signup (88.8%) |
| Best vs worst channel (rev/visitor) | email $60.53 vs social $3.14 (~19×) |
| Week-1 retention | ~25% |
| Revenue concentration | Champions + At-Risk ≈ 64% of revenue |
| Top category | Electronics (41.8% of revenue) |

---

## 5. Interview talking points

**"Walk me through the project."**
Start with the goal (decisions, not charts), then the three layers, then one
insight the recommendation engine surfaces and the action it implies.

**"Why separate metrics from the UI?"**
Pure functions that take DataFrames and return numbers are testable in isolation
and reusable across pages and the recommendation engine. The Streamlit layer is
just presentation. This is why a 9-test suite with exact expected values was
possible.

**"How would you move from CSV to a database?"**
The `data_loader` exposes a `DataSource` protocol; `get_source()` is the single
switch point. Swapping `CSVDataSource` for `SQLiteDataSource` changes nothing
downstream because every consumer receives a DataFrame.

**Explain the funnel.**
Visit → Signup → Add to Cart → Purchase. I report both step-to-step conversion
and conversion-from-top. A subtlety: post-signup activity is also logged as
`visit` events, so the top of the funnel filters to anonymous acquisition visits
to avoid inflating it — a good example of validating a metric's definition.

**Explain retention / cohorts.**
Users are grouped by signup week; I measure the share still active N weeks later.
Week-1 retention is the most predictive early signal. The cohort heatmap shows
whether newer cohorts retain better than older ones.

**Explain RFM.**
Recency, Frequency, Monetary, each scored into quartiles, mapped to segments
(Champions, Loyal, At-Risk, Hibernating…). It showed revenue concentrated in a
few segments, which is what justifies a win-back campaign.

**"What was a bug you caught?"**
The first retention curve dipped then bumped because I computed the week index
from calendar-week flooring; signups mid-week smeared activity across week
boundaries. Switching to weeks-since-each-user's-signup fixed it — caught by the
verification step, not in production.

**"What would you do next?"**
A churn-risk model (logistic regression), shared date/channel filters, cohort
LTV and payback by channel, and CI/CD (already added a GitHub Actions pytest
workflow).
