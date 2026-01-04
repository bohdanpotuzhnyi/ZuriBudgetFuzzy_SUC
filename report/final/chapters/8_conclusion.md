## Conclusion
This project demonstrated that fuzzy linguistic summaries, powered by robust trend estimation and transparent membership
scores, can translate Zürich’s open budgets into interpretable statements while remaining traceable to the underlying
numbers. Determinism-by-design checks confirmed that the system reproducibly returns the same JSON payload when the same
request is issued twice on the cached dataset.

The artifact addresses RQ1 by showing that participants can restate the topic, timeframe, and direction of change after
reading the summaries. It addresses RQ2 by demonstrating repeatable outputs and a deterministic interpretation layer that
surfaces the selected timeframe and trend units in every response, reducing the risk of misreading.

## Outlook
Next steps include:
1. Scheduling periodic re-calibration runs as new budgets are released.
2. Extending the deterministic NLU coverage to handle broader phrasing and multilingual input. 
3. Expanding the data granularity to finer-grained account lines and additional municipalities. 
4. Linking external policy artifacts (e.g., council minutes or policy documents) so the system can reference 
evidence-backed context alongside the descriptive fuzzy summaries.

The immediate roadmap focuses on: 
1. Extending response templates to support more linguistic variations without losing clarity.
2. Broadening the request vocabulary and topic mappings in the NLU layer.
3. Running a larger follow-up evaluation beyond the initial six STEM peers. 
4. Presenting the prototype to Stadt Zürich to explore collaboration and validate requirements for a minimum viable product.

## Use of AI tools
AI-based tools were used to improve the grammar and wording of this report. The system design, implementation, and evaluation were carried out by the authors.
