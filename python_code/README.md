# Explaining Public Budgets with Fuzzy Linguistic Summaries

## Overview

This folder contains a small proof‑of‑concept that turns Zürich’s open budget data into short fuzzy linguistic 
summaries (human‑readable statements like “rising” / “stable”, “high” / “medium”, etc.). It also exposes a tiny 
“Q&A” interface: you can ask a free‑text question, the NLU layer converts it into a structured JSON request, and the 
summarizer responds with a deterministic message + metadata.

The goal is not to build a full product, but to demonstrate the end‑to‑end narrative: open data → aggregation 
→ fuzzy modelling → simple language, while keeping outputs traceable and reproducible.

## Install (Local)

- Python 3.9+
- Recommended: run everything from this folder so cache files are written here:
  - `cd python_code`
- Install dependencies:
  - `pip install -r requirements.txt`

## Run

### Batch summaries (generate / refresh caches)

- `python3 summarizer/zurich_budget_linguistic_summaries.py`
- On success it prints top summaries and writes:
  - `zrh_budget_by_dept_year.csv`
  - `zrh_budget_linguistic_summaries.csv`

### Q&A style (JSON request, slide artifact)

- Example:
  - `python3 summarizer/zurich_budget_linguistic_summaries.py --request '{"timeline":"all","field":"education","generalization_level":1}'`
- Response (JSON):
  - `{ "message": "Since 2019, ...", "request": {...}, ... }`

### Ask in free text (CLI)

- `python3 ask.py "Where is Zurich spending more on housing lately?"`
- Prints the interpreted request (NLU output) and the summarizer response.

### Streamlit dashboard

- From `python_code/`:
  - `streamlit run streamlit_app.py`
- Or from repo root:
  - `streamlit run python_code/streamlit_app.py`

## Regenerate Fuzzy Calibration

- `python3 -m calibration.recompute_membership`
- This recomputes percentile/MAD breakpoints and overwrites `summarizer/label_calibration.json`.

## Examples

- Biggest movers citywide:
  - `python3 summarizer/zurich_budget_linguistic_summaries.py --request '{"timeline":"all","field":"all","generalization_level":1}'`
- Education focus since 2019:
  - `python3 summarizer/zurich_budget_linguistic_summaries.py --request '{"timeline":{"since":2019},"field":"education","generalization_level":2}'`

## NLU Parser

- `nlu/parser.py` maps free‑text questions to the JSON request schema used by `answer_request()`.
- `python3 -m nlu.run_nlu_tests` evaluates the parser against `nlu/nlu_test_set.json` and prints accuracy + failures.

## Troubleshooting

- `ModuleNotFoundError: pandas/numpy`: run `pip install -r requirements.txt`.
- API fetching fails: install `requests`, ensure internet access, and optionally set `ZRH_API_KEY`.
- Empty results: ensure `zrh_budget_by_dept_year.csv` exists for offline mode, or allow API fetching.
