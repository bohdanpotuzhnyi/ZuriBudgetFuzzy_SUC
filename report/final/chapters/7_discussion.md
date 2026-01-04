## What worked well
The fuzzy linguistic summaries did what we hoped: they turn large budget tables into short, readable statements while
still keeping the link to the underlying numbers. In both evaluation rounds, participants could restate the main message
(level + trend over a stated timeframe), which supports the interpretability goal (RQ1). The interface design also held up
across formats: the same JSON-based request/response logic works in a CLI setting, and the Streamlit UI mainly reduced
interaction friction rather than changing the underlying model.

## Failure modes and edge cases
Some outputs remain harder to read when the label fit is weak. This happens most often for small departments or for
cases where the shares sit near label boundaries, so the dominant label can be a "weak" match. Even when $\mu$ makes
this visible, a few readers still need more guidance to interpret what "weakly rising" or "weakly falling" means in
practice.

Window sensitivity is another edge case. With short municipal series (5–6 years), small shifts of the start year can move
a department across the "stable" threshold, especially when the true slope is close to zero. The Theil–Sen estimator
reduces sensitivity to outliers, but it does not eliminate sensitivity to short time windows. This supports the idea that
a citizen-facing tool should either encourage longer windows or explicitly warn when the trend classification is borderline.

Finally, data quality issues (missing values, zeros, or schema quirks from the API) require careful handling. Even small
preprocessing decisions can change the derived shares and therefore the linguistic labels, so these steps must stay
transparent and reproducible.

## Limitations
The prototype is intentionally descriptive: it does not generate causal explanations ("why did healthcare rise?"), because
the budget data alone does not contain policy context. The current scope is also Zürich-only and aggregated at the
department level, which hides shifts inside departments (program-level changes).

On the interaction side, the NLU remains template- and slot-based. It works well for the supported question patterns, but
coverage is limited (especially for multilingual phrasing and richer paraphrases). The evaluation is also small and uses a
technically fluent peer group, so the results should be treated as indicative rather than representative for a broad
citizen audience. Finally, the calibration is tied to the 2019–2024 distribution; if future budgets shift substantially, the
membership functions should be recalibrated to avoid label drift.

## Lessons learned
* The evaluations reinforced that interpretability is not only about the summarization method but also about interaction
  friction. The same logic scored higher once the Streamlit UI removed the need to work with raw JSON.
* We underestimated how much iteration is needed even for a "simple" computing-with-words system: getting membership
  functions, templates, and provenance to work together in a consistent way took most of the engineering effort.
* Adding lightweight transparency cues (timeframe, slope units, $\mu$) matters. Participants repeatedly pointed to these
  details as the reason the sentences felt trustworthy rather than "hand-wavy".

## Implications for citizen-centered design
Even a lightweight NLP layer can bridge the gap between open budget data and the kinds of questions residents ask, as long
as the system stays explicit about provenance and confidence. In a practical deployment, the same approach could be
embedded into civic explainers or chatbot-style interfaces. However, topic mappings and label wording should be co-designed
with residents so that "high", "low", and "rising" match how people actually talk about priorities.
