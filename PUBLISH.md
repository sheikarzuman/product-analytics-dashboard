# Publishing to GitHub

The repo is already initialised and committed locally. Follow these steps to
push it to GitHub and finish the project.

## 0. Prerequisites
- A GitHub account
- Either the **GitHub CLI** (`gh`) or a browser to create the remote repo

Verify your local history first:
```bash
cd ~/product-analytics-dashboard
git log --oneline        # you should see the Day 1–7 commits
git status               # should be clean
```

## 1. Capture screenshots (do this before pushing so the README renders images)
```bash
# in one terminal
streamlit run app.py
```
Then, in your browser at http://localhost:8501, open each page from the sidebar
and capture a screenshot (macOS: Cmd+Shift+4 · Windows: Win+Shift+S). Save as:

```
screenshots/overview.png
screenshots/funnel.png
screenshots/traffic.png
screenshots/retention.png
screenshots/products.png
screenshots/segments.png
screenshots/recommendations.png
```

Then add a gallery near the top of `README.md`, e.g.:
```markdown
![Executive Overview](screenshots/overview.png)
![Conversion Funnel](screenshots/funnel.png)
```
Commit them:
```bash
git add screenshots README.md
git commit -m "Add dashboard screenshots"
```

## 2A. Publish with the GitHub CLI (fastest)
```bash
gh auth login                       # one-time, if not already authenticated
gh repo create product-analytics-dashboard --public --source=. --remote=origin --push
```
That creates the remote, sets `origin`, and pushes `main` in one step.

## 2B. Publish via the GitHub website (no CLI)
1. Go to https://github.com/new
2. Name it `product-analytics-dashboard`, choose **Public**,
   and **do NOT** initialise with a README/license (you already have them).
3. Click **Create repository**, then run:
```bash
git remote add origin https://github.com/<your-username>/product-analytics-dashboard.git
git branch -M main
git push -u origin main
```

## 3. After pushing
- Confirm the **CI** badge: the GitHub Action runs `pytest` automatically.
  Add a badge to the top of the README (replace `<your-username>`):
  ```markdown
  ![CI](https://github.com/<your-username>/product-analytics-dashboard/actions/workflows/ci.yml/badge.svg)
  ```
- Add a repo **description** and topics on GitHub:
  `streamlit`, `pandas`, `plotly`, `analytics`, `data-analysis`, `dashboard`.
- (Optional) Deploy a live demo for free on **Streamlit Community Cloud**
  (https://streamlit.io/cloud): connect the repo, set the main file to `app.py`.
  Add the live URL to the README.

## 4. Final checklist
- [ ] `pytest` passes locally
- [ ] Screenshots committed and visible in README
- [ ] CI green on GitHub
- [ ] Repo description + topics set
- [ ] (Optional) Live Streamlit Cloud demo linked
