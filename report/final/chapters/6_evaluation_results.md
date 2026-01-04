## Evaluation goals

The evaluation checks whether the artifact fulfils three requirements: 

1. Interpretability (RQ1). Can users read a fuzzy-driven summary and correctly restate what it says 
(topic, timeframe, and direction of change), without going back to raw tables?
2. Robustness and reproducibility (RQ2). Do repeated requests return the same result, and does the interpretation 
layer (timeline/field parsing + wording constraints) reduce the chance of misreading by always surfacing timeframe 
and numeric units?

## Evaluation design

We ran two small evaluation rounds with the same group of six peers (STEM backgrounds), using the 
cached 2019–2024 dataset to keep all runs deterministic.

Round 1 (JSON / CLI). Participants interacted with the JSON request/response version (no UI). Each participant executed two scripted tasks:

* Task A – Citizen quick question: "Find out what happened with education in 2019–2024." Success required restating 
the direction of change (stable) and level label (high) for education; 
additional attempts were allowed if the participant reformulated the query.
* Task B – Citywide follow-up: "Find which departments have the biggest changes in these years." Participants reused 
the same timeframe but asked for `field=all`, validating how the system phrases increases/decreases citywide. Success 
required from participants naming the biggest increases (Departement der Industriellen Betriebe (+0.82 pp/yr), 
Schul- und Sportdepartement (+0.30 pp/yr)) and decreases (Sozialdepartement (-1.21 pp/yr), 
Tiefbau- und Entsorgungsdepartement (-0.15 pp/yr))

After the tasks, participants rated clarity, explainability, and usability on a 1–5 Likert scale, 
selected a preference between the prototype and the Zürich open-data API baseline, and left optional notes.

Round 2 (Streamlit UI). The same tasks were repeated in the Streamlit/CLI interface to check whether the same interaction
works in a lightweight UI and whether removing raw JSON improves perceived usability.

Repeatability checks (RQ2). For each task, we sent the same structured request twice and compared the full JSON 
responses to confirm deterministic outputs.

Intent regression (RQ2). We ran the NLU regression set (`python_code/nlu/nlu_test_set.json`, 70 requests) 
through `python_code/nlu/run_nlu_tests.py` to confirm that everyday questions map consistently to the intended 
slots (timeline, field, generalization level), including compact phrasing and German/English mixing.

## Metrics

We report the following indicators:

* Task success rate: share of participants who produced a correct restatement per task, and how often it succeeded on the first attempt.
* Likert averages: mean ratings for clarity, explainability, and usability, plus short qualitative notes.
* Preference split: number of participants preferring the prototype vs. the baseline API.
* Repeatability diff: identical vs. non-identical JSON responses for repeated requests (determinism check).
* NLU exact-match accuracy: percentage of utterances whose parsed slots match the expected intent.

## Results
Running the artifact on the cached 2019–2024 data produced the latest-year summaries in Table~\ref{tbl:dept-summaries}. 
Education (Schul- und Sportdepartement) accounts for ~29.6% of spending in 2024 and is labeled HIGH & STABLE in this 
window. Some departments show clearer directional change (e.g., positive or negative slope in percentage points per 
year), which results in RISING or FALLING labels with strong membership.

\begin{table}[htbp]
\centering
\caption{Department summaries on the cached 2019--2024 dataset.}
\label{tbl:dept-summaries}
\begin{tabular}{lrrl}
\hline
Department & Share 2024 (\%) & Trend (pp/yr) & Labels \\
\hline
Schul- und Sportdepartement & 29.57 & +0.30 & HIGH \& STABLE \\
Sozialdepartement & 17.99 & -1.21 & MEDIUM \& FALLING \\
Departement der Industriellen Betriebe & 12.12 & +0.82 & MEDIUM \& RISING \\
Tiefbau- und Entsorgungsdepartement & 11.90 & -0.15 & MEDIUM \& FALLING \\
\hline
\end{tabular}
\end{table}

**Citizen task walkthrough (RQ1)**

All participants completed both tasks successfully (Table~\ref{tbl:eval-api}). For Task A, five participants 
obtained the correct interpretation on the first request; one required a reformulation. For Task B, two participants 
reformulated once, mainly to discover or confirm the `field=all` behavior.

Across the API round, the average ratings were 4.0 (clarity), 3.8 (explainability), and 4.17 (usability). Five of 
six participants preferred the fuzzy-summary workflow over using the API directly. One participant noted they would 
still use the API when they "need consolidated data".

\begin{table}[htbp]
\centering
\caption{Evaluation Round 1 (API). Requests per task, task success, ratings (1--5), and preference.}
\label{tbl:eval-api}
\begin{tabular}{lrrrrrrrl}
\hline
Part. & A reqs & A ok & B reqs & B ok & Clarity & Expl. & Usab. & Pref. \\
\hline
P1 & 1 & 1 & 1 & 1 & 4 & 4 & 4 & System \\
P2 & 1 & 1 & 2 & 1 & 4 & 3 & 4 & API \\
P3 & 1 & 1 & 1 & 1 & 4 & 4 & 5 & System \\
P4 & 1 & 1 & 1 & 1 & 4 & 4 & 4 & System \\
P5 & 1 & 1 & 2 & 1 & 4 & 4 & 4 & System \\
P6 & 1 & 1 & 1 & 1 & 4 & 4 & 4 & System \\
\hline
\end{tabular}
\end{table}

Because all participants had technical backgrounds (CS studies or regular use of developer tooling), these scores 
should be treated as indicative rather than representative of a broad citizen audience (generally people don't know how to
work with APIs).

**Follow-up evaluation (Round 2 UI)**

In the Streamlit/CLI round (Table~\ref{tbl:eval-streamlit}), all six participants solved both tasks on the first request,
which suggests that the same underlying logic transfers well to a lightweight UI and that removing raw 
JSON friction improves interaction.

\begin{table}[htbp]
\centering
\caption{Evaluation Round 2 (Streamlit/CLI). Requests per task, task success, ratings (1--5), and preference.}
\label{tbl:eval-streamlit}
\begin{tabular}{lrrrrrrrl}
\hline
Part. & A reqs & A ok & B reqs & B ok & Clarity & Expl. & Usab. & Pref. \\
\hline
P1 & 1 & 1 & 1 & 1 & 5 & 4 & 5 & System \\
P2 & 1 & 1 & 1 & 1 & 5 & 3 & 5 & System \\
P3 & 1 & 1 & 1 & 1 & 4 & 4 & 5 & System \\
P4 & 1 & 1 & 1 & 1 & 4 & 4 & 4 & System \\
P5 & 1 & 1 & 1 & 1 & 5 & 4 & 5 & System \\
P6 & 1 & 1 & 1 & 1 & 4 & 4 & 4 & System \\
\hline
\end{tabular}
\end{table}

Average ratings increased to 4.5 (clarity), 3.8 (explainability), and 4.67 (usability), and all six 
participants preferred the prototype in this format. Qualitative notes are clustered around three themes:

1. Lower interaction friction. Participants explicitly compared the UI to issuing raw requests:
   "Chat-like messaging is definitely better than an API." (P5)
2. Fast insight without heavy machinery. One participant valued that the prototype stays lightweight:
   "I like that there’s no LLM or other crap involved." (P2)
3. Clear potential, but the scope is still narrow. Participants saw value but asked for more use cases:
   "The use cases need to be extended." (P3)

**Robustness and reproducibility (RQ2)**

Determinism-by-design. Replaying the Task A and Task B requests produced identical JSON responses down to 
floating-point values (diff = 0), confirming that the pipeline behaves deterministically on the cached dataset.

Intent regression. Running `python_code/nlu/run_nlu_tests.py` over the 70-utterance set resulted in 70/70 
exact matches (100%). The set includes compact phrasing, multilingual requests, and relative references 
(e.g., "In the last 4 years..."), which indicates that the slot canonicalization is stable for the phrasing 
variety represented in the test set.

## Threats to validity
This evaluation is small (n = 6) and biased toward technically fluent participants, so the Likert ratings likely 
overestimate usability for a general citizen population. The scope is also limited to Zürich and to expenditures 
only (revenues excluded). The aggregation level is department totals, which hides intra-department changes. Finally, 
the membership functions are calibrated for 2019–2024; if future budget distributions shift strongly, the calibration 
should be re-run to avoid label drift.
