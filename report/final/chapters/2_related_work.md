This section summarizes the ideas that shaped our approach: why open budget data is often still hard to understand, 
and how fuzzy linguistic summaries can help. We first look at work on transparency and citizen-friendly budget 
communication, then introduce “computing with words” and fuzzy summarization, and finally explain why we use robust 
trend estimation for short municipal time series. These concepts directly inform the prototype design (Section 5) and 
the evaluation criteria (Section 6).

## Budget transparency & citizen-centered public finance communication
Research on transparency repeatedly shows that publishing more data is not the same as creating understanding. 
If data is released in a technical or overwhelming form, it can create “transparency illusions”, overload readers, 
or even reduce trust [@heald2006; @bannister2011trouble; @grimmelikhuijsen2014effects]. In the open budget domain, 
this leads to the idea of translation layers: interfaces that convert administrative structures into the kinds of 
questions citizens actually ask in consultations [@tygel2015howmuch; @kim2016budgetmap]. This is why our summaries 
focus on familiar topics (e.g., education, transport) and on changes over time, instead of presenting raw ledger 
tables.

## Computing with words and perceptions
Zadeh’s “computing with words” argues that people often reason with qualitative terms like “high”, “low”, or “stable”, 
not with exact numbers [@zadeh1999cw; @zadeh2001perceptions]. Later work makes a similar point: systems should adapt to 
human language and perception rather than forcing non-experts to adopt technical parameters and accounting vocabulary 
[@mendel2010cww]. We apply this idea by mapping numeric budget shares and trends to the kinds of phrases that naturally 
appear in civic discussions (e.g., “healthcare is rising” or “education is high but stable”).

## Fuzzy linguistic summarization
Fuzzy linguistic summarization is a way to express statements like “spending is high” while still being explicit 
about uncertainty, by attaching a membership degree ($\mu$) and confidence cues [@yager1982linguistic; @kacprzyk2005protoforms]. 
For representing labels in a controlled and interpretable way, the 2-tuple model is a common 
approach [@herrera2000linguistic]. In our prototype, we use trapezoidal membership functions and calibrate them from 
Zürich’s observed data: percentiles (10/30/50/70/90) for spending shares, and the median absolute deviation (MAD) 
for trend slopes. This keeps labels anchored in what is typical for Zürich and allows us to say when a label is 
only a weak match (e.g., low $\mu$ for very small departments).

## Trend estimation in time series
A simple least-squares slope can change a lot with outliers, which matters for municipal budgets where single-year 
events can distort trends. The Theil–Sen estimator is more robust because it uses the median of pairwise 
slopes [@theil1950; @sen1968], which works well for short windows like 5–6 years. In the prototype, we report trends 
both as percentage points per year and as relative change compared to the mean share, so that trends are comparable 
across departments with very different baseline sizes.

## Summary of gaps
Overall, prior work covers:

1. The limits of “raw transparency”.
2. Citizen-oriented budget interfaces.
3. Fuzzy linguistic summaries.
4. Robust trend estimation.

However, we did not find publicly documented Zürich prototypes that combine the official RPK-API budget feeds, 
Theil–Sen trend estimation, and fuzzy linguistic summaries in a scriptable Q&A-style workflow [@stadtzuerich2024rpk]. 
This project addresses this gap by implementing such an artifact and evaluating it.
