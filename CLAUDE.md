# Project: Product Analytics Dashboard

7-day build of a D2C/e-commerce analytics dashboard. Goal: demonstrate product
thinking & business metrics, not just Python.

## Stack
Python 3.12+, Pandas, Streamlit, Plotly, (SQLite optional post-MVP), Git.

## Architecture rules
- `src/data_loader.py` is the ONLY place that touches the data source.
  Metrics/charts always receive DataFrames so CSV→SQLite is a one-line swap.
- `src/metrics.py` functions are PURE (no I/O, no Streamlit) and type-hinted.
- New analytics pages go in `pages/` (Streamlit auto-discovers them).

## Working agreement (from the user)
- Work incrementally; generate only files needed for the current step.
- Explain reasoning before writing code; prefer maintainable over clever.
- Ask before major architectural changes.
- After each milestone, suggest a Git commit message.
- Assume the user is learning: include concise analytics-concept explanations.

## 7-day plan
- Day 1: setup + synthetic dataset ✅
- Day 2: data loading + KPI metrics + Executive Overview ✅
- Day 3: funnel + traffic analytics ✅
- Day 4: retention, churn, cohorts ✅
- Day 5: product sales, RFM segmentation, recommendations ✅
- Day 6: testing, refactor, docs ✅
- Day 7: GitHub publish + resume/interview prep ✅
