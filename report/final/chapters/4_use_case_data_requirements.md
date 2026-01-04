## Use-case scenarios
We designed the prototype around the kinds of questions people actually ask when they open a public budget portal. 
In practice, these questions come in many patterns, yet we define and focus on the next three:

1. Citizen quick question (topic-focused). A user wants a simple explanation for one area, like education or transport. 
The system should return a short statement that includes the current spending level and the direction of change 
over the selected years (e.g., "Since 2019, education spending has stayed high and mostly stable…").
2. Citizen follow-up (citywide overview). After the topic answer, users often ask a broader question like "So what 
changed the most overall?". Here the system should keep the same timeline and return the largest increases and decreases
across departments, so people can compare shifts in priorities.
3. Fact-check / shareable answer (repeatable output). For students, journalists, or anyone who wants to verify results, 
the same request should always produce the same answer and expose the evidence behind it. The system therefore returns 
a deterministic JSON payload that includes the selected topic, the time window, and the numeric trend information.

## Data sources

The prototype is built on Zürich’s public RPK budget API. We use two endpoint families:

* `departemente` for department metadata (names and identifiers),
* `sachkonto2stellig` for aggregated budget amounts by two-digit account categories.

To focus on decisions that are politically "final" in the data, we filter to approved budgets 
(`betragsTyp = GEMEINDERAT_BESCHLUSS`). The script queries departments across years with light throttling to avoid 
stressing the public endpoint and uses the public API key described in `python_code/README.md`.

* Scope of the dataset. We use the years 2019–2024 to include both pre- and post-pandemic budget adjustments. Amounts 
  are aggregated to department totals per year, and we derive each department’s share of total spending, so results 
  are comparable across years.
* Reproducibility. Because public endpoints can change or fail or connection can be lost (either from client or server 
  side), the prototype supports cached CSV exports. This makes demos and evaluations repeatable and allows inspection 
  of the exact data that produced a summary.
* Limitations. The summaries focus on expenditure priorities rather than net budgets. Revenues are excluded when 
  `spending_only=True` to avoid negative shares. Also, because we aggregate at a department level, the system cannot 
  explain shifts inside a department (e.g., which programs changed).

## Requirements

From the use cases above, we created a small set of requirements. They are split into functional requirements 
(what the system must do) and non-functional requirements (how it should behave).

* Functional:

  * F1 (Topic + timeline queries): The system must answer questions about a department or topic with an optional time window. 
    This includes simple mappings (e.g., "education" → Schul- und Sportdepartement) and basic fallback
    matching for near-misses.
  * F2 (Traceable output): Return JSON containing the natural-language summary, share %, slope, time window, and optional context about other departments.
  * F3 (Citywide follow-up): Provide both topic-specific and "citywide" summaries to handle generalization-level follow-up questions.

* Non-functional:

  * NF1 (Reproducibility): The system must run on cached CSV data and produce deterministic outputs so results can be 
    repeated and checked.
  * NF2 (Robustness): Trend estimation should be stable for short series and not flip due to outliers; the system 
    should also fail gracefully if a query does not match any department cleanly.
  * NF3 (Interpretability): Messages must stay short and readable, and they must expose uncertainty cues (membership $\mu$)
    so users can see whether a label is a strong or weak match.

