## System overview
The prototype follows a simple pipeline: load data → compute shares and trends → assign fuzzy labels → generate a 
response. A small CLI script orchestrates the process. It either loads a cached dataset (`python_code/zrh_budget_by_dept_year.csv`) 
or fetches fresh data from the API, computes department shares, trend slopes, and linguistic labels, and then outputs 
either batch summaries or a JSON answer to a single request. Figure \ref{fig:zrh_flow} shows the end-to-end flow. Internally, 
the pipeline is: data source (API/CSV) → trend module → fuzzy labeling → response templates, exposed through the 
deterministic NLU parser and a query function.


## Iterative development
The artifact was developed in two iterations:

- Iteration 1 (proof of concept v0): a minimal JSON request/response prototype that executed a small set of scripted queries and 
  returned fuzzy driven linguistic statements done to validate that such an idea is feasible and that it can provide 
  consistent results.
- Iteration 2 (proof of concept v1): the current version with a Streamlit UI, CLI interface, simple NLU parser, query service, 
  and a reusable summarizer module.

```{=latex}
\begin{figure}[htbp]
\centering
\includegraphics[width=\textwidth]{images/puml/system_pipeline.png}
\caption{End-to-end flow of the Zürich budget Q\&A prototype}
\label{fig:zrh_flow}
\end{figure}
```

## Data processing
Data loading is handled by `load_or_fetch`. If cached aggregates exist, the system uses them to keep demos and 
evaluations deterministic. Otherwise, it fetches per-department totals from the API, converts amount fields (`betrag`) 
to numeric CHF, and sums two-digit account rows (`sachkonto`) to department totals per year 
(`python_code/summarizer/zurich_budget_linguistic_summaries.py`).

To keep the story consistent ("public spending"), we optionally filter out revenue-related negatives 
(`spending_only=True`). After aggregation, yearly totals are merged back in, so each department-year row also 
contains its share of total city spending. These shares are the input for the fuzzy "low/medium/high" labels.


## Trend computation
Trends are computed with a Theil–Sen slope estimator (`theil_sen_slope`). Instead of fitting one least-squares line 
(which can flip with outliers), it takes the median of all pairwise year-to-year slopes.

We report trends in two forms:

* percentage points per year (`slope_pp_per_year`) for direct interpretability
* relative slope compared to the mean share (`slope_pct_of_mean`) so departments of different size can be compared more fairly.

These values are then used for the fuzzy trend labels.

## Fuzzy model
The fuzzy membership functions are calibrated from Zürich’s 2019–2024 distribution and stored 
in `python_code/summarizer/label_calibration.json` so the configuration is reproducible.

* Spending level (LOW / MEDIUM / HIGH). We build trapezoids from the empirical share percentiles 10/30/50/70/90.
  This keeps the label boundaries tied to what is "small" or "large" in Zürich’s actual budget distribution rather 
  than arbitrary thresholds.
* Trend (FALLING / STABLE / RISING). We use the median absolute deviation (MAD) of relative slopes to set what 
  counts as "stable" in practice. Roughly, "stable" covers a band around the median ($\approx \pm 1 \cdot$ MAD), while "rising" and 
  "falling" extend outward.

For each department, the system outputs a label and membership strength:
`(level_label, level_mu, trend_label, trend_mu)`.
We include $\mu$ values because they serve as a transparency cue: a label can be a strong fit (high $\mu$) or only a weak fit (low $\mu$).

Membership functions are calibrated from the empirical distribution of Zürich’s 2019–2024 budget shares and persisted in 
`python_code/summarizer/label_calibration.json` for reproducibility. Level trapezoids use the 10/30/50/70/90 percentiles to define LOW, MEDIUM, 
and HIGH categories, keeping their overlap proportional to how departments cluster in the data. Trend trapezoids rely on 
the median absolute deviation (MAD) of the relative slopes (Theil–Sen slope divided by mean share) so that "stable" spans 
approximately $\pm 1 \cdot$ MAD around the citywide median and "rising/falling" occupy progressively wider shoulders. Each 
department thus receives `(level_label, level_mu, trend_label, trend_mu)`, and the final message concatenates the dominant 
linguistic values together with supporting statistics to maintain transparency.

\begin{table}[htbp]
\centering
\begin{minipage}{0.48\linewidth}
\centering
\caption{Level member. trap. (share in \%).}
\label{tbl:level-trap}
\begin{tabular}{lrrrr}
\hline
Level label & a & b & c & d \\
\hline
LOW    & 0.00 & 0.00 & 2.75 & 6.37 \\
MEDIUM & 2.75 & 6.37 & 8.06 & 11.05 \\
HIGH   & 8.06 & 11.05 & 27.33 & 100.00 \\
\hline
\end{tabular}
\end{minipage}\hfill
\begin{minipage}{0.48\linewidth}
\centering
\caption{Trend member. trap. (relative slope).}
\label{tbl:trend-trap}
\begin{tabular}{lrrrr}
\hline
Trend label & a & b & c & d \\
\hline
FALLING & -100.00 & -4.24 & -2.47 & -0.71 \\
STABLE  & -4.24   & -2.47 & 1.05  & 2.82 \\
RISING  & -0.71   & 1.05  & 2.82  & 100.00 \\
\hline
\end{tabular}
\end{minipage}
\end{table}

The exact trapezoid boundaries used in the demo are shown in Table~\ref{tbl:level-trap} and Table~\ref{tbl:trend-trap}.
These values are also stored in `python_code/summarizer/label_calibration.json`, so the reported configuration matches 
the executable artifact.


## Response generation
When the CLI is called with `--request`, the program parses the JSON payload, filters the dataset by the requested time
window, resolves the department name (including simple English aliases), and returns one of two response types:

1. Topic answer (one department)
2. City-wide answer (largest increases/decreases across departments)

The output mirrors the slide dialogue shown in `presentation/SUC_Final.pdf` and `presentation/SUC_MidTerm.pdf`: a short message plus a structured JSON 
payload with the evidence.

```json
{
  "message": "Since 2019, Schul- und Sportdepartement is stable and currently high (29.6% in 2024, +0.30 pp/yr). Meanwhile, the biggest increases are in Departement der Industriellen Betriebe, Schul- und Sportdepartement.",
  "request": {"timeline": {"since": 2019}, "field": "education", "generalization_level": 1},
  "department": "Schul- und Sportdepartement",
  "summary": {
    "level": "high",
    "level_mu": 0.97,
    "trend": "stable",
    "trend_mu": 1.00,
    "share_last_pct": 29.57,
    "slope_pp_per_year": 0.30,
    "slope_pct_of_mean": 1.06,
    "years": {"start": 2019, "end": 2024}
  }
}
```

A small "generalization level" controls whether the system appends a broader context (e.g., top movers citywide). 
This makes topic questions and follow-up questions work as a simple multi-turn flow, without requiring a full chatbot stack.

For citywide questions, the JSON explicitly exposes ranked movers:

```json
{
  "message": "Between 2019 and 2024, the biggest increases are in Departement der Industriellen Betriebe (+0.82 pp/yr), Schul- und Sportdepartement (+0.30 pp/yr). Decreases are led by Sozialdepartement (-1.21 pp/yr), Tiefbau- und Entsorgungsdepartement (-0.15 pp/yr).",
  "request": {"timeline": {"since": 2019}, "field": "all", "generalization_level": 1},
  "top_increases": [
    {"departement": "Departement der Industriellen Betriebe", "slope_pp_per_year": 0.823, "last_share": 12.12},
    {"departement": "Schul- und Sportdepartement", "slope_pp_per_year": 0.300, "last_share": 29.57}
  ],
  "top_decreases": [
    {"departement": "Sozialdepartement", "slope_pp_per_year": -1.215, "last_share": 17.99},
    {"departement": "Tiefbau- und Entsorgungsdepartement", "slope_pp_per_year": -0.145, "last_share": 11.90}
  ]
}
```

Because the payload is deterministic (normally the information about the closed year financial statements is not going 
to change), a third party can rerun the same request and verify both the text and the structured evidence.

## Reproducibility and deployment
Running `python3 summarizer/zurich_budget_linguistic_summaries.py` produces both aggregated and summarized CSV outputs, 
so intermediate values can be inspected. Dependencies are intentionally small (`pandas`, `numpy`, and optionally 
`requests`), which keeps the tool lightweight for offline demos. Cached CSVs also act as fixtures for tests and 
notebooks, and the repository README documents setup and example commands.

For demonstrations, we provide a thin query service and a Streamlit front-end (`python_code/streamlit_app.py`). The 
UI shows the parsed request (timeline/field/detail level) as part of the JSON response (`request` field), so the
interpretation does not need to be duplicated separately. When the request originates from the NLU layer, it also
includes confidence metadata such as `field_confidence` and `field_candidates`.

**NLU regression set**
To make the "question understanding" layer reproducible, the repository includes a small test set at 
`python_code/nlu/nlu_test_set.json`. It contains 70 example utterances with expected slot outputs (timeline, 
field, detail level), including short follow-ups and compact phrasing:

```json
{
  "schema_version": "0.2.7",
  "items": [
    {"id": 1, "utterance": "So what are they spending more on now?", "expected": {"timeline": "all", "field": "all", "generalization_level": 1}},
    {"id": 2, "utterance": "Whats increasing the most since 2019?", "expected": {"timeline": {"since": 2019}, "field": "all", "generalization_level": 1}},
    {"id": 69, "utterance": "Detailed: fin dep changes since 2020.", "expected": {"timeline": {"since": 2020}, "field": "finance", "generalization_level": 2}},
    {"id": 70, "utterance": "In the last 4 years, how did finance change?", "expected": {"timeline": {"since": 2021}, "field": "finance", "generalization_level": 1}}
  ]
}
```

The CLI tester (`python_code/nlu/run_nlu_tests.py`) runs the full set and reports exact-match accuracy, so future 
changes to the parser can be checked for regressions when new paraphrases or languages are added.
