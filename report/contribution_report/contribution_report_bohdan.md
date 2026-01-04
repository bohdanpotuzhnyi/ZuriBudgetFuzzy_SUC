# Contribution Report

## Contributions

This project started quite simply: we had a rough idea ("budgets are open, but you have to make a bunch 
of requests to get some idea about them"), and then we tried to turn it into something that 
actually works.

First, we aligned on the core concept: take Zürich’s open budget data, compress the big tables into short fuzzy 
linguistic summaries ("high", "medium", "stable", "rising", etc.), and keep it traceable + deterministic so the 
output can be checked and repeated. From there, the work naturally splits into two tracks:

1. Build the actual pipeline (data → trend → fuzzy labels → message/JSON).
I mostly went into implementation mode. I worked on loading the data (API or cached CSV), aggregating it to
department-year totals, computing shares, computing robust slopes (Theil–Sen), and then mapping those numbers into 
fuzzy labels via trapezoidal membership functions. Next huge thing, was to figure out how we can make it work not as an 
API tool, that just lowers then number of requests and calculations to 1, yet also how to maybe make it a bit closer to 
the actual use-case that might exist(e.g., in a chatbot)
like way, the answer was simple ~~THE CHATGPT~~, oh no, no way the idea is really like... it might run somewhere in 
government. So we have to show how in a simple(~~might be not the most scalable way though~~) to make an NLU system,
that can convert a message to the api request.

2. Make it usable and actually citizen-facing (wording, interaction, evaluation).
Vlada pushed the project toward the citizen-facing side shaping the use-cases and requirements so we don’t dive into 
a pure technical demo(~~was beating me with sticks, but we still went to eval_1 with only API proto~~), 
and making sure the output wording consistently includes timeframe, units and other necessary details. 
She also handled the creation of Streamlit UI app, which basically removed the need to use the console line and made the whole 
interaction feel more chat-like.

Then we ran the two evaluation rounds with the same group (API/JSON first, then Streamlit UI). Vlada coordinated the 
evaluation flow and collected/cleaned the notes, while I handled the "hard proof" parts like determinism-by-design 
and the regression test results. After that, we merged both sides into the write-up and made sure the claims match 
the numbers and tables.

Writing-wise, it was shared. I wrote more of the implementation-heavy parts (pipeline, reproducibility, tests), 
while Vlada wrote more of the citizen-facing framing (use cases, design rationale, discussion). Final edits and 
consistency checks were done together (including the ~~LaTeX~~Pandoc/table pain).

## Summary

Overall, I think the workload was shared in a pretty balanced way, just in different shapes: I did more of the core 
engineering and determinism/testing, while Vlada did more of the framing/UI/evaluation coordination and polishing the 
"human" side of the system. Both of us contributed substantially to writing and final integration.

