## Background
Swiss municipalities such as Zürich publish detailed budget tables through open data portals, yet this openness does not 
automatically translate into understanding. In practice, budget PDFs and API payloads often assume technical and accounting backgrounds, 
which limits who can interpret the figures and participate in public-finance discussions. Prior to work on transparency 
similarly argues that publishing data is not enough: citizens benefit from representations that connect spending to 
meaningful civic questions and provide context for change over time [@bertot2010ict; @cucciniello2017twentyfive].

> “Numbers have an important story to tell. They rely on you to give them a clear and convincing voice.” — Stephen Few.

## Problem
Preliminary discussions about Zürich’s open budget portal indicated four recurring frictions.

1. The material is perceived as overly technical: readers encounter tables and codes rather than explanations. 
2. Accessibility remains low because answering even simple questions requires API literacy or data-processing skills. 
3. These barriers reduce engagement, since many residents feel disconnected from financial decisions. 
4. The absence of interpretive layers makes it difficult to identify what matters most in public spending, 
especially when priorities shift gradually across years.

## Goals
The project explores whether summaries driven by fuzzy logic can serve as a lightweight translation layer from numeric budgets 
to citizen-facing statements. Concretely, we aim to: 

1. Implement systems that map departmental shares and trends to controlled linguistic labels.
2. Provide deterministic and reproducible responses that remain traceable to the original data.
3. Evaluate whether the resulting messages are interpretable and useful for typical citizen questions.

## Presented values and report structure
This report presents a reproducible prototype for explaining Zürich’s public budget in plain language using fuzzy-driven 
summaries. The main contribution is a Python implementation that loads budget data from the official API or from cached 
CSV exports and generates traceable, structured summaries (see Section 5; code in the repository [@potuzhnyiSvirshZuriBudgetFuzzySUC]). In 
addition, the report documents the fuzzy labeling and robust trend estimation approach used to translate numeric shares 
into terms such as “low/high” and “rising/stable/falling” (Section 5). It reports two small evaluation rounds that 
assess interpretability, usability, and repeatability of the outputs (Section 6).

[//]: # (The remainder of the report is structured as follows: Section 2 reviews related work on budget transparency, computing )

[//]: # (with words, fuzzy linguistic summarization, and robust trend estimation. Section 3 states the research questions and )

[//]: # (method. Section 4 defines the use cases, data sources, and requirements. Section 5 describes the prototype design and )

[//]: # (implementation, and Section 6 reports the evaluation results. Section 7 discusses limitations and lessons learned, and )

[//]: # (Section 8 concludes with an outlook.)
