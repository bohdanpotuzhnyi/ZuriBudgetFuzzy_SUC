## Research questions

The project focuses on whether Zürich’s open budget data can be explained in plain language without losing 
traceability to the underlying numbers. The following research questions guided the work:

* RQ1: Can fuzzy-driven summaries make Zürich’s open budget data easier to understand for non-experts?
* RQ2: How do we keep the summaries stable, repeatable, and hard to misread (especially across different time windows)?

Interpretability is evaluated pragmatically. In this project, an output is considered "interpretable" if users can 
correctly explain what the statement refers to (topic + timeframe + direction of change) and if they rate the answer 
as clear enough to be useful in a citizen-facing setting.



## Methodological approach

To structure the project work, a Design Science Research (DSR) approach was applied [@peffers2007design]. The project 
was organized in iterative steps, moving from problem framing to a working artifact and a small-scale evaluation.

1. Problem identification. Initial observations and feedback from the seminar context indicated that budget 
portals are technically rich but hard to use for non-experts. In particular, citizens often ask questions in everyday 
terms ("education", "more lately", "what changed") that do not match accounting structures.

2. Objectives of a solution. The goal was to create a prototype that returns short, understandable statements while 
remaining verifiable. The artifact therefore had to: 

   * Map citizen phrasing to a small set of supported query parameters. 
   * Summarize budget shares and trends in linguistic terms. 
   * Remain stable enough that minor changes in the time window do not produce contradictory narratives without warning.

3. Design and development. A modular pipeline was implemented in Python with four stages: data retrieval, 
aggregation, linguistic summarization, and response generation. To keep results reproducible during 
demonstrations, the system supports cached CSV exports in addition to live API access. A deterministic 
NLU layer was added to map free-form questions to three query slots: timeline, field, and requested level of detail.

4. Demonstration. The artifact is demonstrated as a question–answer flow comparable to the motivating citizen dialogue. 
Users can ask about a department (e.g., education) or the whole city budget, optionally restricting the time window 
(e.g., "since 2021"), and receive a structured JSON response that includes a short natural-language statement plus 
the supporting evidence.

5. Evaluation. Evaluation was aligned with the two research questions:

   * For RQ1 (Interpretability), six peers with STEM backgrounds executed two scripted citizen tasks 
     (a topic-specific question and a citywide follow-up) while saying a result aloud. We recorded whether 
     they retrieved the correct summary, how many reformulations were needed, and Likert ratings for clarity,
     explainability, and usability.
   * For RQ2 (Robustness & reproducibility), we applied determinism-by-design checks: each scripted request 
     was replayed twice on the cached dataset to verify identical JSON responses. We also inspected rolling 
     four-year windows (and small shifts of the start year) to confirm that label changes occur only when the 
     underlying numbers shift meaningfully, not due to small numerical noise. Finally, we ran an automated 
     regression of 70 requests (`python_code/nlu/nlu_test_set.json`) to confirm that the deterministic 
     parser maps everyday questions to the intended slots consistently.

6. Communication. The outcomes are documented in the final report and supported by a runnable CLI/JSON demo 
that mirrors the use-case dialogue.

## Ethical and societal considerations

A citizen-facing transparency tool can easily create a false impression of certainty. For this reason, the artifact 
is designed to show the basis of each statement rather than only a "nice sentence". Each response includes the 
selected topic, the time window, and the numeric trend unit. In addition, fuzzy membership values are reported to 
indicate how strongly a department fits a label such as "high" or "rising".

The system also avoids causal claims. Budget shifts can result from political decisions, accounting changes, 
exceptional events, or administrative reclassifications. Since such causes are not contained in the dataset used 
here, the artifact does not generate explanations of "why" spending changed. Instead, it limits itself to describing 
observed patterns and pointing back to the original data source for verification. Cached datasets are stored in a simple 
format so that results can be reproduced and inspected.
